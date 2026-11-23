"""Entrena y compara el evaluador de pronunciación (Etapa 8): características v1 contra v2.

Hace, en una sola corrida y con los MISMOS datos para todos:
  1. Pasa cada audio de speechocean762 por wav2vec2 (lo más lento: ~5 min con GPU, horas con CPU).
  2. Saca las VARIANTES de cada fonema, mirando solo el conjunto de entrenamiento.
  3. Calcula las características v1 (las originales) y v2 (alineación forzada, por tramo).
  4. Entrena la misma BiLSTM con el mismo protocolo del primer evaluador (versión 1) para cada versión:
     v1, v2, v1+v2 y "solo identidad" (sin audio, línea base). Elige la mejor por VALIDACIÓN.
  5. Mide todas en el conjunto de prueba (2.500 frases que nunca se usaron para entrenar ni elegir).
  6. Guarda la elegida en evaluador_pronunciacion.pt (con su normalización y sus variantes adentro).

En Google Colab (con GPU: Entorno de ejecución -> Cambiar tipo -> T4):
  - Sube este archivo y tutor/rasgos_pronunciacion.py (panel de archivos, a la izquierda).
  - Ejecuta en una celda:   !python entrenar_evaluador.py
  - Descarga evaluador_pronunciacion.pt y resultados_etapa8.json, y ponlos en datos/ y entrenamiento/.

En el computador (desde la carpeta del proyecto):
  python entrenamiento/entrenar_evaluador.py [--cache CARPETA] [--max N]
  --cache usa log-probabilidades ya calculadas (para no repetir wav2vec2); --max limita las frases.
"""
import os
import io
import sys
import json
import copy
import time
import random
import argparse
from collections import Counter, defaultdict

import numpy as np
import torch
import torch.nn as nn
from scipy.stats import pearsonr

try:                                             # dentro del proyecto
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tutor import rasgos_pronunciacion as R
except (NameError, ImportError):                 # en Colab (celda o archivo suelto): el archivo subido al lado
    sys.path.insert(0, os.getcwd())
    import rasgos_pronunciacion as R

MODEL_ID = "facebook/wav2vec2-lv-60-espeak-cv-ft"
device = "cuda" if torch.cuda.is_available() else "cpu"

# La misma tabla ARPAbet -> IPA del primer evaluador y de scripts/generar_fonemas.py
ARPA2IPA = {
    "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ",
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "EH": "ɛ", "ER": "ɚ",
    "EY": "eɪ", "F": "f", "G": "ɡ", "HH": "h", "IH": "ɪ", "IY": "i",
    "JH": "dʒ", "K": "k", "L": "l", "M": "m", "N": "n", "NG": "ŋ",
    "OW": "oʊ", "OY": "ɔɪ", "P": "p", "R": "ɹ", "S": "s", "SH": "ʃ",
    "T": "t", "TH": "θ", "UH": "ʊ", "UW": "u", "V": "v", "W": "w",
    "Y": "j", "Z": "z", "ZH": "ʒ",
}

# Variantes: un símbolo cuenta como variante de un fonema si es lo que más sonó en al menos este
# porcentaje de las veces que ese fonema estaba BIEN pronunciado (nota 2 de los expertos), y si NO es
# otro fonema del inglés (si no, el bot dejaría de marcar errores reales, como decir "z" por "ð").
VARIANTE_MIN_FRACCION = 0.10
VARIANTE_MIN_VECES = 20
FONEMAS_INGLES = set(ARPA2IPA.values()) | {"ə"}


def arpabet_a_ipa(ph):
    base = "".join(c for c in ph if not c.isdigit()).upper()
    acento = ph[-1] if ph and ph[-1].isdigit() else None
    if base == "AH":
        return "ə" if acento == "0" else "ʌ"
    return ARPA2IPA.get(base, "<unk>")


