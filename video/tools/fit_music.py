"""
Ajusta una cancion a la duracion exacta del video (180 s) y le pone el efecto de "radio vieja"
durante el "antes" en blanco y negro.

Uso:  python3 tools/fit_music.py CANCION.mp3
Crea: public/music/musica.wav   (el video la usa sola)

Como la alarga: busca dentro de la cancion dos momentos que suenen casi igual y "salta" de uno
al otro (repite un tramo), asi no se nota el corte. Asi la cancion termina justo con el video.
"""
import os
import subprocess
import sys

import numpy as np

SR = 44100
TOTAL = 180.0
BW_FROM, BW_TO = 3.0, 28.0  # escenas en blanco y negro (radio vieja)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public', 'music', 'musica.wav')


def load(path):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()


def envelope(x, hop=256):
    m = x.mean(1)
    n = len(m) // hop
    e = np.sqrt((m[: n * hop].reshape(n, hop) ** 2).mean(1))
    return np.maximum(0, np.diff(np.log(e + 1e-5), prepend=0)), SR / hop


def main():
    x = load(sys.argv[1])
    L = len(x) / SR
    need = TOTAL - L  # segundos que hay que repetir
    env, fps = envelope(x)
    # 1) duracion exacta de un pulso (beat) con autocorrelacion
    ac = np.correlate(env - env.mean(), env - env.mean(), 'full')[len(env) - 1:]
    lo, hi = int(0.3 * fps), int(1.0 * fps)
    k = lo + int(np.argmax(ac[lo:hi]))
    y0, y1, y2 = ac[k - 1], ac[k], ac[k + 1]
    beat = (k + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)) / fps
    print(f'pulso {beat:.4f}s ({60 / beat:.1f} BPM)')
    # 2) espectro por tramos para comparar como "suena" cada momento
    hop = int(0.05 * SR)
    m = x.mean(1)
    frames = np.lib.stride_tricks.sliding_window_view(m, 4096)[::hop]
    spec = np.log1p(np.abs(np.fft.rfft(frames * np.hanning(4096), axis=1))[:, :400])
    spec = spec / (np.linalg.norm(spec, axis=1, keepdims=True) + 1e-9)
    sfps = SR / hop
    best = None
    if need > 0:
        for nb in range(int((need - 6) / beat), int((need + 6) / beat) + 1):
            D = nb * beat  # salto de un numero entero de pulsos
            if nb % 8:
                continue  # solo compases completos (el pulso detectado es la mitad del real)
            for A in np.arange(D + 8, L - 12, beat / 4):
                i, j = int(A * sfps), int((A - D) * sfps)
                w = int(3 * sfps)
                a, b = spec[i - w: i + w], spec[j - w: j + w]
                if len(a) != len(b) or len(a) == 0:
                    continue
                c = float((a * b).sum(1).mean())
                score = c - abs(D - need) * 0.004
                if best is None or score > best[0]:
                    best = (score, A, D, c)
        _, A, D, c = best
        # afinar el punto exacto de union a nivel de muestra (menor diferencia de onda)
        ia, ib = int(A * SR), int((A - D) * SR)
        k = np.argmin([np.abs(x[ia + o: ia + o + 2048] - x[ib + o: ib + o + 2048]).mean() for o in range(-2048, 2048, 64)])
        o = -2048 + k * 64
        ia, ib = ia + o, ib + o
        fade = int(0.04 * SR)
        ramp = np.linspace(0, 1, fade)[:, None]
        mid = x[ia - fade: ia] * (1 - ramp) + x[ib - fade: ib] * ramp
        y = np.concatenate([x[: ia - fade], mid, x[ib:]])
        print(f'Union en {A:.2f}s -> salta a {A - D:.2f}s (parecido {c:.2f})')
    else:
        y = x
    n = int(TOTAL * SR)
    if len(y) >= n:
        y = y[:n]
    else:
        y = np.concatenate([y, np.zeros((n - len(y), 2), np.float32)])
    y[-int(0.5 * SR):] *= np.linspace(1, 0, int(0.5 * SR))[:, None]
    tmp = OUT + '.tmp.f32'
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    y.astype(np.float32).tofile(tmp)
    # radio vieja en el blanco y negro: menos graves y agudos, mas bajita (con transiciones suaves)
    radio = (f"[0:a]asplit=2[a][b];"
             f"[b]highpass=f=500,lowpass=f=2600,volume=0.55,acompressor=threshold=-18dB:ratio=4[r];"
             f"[a]volume='if(between(t,{BW_FROM},{BW_TO}),0,1)':eval=frame[n];"
             f"[r]volume='if(between(t,{BW_FROM},{BW_TO}),1,0)':eval=frame[rr];"
             f"[n][rr]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[out]")
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', tmp, '-filter_complex', radio, '-map', '[out]', '-ar', str(SR), OUT], check=True)
    os.remove(tmp)
    print('ok', OUT)


if __name__ == '__main__':
    main()
