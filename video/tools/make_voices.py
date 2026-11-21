"""
Genera TODAS las voces del video con voz sintetica (Kokoro TTS, gratis y sin internet).

Uso (desde la carpeta video):
    pip install kokoro-onnx soundfile
    python3 tools/make_voices.py RUTA_A_LA_CARPETA_DEL_MODELO

La carpeta del modelo debe tener estos dos archivos (se descargan una vez de
https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0):
    kokoro-v1.0.fp16.onnx
    voices-v1.0.bin

Que hace:
  1. Lee cada frase de src/dialogue.json.
  2. La genera con la voz de su personaje. Las frases que mezclan idiomas se generan por
     partes (cada parte con la pronunciacion de su idioma) y se unen.
  3. Le cambia el tono (mas aguda para Loria, etc.) y la acelera si no cabe en su tiempo.
  4. La guarda en public/voces/<id>.wav (el video la pone sola).
  5. Ajusta la duracion del subtitulo en src/dialogue.json a lo que dura el audio,
     para que la boca del personaje se mueva solo mientras habla.

Si mas adelante graban sus propias voces, basta con reemplazar el .wav con el mismo nombre.
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(BASE, 'public', 'voces')
DIALOGUE = os.path.join(BASE, 'src', 'dialogue.json')
SCENE_DUR = {'E00': 3, 'E01': 7, 'E02': 10, 'E03': 8, 'E04': 8, 'E05': 16, 'E06': 14, 'E07': 4, 'E08': 28,
             'E09': 4, 'E10': 26, 'E11': 14, 'E12': 18, 'E13': 8, 'E14': 12}

ES, EN, GB, FR = 'es', 'en-us', 'en-gb', 'fr-fr'

# ---------- VOCES DE CADA PERSONAJE ----------
# voice: nombre de voz de Kokoro, o una mezcla {voz: peso}
# pitch: semitonos (+ = mas agudo)   speed: velocidad al generar
CAST = {
    'LORIA': dict(voice='ef_dora', pitch=3.0, speed=1.12),
    'LORIA_LORO': dict(voice='ef_dora', pitch=5.5, speed=1.3),  # cuando repite como loro
    'LORIA_GAFAS': dict(voice='ef_dora', pitch=2.0, speed=1.0),  # calmada, con gafas
    'LORIA BEBÉ': dict(voice='ef_dora', pitch=8.0, speed=1.1),
    'CAMILA': dict(voice={'ef_dora': 0.5, 'af_bella': 0.5}, pitch=0.5, speed=1.0),
    'JEFE': dict(voice='am_michael', pitch=-2.5, speed=0.9),
    'COLEGA': dict(voice='bf_emma', pitch=0.0, speed=1.0),
    'NIÑO': dict(voice='af_sky', pitch=5.0, speed=1.0),
    'ANDRÉS, 34': dict(voice='em_alex', pitch=0.0, speed=1.05),
    'DOÑA MARTA, 60': dict(voice={'ef_dora': 0.6, 'bf_isabella': 0.4}, pitch=-1.5, speed=0.95),
}

# ---------- COMO SE PRONUNCIA CADA FRASE ----------
# Lista de partes (texto, idioma). El texto puede diferir del subtitulo para que suene bien
# (ej. los numeros en letras). "cast" cambia la voz para esa frase.
LINES = {
    'e00_01': dict(parts=[('¿Hablas inglés? ¿Sí?... A ver.', ES)]),
    'e01_01': dict(parts=[('How old are you?', EN)]),
    'e01_02': dict(parts=[('I have twenty years!', EN)]),
    'e02_01': dict(parts=[('Je suis... un croissant?', FR)]),
    'e02_02': dict(parts=[('Where is the', EN), ('baño?', ES)]),
    'e02_03': dict(parts=[('Any questions, Camila?', GB)]),
    'e03_01': dict(parts=[('¿Te da pena hablar en inglés?', ES)]),
    'e03_02': dict(parts=[('¿Te quedas callada en francés?', ES)]),
    'e03_03': dict(parts=[('¿¡Pena de hablar!?', ES)]),
    'e04_01': dict(parts=[('¡No sufras más! ¡Llegó Loria!', ES)]),
    'e05_01': dict(parts=[('I have twenty years...', EN)], speed=0.9),
    'e05_02': dict(parts=[('I have twenty years! I have twenty years!', EN)], cast='LORIA_LORO'),
    'e05_03': dict(
        parts=[('Perdón. Se dice:', ES), ('I am twenty years old.', EN), ('En inglés, la edad va con', ES), ('to be,', EN), ('no con tener.', ES)],
        cast='LORIA_GAFAS',
    ),
    'e06_01': dict(parts=[('¡Escríbele en inglés o en francés, y Loria te corrige y te explica en español!', ES)], speed=1.3),
    'e07_01': dict(parts=[('¡Pero espera, hay más!', ES)]),
    'e08_01': dict(parts=[('¿No quieres escribir? ¡Háblale!', ES)]),
    'e08_02': dict(parts=[('En el bus, en la cocina... ¡o en pijama!', ES)]),
    'e08_03': dict(parts=[('I have tree brothers.', EN)]),
    'e08_04': dict(parts=[('Three!', EN), ('Con la lengua entre los dientes.', ES)], cast='LORIA_GAFAS'),
    'e08_05': dict(parts=[('Yesterday I eat pizza.', EN)], speed=0.9),
    'e08_06': dict(parts=[('Pizza! Pizza!', EN)], cast='LORIA_LORO'),
    'e08_07': dict(parts=[('¡Casi! Se dice:', ES), ('I ate pizza.', EN)], cast='LORIA_GAFAS'),
    'e09_01': dict(parts=[('Un momento... ¿y para los más pequeños?', ES)]),
    'e10_01': dict(parts=[('Apple!', EN)]),
    'e10_02': dict(parts=[('¡Muy bien! ¡Ganaste una estrella!', ES)]),
    'e10_03': dict(parts=[('Le chat!', FR)]),
    'e10_04': dict(parts=[('Thank you!', EN)]),
    'e11_01': dict(parts=[('¿Quieres conversar?', ES)]),
    'e11_02': dict(parts=[('¿Hacer ejercicios?', ES)]),
    'e11_03': dict(parts=[('¿Corregir un texto?', ES)]),
    'e11_04': dict(parts=[('¡Tú eliges!', ES)]),
    'e12_01': dict(parts=[('¡Ahora pido mi', ES), ('croissant', FR), ('en París sin pena!', ES)]),
    'e12_02': dict(parts=[('¡Practico inglés con mi nieto!', ES)]),
    'e12_03': dict(parts=[('¡Conseguí el trabajo!', ES), ('And yes... I am twenty years old!', EN)]),
    'e13_01': dict(parts=[('¿Y cuánto cuesta? ¡Nada! ¡Es totalmente gratis!', ES)], speed=1.2),
    'e13_02': dict(parts=[('¡Búscala en Telegram: arroba, loria a bot!', ES)]),
    'e14_01': dict(parts=[('I am twenty years old! I am twenty years old!', EN)], cast='LORIA_LORO'),
    'e14_02': dict(parts=[('Loria... tú no tienes veinte años.', ES)]),
    'e14_03': dict(parts=[('Cierto. Tengo dos semanas. Te espero en Telegram.', ES)], cast='LORIA_GAFAS'),
}

GAP = 0.12  # silencio entre partes de una frase (segundos)
SR = 24000


def style(k, voice):
    if isinstance(voice, str):
        return k.get_voice_style(voice)
    return sum(k.get_voice_style(v) * w for v, w in voice.items())


def trim(x, thr=0.01):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(0.03 * SR))
    b = min(len(x), idx[-1] + int(0.06 * SR))
    return x[a:b]


def ffmpeg_fx(src, dst, pitch, tempo):
    """Cambia el tono sin cambiar la velocidad, acelera si hace falta y deja el volumen parejo."""
    f = [f'rubberband=pitch={2 ** (pitch / 12):.5f}:tempo={tempo:.4f}:formant=preserved' if (pitch or tempo != 1) else 'anull',
         'highpass=f=90', 'acompressor=threshold=-20dB:ratio=3:attack=5:release=80', 'loudnorm=I=-16:TP=-1.5:LRA=7']
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', src, '-af', ','.join(f), '-ar', '48000', '-ac', '1', dst], check=True)


def main():
    model_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    k = Kokoro(os.path.join(model_dir, 'kokoro-v1.0.fp16.onnx'), os.path.join(model_dir, 'voices-v1.0.bin'))
    os.makedirs(OUT, exist_ok=True)
    data = json.load(open(DIALOGUE, encoding='utf-8'))
    lines = data['lines']
    report = []
    for i, l in enumerate(lines):
        cfg = LINES[l['id']]
        cast = CAST[cfg.get('cast', l['who'])]
        speed = cfg.get('speed', cast['speed'])
        st = style(k, cast['voice'])
        audio = []
        for text, lang in cfg['parts']:
            s, sr = k.create(text, voice=st, speed=speed, lang=lang)
            audio.append(trim(s))
            audio.append(np.zeros(int(GAP * SR)))
        x = np.concatenate(audio[:-1])
        length = len(x) / SR
        # tiempo disponible: hasta la siguiente frase de la misma escena, o el final de la escena
        nxt = [m['at'] for m in lines[i + 1:] if m['scene'] == l['scene']]
        limit = (nxt[0] if nxt else SCENE_DUR[l['scene']]) - l['at'] - 0.15
        tempo = 1.0
        if length > limit:
            tempo = min(1.35, length / limit)
        with tempfile.NamedTemporaryFile(suffix='.wav') as tmp:
            sf.write(tmp.name, x, SR)
            ffmpeg_fx(tmp.name, os.path.join(OUT, l['id'] + '.wav'), cast['pitch'], tempo)
        final = length / tempo
        l['dur'] = round(min(limit + 0.15, max(final + 0.35, 1.2)), 2)
        flag = '  <-- NO CABE' if final > limit + 0.05 else ('  (acelerada x%.2f)' % tempo if tempo > 1 else '')
        report.append(f"{l['id']}  {final:4.1f}s / {limit:4.1f}s disponibles{flag}")
        print(report[-1], flush=True)
    json.dump(data, open(DIALOGUE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('Listo:', len(lines), 'voces en public/voces/')


if __name__ == '__main__':
    main()
