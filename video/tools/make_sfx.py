"""
Genera los efectos de sonido del video (sin descargar nada, todo sintetizado).
Uso:  python3 tools/make_sfx.py
Crea los archivos .wav en public/sfx/. Si luego consiguen efectos mejores
(libres de derechos), basta con reemplazar el archivo con el mismo nombre.
"""
import os
import wave
import numpy as np

SR = 44100
OUT = os.path.join(os.path.dirname(__file__), '..', 'public', 'sfx')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)


def t(d):
    return np.linspace(0, d, int(SR * d), endpoint=False)


def env(n, a=0.005, r=0.1, d=None):
    """Envolvente ataque / caida exponencial."""
    x = np.arange(n) / SR
    att = np.clip(x / max(a, 1e-4), 0, 1)
    dec = np.exp(-x / r) if d is None else np.clip(1 - x / d, 0, 1)
    return att * dec


def lowpass(x, k):
    k = max(1, int(k))
    return np.convolve(x, np.ones(k) / k, mode='same')


def save(name, x, gain=0.8):
    x = np.asarray(x, dtype=np.float64)
    peak = np.max(np.abs(x)) or 1
    x = x / peak * gain
    data = (x * 32767).astype(np.int16)
    with wave.open(os.path.join(OUT, name + '.wav'), 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    print('ok', name)


# POP: burbuja corta
x = t(0.12)
f = 900 * np.exp(-x * 25) + 300
save('pop', np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(x), 0.002, 0.03))

# WHOOSH: ruido filtrado que sube y baja
x = t(0.45)
n = rng.standard_normal(len(x))
sweep = np.concatenate([lowpass(n[i:i + 2205], 2 + 40 * (1 - abs(i / len(x) * 2 - 1))) for i in range(0, len(x), 2205)])[: len(x)]
save('whoosh', sweep * np.sin(np.pi * x / x[-1]) ** 2, 0.6)

# BUZZER: error de concurso
x = t(0.7)
b = np.sign(np.sin(2 * np.pi * 110 * x)) + 0.6 * np.sign(np.sin(2 * np.pi * 116 * x))
save('buzzer', lowpass(b, 6) * env(len(x), 0.005, 10, d=0.7), 0.7)

# DING: acierto (campanita)
x = t(1.0)
d = sum(a * np.sin(2 * np.pi * fr * x) for fr, a in [(1318, 1), (2637, 0.4), (3951, 0.2)])
save('ding', d * env(len(x), 0.002, 0.35))

# SPARKLE: brillo de las gafas (glissando agudo)
x = t(0.6)
s = np.zeros_like(x)
for i, fr in enumerate([1568, 2093, 2637, 3136, 4186]):
    st = int(i * 0.07 * SR)
    seg = x[: len(x) - st]
    s[st:] += np.sin(2 * np.pi * fr * seg) * env(len(seg), 0.002, 0.12)
save('sparkle', s, 0.6)

# SCRATCH: rayon de disco
x = t(0.5)
sc = rng.standard_normal(len(x)) * (0.5 + 0.5 * np.sin(2 * np.pi * 18 * x))
tone = np.sin(2 * np.pi * np.cumsum(400 + 1200 * np.sin(2 * np.pi * 3 * x)) / SR)
save('scratch', (lowpass(sc, 3) * 0.6 + tone * 0.4) * env(len(x), 0.002, 10, d=0.5), 0.7)

# SIREN: "pero espera, hay mas"
x = t(1.6)
fr = 700 + 400 * np.sin(2 * np.pi * 1.6 * x)
save('siren', np.sin(2 * np.pi * np.cumsum(fr) / SR) * env(len(x), 0.05, 10, d=1.6), 0.6)

# DRUMS: redoble corto
x = t(1.2)
dr = np.zeros_like(x)
for i in range(0, len(x), int(SR * 0.045)):
    seg = min(int(SR * 0.08), len(x) - i)
    dr[i:i + seg] += rng.standard_normal(seg) * env(seg, 0.001, 0.02) * (0.4 + 0.6 * i / len(x))