# ----------------------------------------------------------------------------- 1. datos
def cargar(particion, args, vocab):
    """Lista de frases: log_probs [T, V], fonemas IPA, notas por fonema (0-2) y nota de la frase (0-10)."""
    frases = []
    if args.cache:
        filas = [json.loads(l) for l in open(os.path.join(args.cache, f"{particion}_meta.jsonl"), encoding="utf-8")]
        for r in filas[: args.max or None]:
            ruta = os.path.join(args.cache, particion, f"{r['i']:04d}.npy")
            if os.path.exists(ruta):
                frases.append(_frase(np.load(ruta), r))
        return frases

    import soundfile as sf
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download
    from transformers import Wav2Vec2ForCTC, Wav2Vec2FeatureExtractor
    global _w2v
    if "_w2v" not in globals():
        _w2v = (Wav2Vec2FeatureExtractor.from_pretrained(MODEL_ID), Wav2Vec2ForCTC.from_pretrained(MODEL_ID).to(device).eval())
    fe, w = _w2v
    ruta = hf_hub_download("mispeech/speechocean762", f"data/{particion}-00000-of-00001.parquet", repo_type="dataset")
    tabla = pq.read_table(ruta)
    n = min(tabla.num_rows, args.max or tabla.num_rows)
    t0 = time.time()
    for i in range(n):
        r = tabla.slice(i, 1).to_pylist()[0]
        x, _ = sf.read(io.BytesIO(r["audio"]["bytes"]), dtype="float32")
        with torch.inference_mode():
            entrada = fe(x, sampling_rate=16000, return_tensors="pt").input_values.to(device)
            lp = torch.log_softmax(w(entrada).logits, -1).squeeze(0).float().cpu().numpy()
        frases.append(_frase(lp, r))
        if (i + 1) % 250 == 0:
            print(f"  {particion}: {i+1}/{n} audios ({time.time()-t0:.0f} s)", flush=True)
    return frases


def _frase(lp, r):
    fonemas, notas = [], []
    for palabra in r["words"]:
        for ph, nota in zip(palabra["phones"], palabra["phones-accuracy"]):
            fonemas.append(arpabet_a_ipa(ph))
            notas.append(float(nota))
    return {"lp": lp.astype(np.float32), "fonemas": fonemas,
            "notas": np.array(notas, dtype=np.float32), "nota_frase": float(r["accuracy"])}


# ----------------------------------------------------------------------------- 2. variantes
def sacar_variantes(entrenamiento, vocab):
    """Qué símbolos usa wav2vec2 para cada fonema BIEN pronunciado (solo datos de entrenamiento)."""
    inv = {i: s for s, i in vocab.items()}
    blanco, especiales = R.especiales_de(vocab)
    oidos, totales = defaultdict(Counter), Counter()
    for f in entrenamiento:
        a = R.analizar(f["lp"], R.ids_aceptados(f["fonemas"], vocab, {}), blanco, especiales)
        for fon, nota, oido in zip(f["fonemas"], f["notas"], a["oidos"]):
            if nota == 2.0:
                oidos[fon][inv[oido]] += 1
                totales[fon] += 1
    variantes = {}
    for fon, cuenta in sorted(oidos.items()):
        v = [s for s, c in cuenta.most_common() if s != fon and s not in FONEMAS_INGLES and s != "g"
             and c >= VARIANTE_MIN_VECES and c / totales[fon] >= VARIANTE_MIN_FRACCION]
        if v:
            variantes[fon] = v
        top = ", ".join(f"{s} {100*c/totales[fon]:.0f}%" for s, c in cuenta.most_common(3))
        print(f"  {fon:>3} (n={totales[fon]:>5}): {top}" + (f"   -> variantes {v}" if v else ""))
    return variantes


# ----------------------------------------------------------------------------- 3-5. red y entrenamiento
class EvaluadorPronunciacion(nn.Module):
    """La misma BiLSTM del primer evaluador; solo cambia cuántas características recibe."""
    def __init__(self, vocab_size, n_rasgos=4, emb_dim=16, hidden_dim=64):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb_dim)
        self.lstm = nn.LSTM(n_rasgos + emb_dim, hidden_dim, num_layers=2, batch_first=True, bidirectional=True)
        self.head_fonema = nn.Linear(hidden_dim * 2, 1)
        self.head_frase = nn.Linear(hidden_dim * 2, 1)

    def forward(self, token_ids, acoustic_feats):
        x = torch.cat([self.emb(token_ids), acoustic_feats], dim=-1)
        out, _ = self.lstm(x)
        return self.head_fonema(out).squeeze(-1), self.head_frase(out.mean(dim=1)).squeeze(-1)


def preparar(f, columnas, media, desv, solo_identidad=False):
    x = (f["rasgos"][:, columnas] - media) / desv
    if solo_identidad:
        x = np.zeros_like(x)
    return (torch.tensor(f["tokens"], device=device).unsqueeze(0),
            torch.tensor(x, dtype=torch.float32, device=device).unsqueeze(0))


