# -*- coding: utf-8 -*-
"""EvaluadorPronunciacion.ipynb

Cuaderno de Google Colab con el que se entrenó el evaluador de pronunciación del bot
(exportado como .py; ver entrenamiento/README.md). Está pensado para correr en Colab con GPU:
la línea "!pip install" es una orden de Colab y no funciona como Python normal.

Produce los dos archivos que usa pronunciacion.py: evaluador_pronunciacion.pt y normalizacion.npz.

Original file is located at
    https://colab.research.google.com/drive/1eegJWtF1aB5zALxuajDvMfRLiLdKI1mJ
"""

# En Colab, quita el "#" de la línea siguiente (es una orden de Colab, no Python normal):
# !pip install -q datasets transformers torch torchaudio librosa soundfile scipy

from datasets import load_dataset

# Descarga el dataset oficial de Hugging Face (2500 train / 2500 test)
dataset = load_dataset("mispeech/speechocean762")
print(dataset)

import torch
import numpy as np
from transformers import Wav2Vec2ForCTC, Wav2Vec2FeatureExtractor, Wav2Vec2PhonemeCTCTokenizer

device = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_ID = "facebook/wav2vec2-lv-60-espeak-cv-ft"

feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_ID)
tokenizer = Wav2Vec2PhonemeCTCTokenizer.from_pretrained(MODEL_ID, do_phonemize=False)
wav2vec = Wav2Vec2ForCTC.from_pretrained(MODEL_ID).to(device)
wav2vec.eval()

processor = feature_extractor   # así el resto del código sigue funcionando igual
vocab = tokenizer.get_vocab()
print("Tamaño del vocabulario:", len(vocab))

from collections import Counter

ARPA2IPA = {
    "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ",
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "EH": "ɛ", "ER": "ɚ",
    "EY": "eɪ", "F": "f", "G": "ɡ", "HH": "h", "IH": "ɪ", "IY": "i",
    "JH": "dʒ", "K": "k", "L": "l", "M": "m", "N": "n", "NG": "ŋ",
    "OW": "oʊ", "OY": "ɔɪ", "P": "p", "R": "ɹ", "S": "s", "SH": "ʃ",
    "T": "t", "TH": "θ", "UH": "ʊ", "UW": "u", "V": "v", "W": "w",
    "Y": "j", "Z": "z", "ZH": "ʒ",
}
UNK_ID = vocab.get("<unk>", 0)
stats = {"total": 0, "unk": 0}
desconocidos = Counter()


def arpabet_a_ipa(ph):
    base = "".join(c for c in ph if not c.isdigit()).upper()
    acento = ph[-1] if ph and ph[-1].isdigit() else None
    if base == "AH":                       # AH0 = ə (sin acento), AH1/AH2 = ʌ
        return "ə" if acento == "0" else "ʌ"
    return ARPA2IPA.get(base)


def token_de_fonema(ph):
    stats["total"] += 1
    ipa = arpabet_a_ipa(ph)
    if ipa is not None:
        for candidato in ([ipa, "g"] if ipa == "ɡ" else [ipa]):
            if candidato in vocab:
                return vocab[candidato]
    stats["unk"] += 1
    desconocidos[f"{ph} -> {ipa}"] += 1
    return UNK_ID


def extraer_features_frase(ejemplo):
    audio = ejemplo["audio"]["array"]
    inputs = processor(audio, sampling_rate=16000, return_tensors="pt").to(device)

    with torch.no_grad():
        logits = wav2vec(inputs.input_values).logits  # [1, T, V]
        log_probs = torch.log_softmax(logits, dim=-1).squeeze(0).cpu().numpy()  # [T, V]

    fonemas_seq = []
    puntajes_seq = []

    for word_info in ejemplo["words"]:
        for ph, score in zip(word_info["phones"], word_info["phones-accuracy"]):
            token_id = token_de_fonema(ph)

            ph_probs = log_probs[:, token_id]
            max_ph = np.max(ph_probs)
            mean_ph = np.mean(ph_probs)
            std_ph = np.std(ph_probs)
            gop_proxy = max_ph - np.mean(np.max(log_probs, axis=-1))

            fonemas_seq.append([token_id, max_ph, mean_ph, std_ph, gop_proxy])
            puntajes_seq.append(float(score))  # Escala 0 a 2

    return {
        "features": np.array(fonemas_seq, dtype=np.float32),
        "labels": np.array(puntajes_seq, dtype=np.float32),
        "sentence_score": float(ejemplo["accuracy"]),  # Escala 0 a 10
    }

