"""Evaluador de pronunciación: wav2vec2 (fonemas por instante) + red BiLSTM entrenada (puntajes).

1. wav2vec2 da la probabilidad de cada fonema en cada instante del audio.
2. tutor/rasgos_pronunciacion.py convierte eso en características por fonema esperado
   (v1: sobre todo el audio; v2: alineación forzada y medida en el tramo de cada fonema).
3. La BiLSTM (entrenamiento/entrenar_evaluador.py) da un puntaje a cada fonema (0 a 2) y a la frase (0 a 10).
4. La alineación dice además qué sonido se oyó en cada fonema y en qué palabra estaba.

datos/evaluador_pronunciacion.pt trae los pesos, qué características usa, su normalización y sus variantes.
"""
import os
import re
import sys
import torch
import torch.nn as nn
import numpy as np
from faster_whisper import decode_audio
from transformers import Wav2Vec2ForCTC, Wav2Vec2FeatureExtractor, Wav2Vec2PhonemeCTCTokenizer

from tutor import rasgos_pronunciacion as R

MODEL_ID = "facebook/wav2vec2-lv-60-espeak-cv-ft"
CARPETA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos")
RUTA_MODELO = os.path.join(CARPETA, "evaluador_pronunciacion.pt")
device = "cuda" if torch.cuda.is_available() else "cpu"

feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_ID)
tokenizer = Wav2Vec2PhonemeCTCTokenizer.from_pretrained(MODEL_ID, do_phonemize=False)
wav2vec = Wav2Vec2ForCTC.from_pretrained(MODEL_ID).to(device)
wav2vec.eval()

vocab = tokenizer.get_vocab()
_simbolo = {i: s for s, i in vocab.items()}
BLANCO, ESPECIALES = R.especiales_de(vocab)


class EvaluadorPronunciacion(nn.Module):
    def __init__(self, vocab_size, n_rasgos=4, emb_dim=16, hidden_dim=64):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb_dim)
        self.lstm = nn.LSTM(n_rasgos + emb_dim, hidden_dim, num_layers=2, batch_first=True, bidirectional=True)
        self.head_fonema = nn.Linear(hidden_dim * 2, 1)
        self.head_frase = nn.Linear(hidden_dim * 2, 1)

    def forward(self, token_ids, acoustic_feats):
        e = self.emb(token_ids)
        x = torch.cat([e, acoustic_feats], dim=-1)
        out, _ = self.lstm(x)
        pred_fonema = self.head_fonema(out).squeeze(-1)
        pred_frase = self.head_frase(out.mean(dim=1)).squeeze(-1)
        return pred_fonema, pred_frase


# ----------------------------------------------------------------------------- carga del modelo
_guardado = torch.load(RUTA_MODELO, map_location=device, weights_only=True)
VERSION = _guardado["rasgos"]                          # "v1", "v2" o "v1+v2" (el actual es "v1+v2")
VARIANTES = _guardado["variantes"]
NORM_MEDIA = np.array(_guardado["media"], dtype=np.float32)
NORM_DESV = np.array(_guardado["desv"], dtype=np.float32)
evaluador = EvaluadorPronunciacion(len(vocab), _guardado["n_rasgos"]).to(device)
evaluador.load_state_dict(_guardado["estado"])
evaluador.eval()
print(f"Evaluador de pronunciación cargado (características {VERSION})", file=sys.stderr)

# Símbolo de wav2vec2 -> fonema del inglés que representa (para decir qué se oyó con símbolos conocidos)
# (si un símbolo es variante de dos fonemas, como "uː" de "u" y de "ʊ", gana el primero en orden)
_FONEMA_DE_VARIANTE = {}
for _f in sorted(VARIANTES):
    for _v in VARIANTES[_f]:
        _FONEMA_DE_VARIANTE.setdefault(_v, _f)

# Un fonema se marca como débil si su puntaje (escala 0 a 2) queda por debajo de este valor.
# Calíbralo con scripts/probar_pronunciacion.py: si nunca marca nada, súbelo; si marca todo, bájalo.
UMBRAL_FONEMA = 1.5

