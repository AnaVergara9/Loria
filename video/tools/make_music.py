"""
Genera la musica de fondo del video (180 s exactos), sintetizada, sin derechos de autor.
Uso:  python3 tools/make_music.py      -> crea public/music/musica-loria.wav

Partes (siguen las escenas de src/timeline.ts):
  0:00-0:03  gancho (alegre, corto)
  0:03-0:28  "antes" en blanco y negro: drama suave en menor
  0:28-1:42  teletienda alegre (bateria, bajo, acordes, campanitas)
  1:42-2:08  modo ninos: xilofono y palmas, juguetona
  2:08-2:57  teletienda alegre otra vez
  2:57-3:00  remate final
Si consiguen una cancion libre de derechos que les guste mas, borren este archivo
y pongan la suya en public/music/ (solo debe haber un archivo ahi).
"""
import os
import wave

import numpy as np

SR = 44100
TOTAL = 180.0
BPM = 120
BEAT = 60 / BPM
rng = np.random.default_rng(3)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public', 'music', 'musica-loria.wav')

mix = np.zeros(int(SR * (TOTAL + 2)))


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def add(t0, sig, gain=1.0):
    i = int(t0 * SR)
    if i >= len(mix):
        return
    sig = sig[: len(mix) - i]
    mix[i : i + len(sig)] += sig * gain


def env(n, a=0.005, d=0.3):
    x = np.arange(n) / SR
    return np.clip(x / a, 0, 1) * np.exp(-x / d)


def tone(freq, dur, harm=((1, 1),), a=0.005, d=0.3):
    n = int(dur * SR)
    x = np.arange(n) / SR
    s = sum(amp * np.sin(2 * np.pi * freq * h * x) for h, amp in harm)
    return s * env(n, a, d)


def kick():
    n = int(0.35 * SR)
    x = np.arange(n) / SR
    f = 50 + 110 * np.exp(-x * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9)


def snare():
    n = int(0.22 * SR)
    x = np.arange(n) / SR
    noise = rng.standard_normal(n)
    return (noise * 0.7 + np.sin(2 * np.pi * 190 * x) * 0.5) * np.exp(-x * 20)


def hat():
    n = int(0.05 * SR)
    noise = rng.standard_normal(n)
    noise = noise - np.convolve(noise, np.ones(4) / 4, mode='same')  # quita graves
    return noise * np.exp(-np.arange(n) / SR * 90)


def clap():
    n = int(0.2 * SR)
    s = np.zeros(n)
    for off in (0, 0.012, 0.024):
        i = int(off * SR)
        m = n - i
        s[i:] += rng.standard_normal(m) * np.exp(-np.arange(m) / SR * 35)
    return s


def bass(note, dur):
    f = midi(note)
    return tone(f, dur, ((1, 1), (2, 0.35), (3, 0.12)), a=0.004, d=dur * 0.9)


def stab(notes, dur):
    return sum(tone(midi(n), dur, ((1, 1), (2, 0.4), (3, 0.25), (4, 0.12)), a=0.003, d=0.12) for n in notes) / len(notes)


def bell(note, dur=0.6):
    f = midi(note)
    return tone(f, dur, ((1, 1), (2.76, 0.3), (5.4, 0.12)), a=0.002, d=0.25)


def xylo(note):
    f = midi(note)
    return tone(f, 0.4, ((1, 1), (3.9, 0.25), (9.2, 0.08)), a=0.001, d=0.09)


def pad(notes, dur, trem=0.0):
    n = int(dur * SR)
    x = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * midi(m) * x) + 0.3 * np.sin(2 * np.pi * midi(m) * 2.003 * x) for m in notes) / len(notes)
    shape = np.clip(np.minimum(x / 0.6, (dur - x) / 0.6), 0, 1)
    if trem:
        shape *= 1 - trem * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * x))
    return s * shape


# Progresion alegre: C - G - Am - F (2 compases de 4 tiempos cada acorde = 4 s)
HAPPY = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]
MELODY = [72, 76, 79, 76, 74, 71, 74, 79, 72, 76, 81, 76, 77, 74, 72, 69]


def happy(t0, t1, intensity=1.0):
    t = t0
    bar = 0
    while t < t1 - 0.01:
        root, chord = HAPPY[(bar // 2) % 4]
        for b in range(4):
            tb = t + b * BEAT
            if tb >= t1:
                break
            add(tb, kick(), 0.9 * intensity)
            if b in (1, 3):
                add(tb, snare(), 0.45 * intensity)
            add(tb, hat(), 0.25)
            add(tb + BEAT / 2, hat(), 0.18)
            add(tb, bass(root if b % 2 == 0 else root + 12, BEAT * 0.9), 0.55)
            add(tb + BEAT / 2, stab(chord, 0.25), 0.28)
            if bar % 4 in (1, 3):
                add(tb, bell(MELODY[(bar * 4 + b) % 16], 0.5), 0.13)
        t += 4 * BEAT
        bar += 1


def drama(t0, t1):
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
    t = t0
    i = 0
    while t < t1 - 0.5:
        d = min(4.0, t1 - t)
        add(t, pad(chords[i % 4], d + 0.4, trem=0.35), 0.22)
        add(t, bass(chords[i % 4][0] - 12, d), 0.35)
        for k in range(4):
            if t + k < t1:
                add(t + k, tone(midi(chords[i % 4][k % 3] + 12), 0.9, ((1, 1), (2, 0.2)), d=0.4), 0.08)
        t += 4.0
        i += 1


def kids(t0, t1):
    seq = [72, 76, 79, 84, 79, 76, 74, 77, 81, 77, 74, 71, 72, 76, 79, 76]
    roots = [48, 53, 55, 48]
    t = t0
    step = 0
    while t < t1 - 0.01:
        add(t, xylo(seq[step % 16]), 0.32)
        if step % 4 == 0:
            add(t, kick(), 0.45)
            add(t, bass(roots[(step // 8) % 4], BEAT * 1.8), 0.4)
        if step % 4 == 2:
            add(t, clap(), 0.25)
        t += BEAT / 2
        step += 1


def sting(t0):
    for i, n in enumerate([60, 64, 67, 72]):
        add(t0 + i * 0.12, stab([n, n + 4, n + 7], 0.5), 0.35)
    add(t0 + 0.5, stab([72, 76, 79, 84], 1.8), 0.5)
    add(t0 + 0.5, kick(), 1.0)
    add(t0 + 0.5, bass(36, 1.6), 0.7)


happy(0.0, 2.5, 0.6)
drama(3.0, 28.0)
happy(28.0, 102.0)
kids(102.0, 128.0)
happy(128.0, 177.0)
sting(177.0)

# suavizar cortes entre partes y normalizar
mix = mix[: int(TOTAL * SR)]
fade = int(0.05 * SR)
mix[:fade] *= np.linspace(0, 1, fade)
mix[-int(1.0 * SR):] *= np.linspace(1, 0, int(1.0 * SR))
mix = np.tanh(mix * 1.2)
mix = mix / np.max(np.abs(mix)) * 0.85
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with wave.open(OUT, 'w') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok', OUT, round(len(mix) / SR, 2), 's')