# Reinicia los contadores por si corres esta celda más de una vez
stats["total"] = 0
stats["unk"] = 0
desconocidos.clear()

# Procesar particiones (tarda unos 3-4 minutos con GPU T4)
train_data = [extraer_features_frase(x) for x in dataset["train"]]
test_data = [extraer_features_frase(x) for x in dataset["test"]]
print("Características extraídas:", len(train_data), "train,", len(test_data), "test")

print(f"Fonemas sin token: {stats['unk']} de {stats['total']} ({100*stats['unk']/stats['total']:.1f}%)")
print(desconocidos.most_common(10))

import torch.nn as nn
from torch.utils.data import DataLoader
from scipy.stats import pearsonr

class EvaluadorPronunciacion(nn.Module):
    def __init__(self, vocab_size, emb_dim=16, hidden_dim=64):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb_dim)
        # 4 features acústicas + emb_dim del fonema esperado
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

modelo_eval = EvaluadorPronunciacion(len(vocab)).to(device)
optimizer = torch.optim.Adam(modelo_eval.parameters(), lr=1e-3)
criterion = nn.MSELoss()

# Entrenamiento rápido (15 épocas, ~1 minuto)
for epoch in range(15):
    modelo_eval.train()
    total_loss = 0
    for item in train_data:
        if len(item["features"]) == 0:
            continue
        feats = torch.tensor(item["features"], device=device).unsqueeze(0)
        tokens = feats[:, :, 0].long()
        acoustics = feats[:, :, 1:]
        y_fon = torch.tensor(item["labels"], device=device).unsqueeze(0)
        y_fra = torch.tensor([item["sentence_score"]], device=device)

        optimizer.zero_grad()
        p_fon, p_fra = modelo_eval(tokens, acoustics)
        loss = criterion(p_fon, y_fon) + 0.1 * criterion(p_fra, y_fra)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print(f"Época {epoch+1}/15 - Loss: {total_loss/len(train_data):.4f}")

# Evaluación con Correlación de Pearson (Tabla III del paper)
modelo_eval.eval()
all_preds_fon, all_true_fon = [], []
all_preds_fra, all_true_fra = [], []

with torch.no_grad():
    for item in test_data:
        if len(item["features"]) == 0:
            continue
        feats = torch.tensor(item["features"], device=device).unsqueeze(0)
        tokens = feats[:, :, 0].long()
        acoustics = feats[:, :, 1:]
        p_fon, p_fra = modelo_eval(tokens, acoustics)

        all_preds_fon.extend(p_fon.squeeze(0).cpu().numpy())
        all_true_fon.extend(item["labels"])
        all_preds_fra.append(p_fra.item())
        all_true_fra.append(item["sentence_score"])

r_fon, _ = pearsonr(all_preds_fon, all_true_fon)
r_fra, _ = pearsonr(all_preds_fra, all_true_fra)
print(f"\nResultados en Test speechocean762:")
print(f"Pearson por fonema: {r_fon:.3f} (Referencia GOPT: 0.610)")
print(f"Pearson por frase:  {r_fra:.3f} (Referencia GOPT: 0.740)")

# Guardar pesos para llevarlos al bot
torch.save(modelo_eval.state_dict(), "evaluador_pronunciacion.pt")

import copy
import random
import numpy as np
import torch
import torch.nn as nn
from scipy.stats import pearsonr

SOLO_IDENTIDAD = False  # Ponlo en True para una ablación: la red solo ve QUÉ fonema es,
                         # sin ninguna característica acústica. Sirve como línea base
                         # para el informe (¿cuánto aportan realmente las características?).
                         # Si lo pones en True, NO descargues ese .pt para el bot.

random.seed(0)
torch.manual_seed(0)

# 1) Normalización (solo columnas acústicas; la columna 0 es el id del fonema)
todas = np.concatenate([x["features"][:, 1:] for x in train_data if len(x["features"])])
media, desv = todas.mean(axis=0), todas.std(axis=0) + 1e-6
np.savez("normalizacion.npz", media=media, desv=desv)