# El banco de frases (con sus fonemas) está en datos/ejercicios.json y se maneja en tutor/ejercicios.py.


def palabras_de(frase: str) -> list:
    """Las palabras de la frase, igual que las separa scripts/generar_fonemas.py."""
    return [p.strip("'") for p in re.findall(r"[a-z']+", frase.lower().replace("’", "'"))]


def _separar(fonemas_esperados: str, frase: str | None) -> tuple:
    """("k æ n | j u", "Can you") -> (["k","æ","n","j","u"], ["can","can","can","you","you"]).
    Si no hay separadores o no cuadran con la frase, las palabras quedan en None."""
    grupos = [g.split() for g in fonemas_esperados.split("|")]
    fonemas = [f for g in grupos for f in g]
    palabras = palabras_de(frase) if frase else []
    if len(grupos) > 1 and len(palabras) == len(grupos):
        return fonemas, [p for p, g in zip(palabras, grupos) for _ in g]
    return fonemas, [None] * len(fonemas)


def evaluar_audio(ruta_audio: str, fonemas_esperados: str, detalle: bool = False, frase: str | None = None) -> dict:
    # av (ya instalado con faster-whisper) lee OGG/Opus sin necesitar ffmpeg aparte
    audio = decode_audio(ruta_audio, sampling_rate=16000)
    if len(audio) < 8000:  # menos de 0.5 s
        raise ValueError("El audio es demasiado corto para evaluarlo.")

    inputs = feature_extractor(audio, sampling_rate=16000, return_tensors="pt").to(device)
    with torch.no_grad():
        logits = wav2vec(inputs.input_values).logits
        log_probs = torch.log_softmax(logits, dim=-1).squeeze(0).cpu().numpy()

    lista_fonemas, palabra_de_fonema = _separar(fonemas_esperados, frase)
    tokens = [ids[0] for ids in R.ids_aceptados(lista_fonemas, vocab, {})]
    aceptados = R.ids_aceptados(lista_fonemas, vocab, VARIANTES)
    analisis = R.analizar(log_probs, aceptados, BLANCO, ESPECIALES)   # siempre: dice qué se oyó

    partes = []
    if "v1" in VERSION:
        partes.append(R.rasgos_v1(log_probs, tokens))
    if "v2" in VERSION:
        partes.append(analisis["rasgos"])
    arr = (np.concatenate(partes, axis=1) - NORM_MEDIA) / NORM_DESV

    with torch.no_grad():
        p_fon, p_fra = evaluador(torch.tensor([tokens], device=device),
                                 torch.tensor(arr, dtype=torch.float32, device=device).unsqueeze(0))

    puntajes_fonemas = p_fon.squeeze(0).cpu().numpy().tolist()
    puntaje_frase = max(0.0, min(10.0, float(p_fra.item())))

    # Los sonidos más débiles (de menor a mayor puntaje), con su palabra y lo que se oyó
    orden = sorted(range(len(lista_fonemas)), key=lambda k: puntajes_fonemas[k])
    peores = []
    for k in orden[:3]:
        if puntajes_fonemas[k] >= UMBRAL_FONEMA:
            break
        item = {"fonema": lista_fonemas[k], "puntaje": round(puntajes_fonemas[k], 2)}
        if palabra_de_fonema[k]:
            item["palabra"] = palabra_de_fonema[k]
        if analisis["estado"][k] == "omitido":
            item["se_escucho"] = "(casi no se oyó)"
        elif analisis["oidos"][k] not in aceptados[k]:
            oido = _simbolo[analisis["oidos"][k]]
            item["se_escucho"] = _FONEMA_DE_VARIANTE.get(oido, oido)
        peores.append(item)

    resultado = {"puntaje_frase": round(puntaje_frase, 1), "peores_fonemas": peores}
    if detalle:  # solo para depurar y calibrar el umbral (no se manda al LLM)
        resultado["detalle"] = [
            (f, round(s, 2), palabra_de_fonema[k] or "", _simbolo[analisis["oidos"][k]], analisis["estado"][k])
            for k, (f, s) in enumerate(zip(lista_fonemas, puntajes_fonemas))]
    return resultado
