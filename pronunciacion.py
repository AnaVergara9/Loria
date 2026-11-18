import os
import torch
import torch.nn as nn
import numpy as np
from faster_whisper import decode_audio
from transformers import Wav2Vec2ForCTC, Wav2Vec2FeatureExtractor, Wav2Vec2PhonemeCTCTokenizer

MODEL_ID = "facebook/wav2vec2-lv-60-espeak-cv-ft"
device = "cuda" if torch.cuda.is_available() else "cpu"

feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_ID)
tokenizer = Wav2Vec2PhonemeCTCTokenizer.from_pretrained(MODEL_ID, do_phonemize=False)
wav2vec = Wav2Vec2ForCTC.from_pretrained(MODEL_ID).to(device)
wav2vec.eval()

vocab = tokenizer.get_vocab()


class EvaluadorPronunciacion(nn.Module):
    def __init__(self, vocab_size, emb_dim=16, hidden_dim=64):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb_dim)
        self.lstm = nn.LSTM(4 + emb_dim, hidden_dim, num_layers=2, batch_first=True, bidirectional=True)
        self.head_fonema = nn.Linear(hidden_dim * 2, 1)
        self.head_frase = nn.Linear(hidden_dim * 2, 1)

    def forward(self, token_ids, acoustic_feats):
        e = self.emb(token_ids)
        x = torch.cat([e, acoustic_feats], dim=-1)
        out, _ = self.lstm(x)
        pred_fonema = self.head_fonema(out).squeeze(-1)
        pred_frase = self.head_frase(out.mean(dim=1)).squeeze(-1)
        return pred_fonema, pred_frase


evaluador = EvaluadorPronunciacion(len(vocab)).to(device)
evaluador.load_state_dict(torch.load("evaluador_pronunciacion.pt", map_location=device))
evaluador.eval()

# Normalización de las características acústicas (se genera en Colab junto con el .pt).
# El .pt y normalizacion.npz van SIEMPRE juntos: si no coinciden, los puntajes no valen.
if os.path.exists("normalizacion.npz"):
    _norm = np.load("normalizacion.npz")
    NORM_MEDIA, NORM_DESV = _norm["media"], _norm["desv"]
    print("Normalización cargada (normalizacion.npz)")
else:
    NORM_MEDIA = NORM_DESV = None
    print("Sin normalizacion.npz: el evaluador asume un modelo entrenado sin normalizar")

# Un fonema se marca como débil si su puntaje (escala 0 a 2) queda por debajo de este valor.
# Calíbralo con probar_pronunciacion.py: si nunca marca nada, súbelo; si marca todo, bájalo.
UMBRAL_FONEMA = 1.5

# Banco de ejercicios con sus fonemas IPA esperados
EJERCICIOS_PRONUNCIACION = [
    {"frase": "I think the weather is nice today", "fonemas": "aɪ θ ɪ ŋ k ð ə w ɛ ð ɚ ɪ z n aɪ s t ə d eɪ"},
    {"frase": "She sells seashells by the seashore", "fonemas": "ʃ i s ɛ l z s i ʃ ɛ l z b aɪ ð ə s i ʃ ɔ ɹ"},
    {"frase": "Three free throws for the team", "fonemas": "θ ɹ i f ɹ i θ ɹ oʊ z f ɔ ɹ ð ə t i m"},
    {"frase": "Can you read this book with me?", "fonemas": "k æ n j u ɹ i d ð ɪ s b ʊ k w ɪ ð m i"},
    {"frase": "Very well, thank you for asking", "fonemas": "v ɛ ɹ i w ɛ l θ æ ŋ k j u f ɔ ɹ æ s k ɪ ŋ"},
]


def evaluar_audio(ruta_audio: str, fonemas_esperados: str, detalle: bool = False) -> dict:
    # av (ya instalado con faster-whisper) lee OGG/Opus sin necesitar ffmpeg aparte
    audio = decode_audio(ruta_audio, sampling_rate=16000)
    if len(audio) < 8000:  # menos de 0.5 s
        raise ValueError("El audio es demasiado corto para evaluarlo.")

    inputs = feature_extractor(audio, sampling_rate=16000, return_tensors="pt").to(device)

    with torch.no_grad():
        logits = wav2vec(inputs.input_values).logits
        log_probs = torch.log_softmax(logits, dim=-1).squeeze(0).cpu().numpy()

    lista_fonemas = fonemas_esperados.split()
    fonemas_seq = []

    for ph in lista_fonemas:
        token_id = vocab.get(ph, vocab.get("<unk>", 0))
        ph_probs = log_probs[:, token_id]
        max_ph = float(np.max(ph_probs))
        mean_ph = float(np.mean(ph_probs))
        std_ph = float(np.std(ph_probs))
        gop_proxy = max_ph - float(np.mean(np.max(log_probs, axis=-1)))
        fonemas_seq.append([token_id, max_ph, mean_ph, std_ph, gop_proxy])

    arr = np.array(fonemas_seq, dtype=np.float32)
    if NORM_MEDIA is not None:
        arr[:, 1:] = (arr[:, 1:] - NORM_MEDIA) / NORM_DESV
    feats = torch.tensor(arr, device=device).unsqueeze(0)
    tokens = feats[:, :, 0].long()
    acoustics = feats[:, :, 1:]

    with torch.no_grad():
        p_fon, p_fra = evaluador(tokens, acoustics)

    puntajes_fonemas = p_fon.squeeze(0).cpu().numpy().tolist()
    puntaje_frase = max(0.0, min(10.0, float(p_fra.item())))

    # Ordenar de menor a mayor puntaje para detectar los peores sonidos
    ordenados = sorted(zip(lista_fonemas, puntajes_fonemas), key=lambda x: x[1])
    peores = [{"fonema": f, "puntaje": round(s, 2)} for f, s in ordenados[:3] if s < UMBRAL_FONEMA]

    resultado = {
        "puntaje_frase": round(puntaje_frase, 1),
        "peores_fonemas": peores,
    }
    if detalle:  # solo para depurar y calibrar el umbral (no se manda al LLM)
        resultado["detalle"] = [(f, round(s, 2)) for f, s in zip(lista_fonemas, puntajes_fonemas)]
    return resultado