def preparar(item):
    f = item["features"].copy()
    f[:, 1:] = (f[:, 1:] - media) / desv
    if SOLO_IDENTIDAD:
        f[:, 1:] = 0.0
    return f


def evaluar(modelo, datos):
    modelo.eval()
    pf, tf, pr, tr = [], [], [], []
    with torch.no_grad():
        for item in datos:
            if len(item["features"]) == 0:
                continue
            feats = torch.tensor(preparar(item), device=device).unsqueeze(0)
            p_fon, p_fra = modelo(feats[:, :, 0].long(), feats[:, :, 1:])
            pf.extend(p_fon.squeeze(0).cpu().numpy())
            tf.extend(item["labels"])
            pr.append(p_fra.item())
            tr.append(item["sentence_score"])
    return pearsonr(pf, tf)[0], pearsonr(pr, tr)[0]


# 2) Partición train / validación
idx = list(range(len(train_data)))
random.shuffle(idx)
val = [train_data[i] for i in idx[:250]]
tr = [train_data[i] for i in idx[250:]]

# 3) Entrenamiento
modelo_eval = EvaluadorPronunciacion(len(vocab)).to(device)
optimizer = torch.optim.Adam(modelo_eval.parameters(), lr=1e-3, weight_decay=1e-4)
criterion = nn.MSELoss()

mejor_r, mejor_estado, mejor_epoca = -1.0, None, 0
EPOCAS = 30

for epoch in range(EPOCAS):
    modelo_eval.train()
    random.shuffle(tr)
    total = 0.0
    for item in tr:
        if len(item["features"]) == 0:
            continue
        feats = torch.tensor(preparar(item), device=device).unsqueeze(0)
        y_fon = torch.tensor(item["labels"], device=device).unsqueeze(0)
        y_fra = torch.tensor([item["sentence_score"]], device=device)

        optimizer.zero_grad()
        p_fon, p_fra = modelo_eval(feats[:, :, 0].long(), feats[:, :, 1:])
        loss = criterion(p_fon, y_fon) + 0.5 * criterion(p_fra, y_fra)
        loss.backward()
        optimizer.step()
        total += loss.item()

    r_fon_v, r_fra_v = evaluar(modelo_eval, val)
    print(f"Época {epoch+1}/{EPOCAS} - Loss: {total/len(tr):.4f} | Val Pearson fonema {r_fon_v:.3f}, frase {r_fra_v:.3f}")
    if r_fon_v > mejor_r:
        mejor_r, mejor_estado, mejor_epoca = r_fon_v, copy.deepcopy(modelo_eval.state_dict()), epoch + 1

print(f"\nMejor época según validación: {mejor_epoca} (Pearson fonema en val = {mejor_r:.3f})")
modelo_eval.load_state_dict(mejor_estado)

# 4) Evaluación final en TEST (se mira una sola vez)
r_fon, _ = evaluar(modelo_eval, test_data)
_, r_fra = evaluar(modelo_eval, test_data)
print("\nResultados en Test speechocean762:")
print(f"Pearson por fonema: {r_fon:.3f} (Referencia GOPT: 0.610)")
print(f"Pearson por frase:  {r_fra:.3f} (Referencia GOPT: 0.740)")

if not SOLO_IDENTIDAD:
    torch.save(modelo_eval.state_dict(), "evaluador_pronunciacion.pt")
    print("\nGuardados: evaluador_pronunciacion.pt y normalizacion.npz  -> descarga LOS DOS")

# ¿Los 2 fonemas con peor puntaje de cada frase son realmente errores anotados?
modelo_eval.eval()
aciertos, marcados, azar = 0, 0, 0.0
with torch.no_grad():
    for item in test_data:
        y = item["labels"]
        if len(y) < 3 or (y < 2).sum() == 0:   # solo frases con algún error anotado
            continue
        feats = torch.tensor(preparar(item), device=device).unsqueeze(0)
        p_fon, _ = modelo_eval(feats[:, :, 0].long(), feats[:, :, 1:])
        peores = p_fon.squeeze(0).cpu().numpy().argsort()[:2]
        aciertos += int((y[peores] < 2).sum())
        marcados += 2
        azar += 2 * float((y < 2).mean())
print(f"Acierto de los 2 fonemas marcados: {100*aciertos/marcados:.1f}%")
print(f"Acierto esperado eligiendo al azar: {100*azar/marcados:.1f}%")