def evaluar(modelo, datos, columnas, media, desv, solo_identidad=False):
    modelo.eval()
    pf, tf, pr, tr, aciertos, marcados, azar = [], [], [], [], 0, 0, 0.0
    with torch.no_grad():
        for f in datos:
            p_fon, p_fra = modelo(*preparar(f, columnas, media, desv, solo_identidad))
            p = p_fon.squeeze(0).cpu().numpy()
            pf.extend(p); tf.extend(f["notas"]); pr.append(p_fra.item()); tr.append(f["nota_frase"])
            y = f["notas"]
            if len(y) >= 3 and (y < 2).any():           # ¿los 2 peores marcados son errores reales?
                peores = p.argsort()[:2]
                aciertos += int((y[peores] < 2).sum()); marcados += 2; azar += 2 * float((y < 2).mean())
    return {"pearson_fonema": float(pearsonr(pf, tf)[0]), "pearson_frase": float(pearsonr(pr, tr)[0]),
            "acierto_2_peores": aciertos / max(marcados, 1), "acierto_azar": azar / max(marcados, 1)}


def entrenar(nombre, columnas, entrenamiento, validacion, vocab_size, epocas, solo_identidad=False):
    random.seed(0)
    torch.manual_seed(0)
    todas = np.concatenate([f["rasgos"][:, columnas] for f in entrenamiento])
    media, desv = todas.mean(axis=0), todas.std(axis=0) + 1e-6
    modelo = EvaluadorPronunciacion(vocab_size, len(columnas)).to(device)
    opt = torch.optim.Adam(modelo.parameters(), lr=1e-3, weight_decay=1e-4)
    mse = nn.MSELoss()
    orden = list(entrenamiento)
    mejor = (-1.0, None, 0)
    t0 = time.time()
    for epoca in range(epocas):
        modelo.train()
        random.shuffle(orden)
        for f in orden:
            tokens, x = preparar(f, columnas, media, desv, solo_identidad)
            y_fon = torch.tensor(f["notas"], device=device).unsqueeze(0)
            y_fra = torch.tensor([f["nota_frase"]], device=device)
            opt.zero_grad()
            p_fon, p_fra = modelo(tokens, x)
            loss = mse(p_fon, y_fon) + 0.5 * mse(p_fra, y_fra)
            loss.backward()
            opt.step()
        r = evaluar(modelo, validacion, columnas, media, desv, solo_identidad)["pearson_fonema"]
        if r > mejor[0]:
            mejor = (r, copy.deepcopy(modelo.state_dict()), epoca + 1)
    modelo.load_state_dict(mejor[1])
    print(f"  {nombre:<16} mejor época {mejor[2]:>2}, Pearson fonema en validación {mejor[0]:.3f} ({time.time()-t0:.0f} s)")
    return modelo, media, desv, mejor[0]