save('drumroll', lowpass(dr, 3), 0.6)

# REWIND: casete rebobinando (tono que acelera + chirrido)
x = t(1.2)
fr = 300 + 2500 * (x / x[-1]) ** 2
rw = np.sin(2 * np.pi * np.cumsum(fr) / SR) * 0.5 + lowpass(rng.standard_normal(len(x)), 4) * 0.3
save('rewind', rw * env(len(x), 0.02, 10, d=1.25), 0.6)

# STATIC: tele cambiando de canal
x = t(0.8)
save('static', rng.standard_normal(len(x)) * env(len(x), 0.005, 10, d=0.8), 0.45)

# CLICK: control remoto
x = t(0.06)
save('click', rng.standard_normal(len(x)) * env(len(x), 0.0005, 0.006), 0.7)

# STAMP: golpe de sello
x = t(0.35)
th = np.sin(2 * np.pi * np.cumsum(120 * np.exp(-x * 12) + 50) / SR) * env(len(x), 0.001, 0.08)
th += lowpass(rng.standard_normal(len(x)), 8) * env(len(x), 0.001, 0.02)
save('stamp', th, 0.9)

# BOING: rebote del logo
x = t(0.5)
fr = 200 + 260 * np.exp(-x * 6) * (1 + 0.3 * np.sin(2 * np.pi * 14 * x))
save('boing', np.sin(2 * np.pi * np.cumsum(fr) / SR) * env(len(x), 0.002, 0.2), 0.7)

# APPLAUSE: publico (muchos aplausos cortos al azar)
x = t(3.0)
ap = np.zeros_like(x)
for _ in range(900):
    i = rng.integers(0, len(x) - 900)
    ap[i:i + 900] += rng.standard_normal(900) * env(900, 0.0005, 0.004)
ap = lowpass(ap, 2) * np.clip(np.minimum(x / 0.2, (3.0 - x) / 0.8), 0, 1)
save('applause', ap, 0.55)

# FANFARE: ta-ta-taaa
seq = [(523, 0.12), (659, 0.12), (784, 0.12), (1046, 0.6)]
fan = []
for fr, d in seq:
    xx = t(d)
    note = sum(np.sign(np.sin(2 * np.pi * fr * h * xx)) / h for h in (1, 2))
    fan.append(lowpass(note, 4) * env(len(xx), 0.005, 10, d=d + 0.05))
save('fanfare', np.concatenate(fan), 0.55)

# CRAYON: garabateo
x = t(0.6)
cr = rng.standard_normal(len(x)) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 7 * x)))
save('crayon', lowpass(cr, 2) * env(len(x), 0.01, 10, d=0.6), 0.4)

# CRICKETS: silencio incomodo
x = t(1.5)
ck = np.sin(2 * np.pi * 4200 * x) * (np.sin(2 * np.pi * 30 * x) > 0.3) * ((x % 0.5) < 0.2)
save('crickets', ck * 0.6, 0.35)

# STAR: estrella ganada (arpegio)
star = []
for fr in (1046, 1318, 1568, 2093):
    xx = t(0.08)
    star.append(np.sin(2 * np.pi * fr * xx) * env(len(xx), 0.002, 0.06))
xx = t(0.4)
star.append(np.sin(2 * np.pi * 2637 * xx) * env(len(xx), 0.002, 0.15))
save('star', np.concatenate(star), 0.6)

# CRACK: huevo que se rompe
x = t(0.3)
ck = np.zeros_like(x)
for i in (0, int(0.05 * SR), int(0.11 * SR)):
    seg = len(x) - i
    ck[i:] += rng.standard_normal(seg) * env(seg, 0.0005, 0.015)
save('crack', ck, 0.8)

# KACHING: precio
x = t(0.9)
kc = sum(np.sin(2 * np.pi * fr * x) * env(len(x), 0.002, 0.25) for fr in (2093, 2637, 3136))
kc[: int(0.05 * SR)] += rng.standard_normal(int(0.05 * SR)) * 0.5
save('kaching', kc, 0.6)
