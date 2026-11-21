"""
Revisa las voces con reconocimiento de voz (Whisper): escribe lo que "entiende" de cada audio
para comprobar que se escucha la frase correcta.
Uso: python3 tools/check_voices.py CARPETA_WHISPER [ids...]
(CARPETA_WHISPER = sherpa-onnx-whisper-small, de https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models)
"""
import json, os, sys, subprocess
import numpy as np
import sherpa_onnx

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
d = sys.argv[1]
ids = sys.argv[2:]
pre = 'small'
rec = sherpa_onnx.OfflineRecognizer.from_whisper(
    encoder=os.path.join(d, f'{pre}-encoder.int8.onnx'), decoder=os.path.join(d, f'{pre}-decoder.int8.onnx'),
    tokens=os.path.join(d, f'{pre}-tokens.txt'), language='', task='transcribe', num_threads=4)
lines = json.load(open(os.path.join(BASE, 'src', 'dialogue.json'), encoding='utf-8'))['lines']
for l in lines:
    if ids and l['id'] not in ids:
        continue
    path = [os.path.join(BASE, 'public', 'voces', l['id'] + e) for e in ('.wav', '.mp3', '.m4a')]
    path = next((p for p in path if os.path.exists(p)), None)
    if not path:
        continue
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-ar', '16000', '-ac', '1', '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    s = rec.create_stream()
    s.accept_waveform(16000, x)
    rec.decode_stream(s)
    print(f"{l['id']} | {l['text']}\n        -> {s.result.text.strip()}", flush=True)