# ----------------------------------------------------------------------------- principal
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", help="carpeta con log-probabilidades ya calculadas")
    ap.add_argument("--max", type=int, default=0, help="usar solo las primeras N frases de cada partición")
    ap.add_argument("--epocas", type=int, default=30)
    ap.add_argument("--salida", default=".", help="dónde guardar el .pt y los resultados")
    args, _ = ap.parse_known_args()              # en una celda de Colab llegan argumentos propios del cuaderno

    from transformers import Wav2Vec2PhonemeCTCTokenizer
    vocab = Wav2Vec2PhonemeCTCTokenizer.from_pretrained(MODEL_ID, do_phonemize=False).get_vocab()
    blanco, especiales = R.especiales_de(vocab)

    print("1) Pasando los audios por wav2vec2...")
    entrenamiento_total = cargar("train", args, vocab)
    prueba = cargar("test", args, vocab)
    print(f"   {len(entrenamiento_total)} frases de entrenamiento, {len(prueba)} de prueba")

    # Misma partición entrenamiento / validación que el primer evaluador (semilla 0, 250 frases)
    idx = list(range(len(entrenamiento_total)))
    random.seed(0)
    random.shuffle(idx)
    n_val = 250 if len(idx) >= 2500 else max(len(idx) // 10, 20)
    validacion = [entrenamiento_total[i] for i in idx[:n_val]]
    entrenamiento = [entrenamiento_total[i] for i in idx[n_val:]]

    print("\n2) Variantes de cada fonema (fonema: lo que más sonó cuando estaba bien pronunciado)")
    variantes = sacar_variantes(entrenamiento, vocab)

    print("\n3) Características v1 y v2")
    t0 = time.time()
    for f in entrenamiento_total + prueba:
        f["tokens"] = [ids[0] for ids in R.ids_aceptados(f["fonemas"], vocab, {})]
        f["rasgos"] = np.concatenate([R.rasgos_v1(f["lp"], f["tokens"]),
                                      R.analizar(f["lp"], R.ids_aceptados(f["fonemas"], vocab, variantes),
                                                 blanco, especiales)["rasgos"]], axis=1)
    print(f"   listo en {time.time()-t0:.0f} s")
    nv1 = len(R.NOMBRES_V1)
    todas_cols = list(range(nv1 + len(R.NOMBRES_V2)))
    configuraciones = {"solo_identidad": (todas_cols, True), "v1": (list(range(nv1)), False),
                       "v2": (todas_cols[nv1:], False), "v1+v2": (todas_cols, False)}

    # Línea base sin red: ¿cuánto se parece cada característica sola a la nota del experto?
    notas = np.concatenate([f["notas"] for f in prueba])
    sin_red = {}
    for nombre, col in [("v1 gop_global", 3), ("v2 gop", nv1 + 1), ("v2 lpp", nv1)]:
        sin_red[nombre] = float(pearsonr(np.concatenate([f["rasgos"][:, col] for f in prueba]), notas)[0])
    print("   Pearson de una sola característica con la nota del experto (prueba, sin red):",
          ", ".join(f"{k} {v:.3f}" for k, v in sin_red.items()))

    if device == "cpu":
        torch.set_num_threads(1)                 # la red es pequeña: un hilo es más rápido
    print(f"\n4) Entrenando ({args.epocas} épocas cada una, con {device})")
    modelos = {}
    for nombre, (cols, ident) in configuraciones.items():
        modelos[nombre] = entrenar(nombre, cols, entrenamiento, validacion, len(vocab), args.epocas, ident)
    elegida = max((n for n in configuraciones if n != "solo_identidad"), key=lambda n: modelos[n][3])

    print("\n5) Resultados en PRUEBA (se miden una sola vez)")
    resultados = {}
    print(f"   {'versión':<16} {'Pearson fonema':>15} {'Pearson frase':>14} {'2 peores = error':>17}")
    for nombre, (cols, ident) in configuraciones.items():
        modelo, media, desv, r_val = modelos[nombre]
        r = evaluar(modelo, prueba, cols, media, desv, ident)
        r["pearson_fonema_validacion"] = r_val
        resultados[nombre] = r
        print(f"   {nombre:<16} {r['pearson_fonema']:>15.3f} {r['pearson_frase']:>14.3f} "
              f"{100*r['acierto_2_peores']:>12.1f}% (azar {100*r['acierto_azar']:.1f}%)")
    print("   Referencia GOPT (Gong et al., 2022): fonema ~0.61")
    print(f"\n   Elegida por validación: {elegida}")

    modelo, media, desv, _ = modelos[elegida]
    cols = configuraciones[elegida][0]
    os.makedirs(args.salida, exist_ok=True)
    torch.save({"version": 2, "rasgos": elegida, "n_rasgos": len(cols),
                "media": media.tolist(), "desv": desv.tolist(), "variantes": variantes,
                "estado": {k: v.cpu() for k, v in modelo.state_dict().items()}},   # en CPU: abre en cualquier equipo
               os.path.join(args.salida, "evaluador_pronunciacion.pt"))
    with open(os.path.join(args.salida, "resultados_etapa8.json"), "w", encoding="utf-8") as f:
        json.dump({"frases_entrenamiento": len(entrenamiento), "frases_validacion": len(validacion),
                   "frases_prueba": len(prueba), "epocas": args.epocas, "elegida": elegida,
                   "variantes": variantes, "sin_red": sin_red, "resultados": resultados},
                  f, ensure_ascii=False, indent=2)
    print(f"   Guardados: evaluador_pronunciacion.pt y resultados_etapa8.json en {os.path.abspath(args.salida)}")


if __name__ == "__main__":
    main()
