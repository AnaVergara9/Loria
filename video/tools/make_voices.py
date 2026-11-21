"""
Genera TODAS las voces del video con voz sintetica (IA), gratis y sin internet.

Motores de voz:
  - Kokoro (voces en espanol, ingles y frances)       -> pip install kokoro-onnx soundfile
  - Piper (voces en espanol naturales)                  -> pip install piper-tts
  - Whisper via sherpa-onnx (solo para REVISAR que cada audio se entienda bien)

Uso (desde la carpeta video):
    python3 tools/make_voices.py CARPETA_MODELOS [ids...]

CARPETA_MODELOS debe tener:
  kokoro-v1.0.fp16.onnx y voices-v1.0.bin
      (https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0)
  vits-piper-es_AR-daniela-high/ y vits-piper-es_MX-claude-high/
      (https://github.com/k2-fsa/sherpa-onnx/releases/tag/tts-models)
  sherpa-onnx-whisper-small/   (opcional, para el control de calidad)
      (https://github.com/k2-fsa/sherpa-onnx/releases/tag/asr-models)

Como trabaja:
  1. Cada frase se divide en partes por idioma; cada parte la dice una voz NATIVA de ese idioma
     (asi el ingles suena a ingles y el frances a frances).
  2. Se generan varias versiones de cada frase y Whisper "escucha" cada una;
     se queda con la que mejor se entiende.
  3. Ajusta el tono (suave, para que no suene robotico) y el volumen.
  4. Guarda public/voces/<id>.wav y ajusta en src/dialogue.json lo que dura cada subtitulo.
Si mas adelante graban sus propias voces, basta con reemplazar el .wav con el mismo nombre.
"""
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata

import numpy as np
import soundfile as sf

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(BASE, 'public', 'voces')
DIALOGUE = os.path.join(BASE, 'src', 'dialogue.json')
SCENE_DUR = {'E00': 3, 'E01': 7, 'E02': 10, 'E03': 8, 'E04': 8, 'E05': 16, 'E06': 14, 'E07': 4, 'E08': 28,
             'E09': 4, 'E10': 26, 'E11': 14, 'E12': 18, 'E13': 8, 'E14': 12}
SR = 24000
ES, EN, GB, FR = 'es', 'en-us', 'en-gb', 'fr-fr'

# ---------- VOCES DE CADA PERSONAJE ----------
# Para cada idioma: (motor, voz). k = Kokoro, p = Piper.
# pitch = semitonos (+ agudo). cartoon=True cambia el tono "tipo caricatura" (mas natural en tonos muy agudos).
CAST = {
    'LORIA': dict(voices={ES: ('k', 'ef_dora'), EN: ('k', 'af_heart'), FR: ('k', 'ff_siwis')}, pitch=1.5, speed=1.1),
    'LORIA_LORO': dict(voices={ES: ('k', 'ef_dora'), EN: ('k', 'af_heart')}, pitch=3.0, speed=1.2, cartoon=True),
    'LORIA_GAFAS': dict(voices={ES: ('k', 'ef_dora'), EN: ('k', 'af_heart')}, pitch=1.0, speed=0.98),
    'LORIA BEBÉ': dict(voices={ES: ('k', 'ef_dora')}, pitch=4.0, speed=1.05, cartoon=True),
    'CAMILA': dict(voices={ES: ('p', 'es_AR-daniela-high'), EN: ('k', 'af_bella'), FR: ('k', 'ff_siwis')}, pitch=0.0, speed=1.0),
    'JEFE': dict(voices={EN: ('k', 'am_michael')}, pitch=-1.0, speed=0.92),
    'COLEGA': dict(voices={GB: ('k', 'bf_emma')}, pitch=0.0, speed=1.0),
    'NIÑO': dict(voices={EN: ('k', 'af_nova')}, pitch=3.0, speed=1.0, cartoon=True),
    'NIÑO_FR': dict(voices={FR: ('k', 'ff_siwis')}, pitch=2.0, speed=1.0),
    'ANDRÉS, 34': dict(voices={ES: ('k', 'em_alex')}, pitch=0.0, speed=1.05),
    'DOÑA MARTA, 60': dict(voices={ES: ('p', 'es_MX-claude-high')}, pitch=-1.0, speed=0.95),
}

# ---------- COMO SE PRONUNCIA CADA FRASE ----------
# parts = [(texto, idioma)]. El texto puede diferir del subtitulo para que suene bien.
LINES = {
    'e00_01': dict(parts=[('¿Hablas inglés? ¿Sí? ¡A ver, a ver!', ES)]),
    'e01_01': dict(parts=[('How old are you?', EN)]),
    'e01_02': dict(parts=[('I have twenty years!', EN)]),
    'e02_01': dict(parts=[('Je suis... un croissant?', FR)]),
    'e02_02': dict(parts=[('Where is the baño?', EN)]),
    'e02_03': dict(parts=[('Any questions, Camila?', GB)]),
    'e03_01': dict(parts=[('¿Te da pena hablar en inglés?', ES)]),
    'e03_02': dict(parts=[('¿Te quedas callada en francés?', ES)]),
    'e03_03': dict(parts=[('¿¡Pena de hablar!?', ES)]),
    'e04_01': dict(parts=[('¡No sufras más! ¡Ya llegó Loria!', ES)]),
    'e05_01': dict(parts=[('I have twenty years...', EN)], speed=0.9),
    'e05_02': dict(parts=[('I have twenty years! I have twenty years!', EN)], cast='LORIA_LORO'),
    'e05_03': dict(
        parts=[('Perdón. Se dice:', ES), ('I am twenty years old.', EN), ('En inglés, la edad va con el verbo', ES), ('to be.', EN), ('No con tener.', ES)],
        cast='LORIA_GAFAS',
    ),
    'e06_01': dict(parts=[('¡Escríbele en inglés o en francés, y Loria te corrige y te explica en español!', ES)], speed=1.2),
    'e07_01': dict(parts=[('¡Pero espera, hay más!', ES)]),
    'e08_01': dict(parts=[('¿No quieres escribir? ¡Háblale!', ES)]),
    'e08_02': dict(parts=[('En el bus, en la cocina... ¡o en pijama!', ES)]),
    'e08_03': dict(parts=[('I have tree brothers.', EN)]),
    'e08_04': dict(parts=[('Three!', EN), ('Con la lengua entre los dientes.', ES)], cast='LORIA_GAFAS'),
    'e08_05': dict(parts=[('Yesterday, I eat pizza.', EN)], speed=0.9),
    'e08_06': dict(parts=[('Pizza! Pizza!', EN)], cast='LORIA_LORO'),
    'e08_07': dict(parts=[('¡Casi! Se dice:', ES), ('I ate pizza.', EN)], cast='LORIA_GAFAS'),
    'e09_01': dict(parts=[('Un momento... ¿y para los más pequeños?', ES)]),
    'e10_01': dict(parts=[('An apple!', EN)]),
    'e10_02': dict(parts=[('¡Muy bien! ¡Ganaste una estrella!', ES)]),
    'e10_03': dict(parts=[("C'est un chat !", FR)], cast='NIÑO_FR'),
    'e10_04': dict(parts=[('Thank you!', EN)]),
    'e11_01': dict(parts=[('¿Quieres conversar?', ES)]),
    'e11_02': dict(parts=[('¿Quieres hacer ejercicios?', ES)]),
    'e11_03': dict(parts=[('¿O quieres corregir un texto?', ES)]),
    'e11_04': dict(parts=[('¡Tú eliges!', ES)]),
    'e12_01': dict(parts=[('¡Ahora pido mi cruasán en París sin pena!', ES)]),
    'e12_02': dict(parts=[('¡Practico inglés con mi nieto!', ES)]),
    'e12_03': dict(parts=[('¡Conseguí el trabajo!', ES), ('And yes... I am twenty years old!', EN)]),
    'e13_01': dict(parts=[('¿Y cuánto cuesta? ¡Nada! ¡Es totalmente gratis!', ES)], speed=1.15),
    'e13_02': dict(parts=[('¡Búscala en Telegram, como: Loria, a, bot!', ES)]),
    'e14_01': dict(parts=[('I am twenty years old! I am twenty years old!', EN)], cast='LORIA_LORO'),
    'e14_02': dict(parts=[('Loria... tú no tienes veinte años.', ES)]),
    'e14_03': dict(parts=[('Cierto. Tengo dos semanas. Te espero en Telegram.', ES)], cast='LORIA_GAFAS'),
}
GAP = 0.14


class Engines:
    def __init__(self, d):
        from kokoro_onnx import Kokoro
        self.k = Kokoro(os.path.join(d, 'kokoro-v1.0.fp16.onnx'), os.path.join(d, 'voices-v1.0.bin'))
        self.d = d
        self.piper = {}
        self.asr = {}
        wd = os.path.join(d, 'sherpa-onnx-whisper-small')
        if os.path.isdir(wd):
            import sherpa_onnx
            for lang in ('es', 'en', 'fr'):
                self.asr[lang] = sherpa_onnx.OfflineRecognizer.from_whisper(
                    encoder=os.path.join(wd, 'small-encoder.int8.onnx'), decoder=os.path.join(wd, 'small-decoder.int8.onnx'),
                    tokens=os.path.join(wd, 'small-tokens.txt'), language=lang, task='transcribe', num_threads=4)

    def say(self, engine, voice, text, lang, speed):
        if engine == 'k':
            s, sr = self.k.create(text, voice=voice, speed=speed, lang=lang)
            return resample(np.asarray(s, dtype=np.float32), sr)
        from piper import PiperVoice, SynthesisConfig
        if voice not in self.piper:
            vd = os.path.join(self.d, f'vits-piper-{voice}')
            self.piper[voice] = PiperVoice.load(os.path.join(vd, f'{voice}.onnx'), config_path=os.path.join(vd, f'{voice}.onnx.json'))
        v = self.piper[voice]
        chunks = list(v.synthesize(text, syn_config=SynthesisConfig(length_scale=1.0 / speed)))
        return resample(np.concatenate([c.audio_float_array for c in chunks]).astype(np.float32), v.config.sample_rate)

    def hear(self, x, lang):
        """Lo que Whisper entiende del audio x, escuchando en el idioma dado."""
        rec = self.asr.get(lang[:2])
        if rec is None:
            return None
        y = resample(np.concatenate([np.zeros(4000, np.float32), x, np.zeros(8000, np.float32)]), SR, 16000)
        st = rec.create_stream()
        st.accept_waveform(16000, y)
        rec.decode_stream(st)
        return st.result.text.strip()


def resample(x, sr, to=SR):
    if sr == to:
        return x
    n = int(len(x) * to / sr)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


def trim(x, thr=0.012):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    return x[max(0, idx[0] - int(0.03 * SR)): min(len(x), idx[-1] + int(0.08 * SR))]


def norm(t):
    t = unicodedata.normalize('NFKD', t.lower())
    t = ''.join(c for c in t if not unicodedata.combining(c))
    t = t.replace('twenty', '20').replace('veinte', '20').replace('cruasan', 'croissant').replace('cuasan', 'croissant')
    return re.sub(r'[^a-z0-9 ]', ' ', t).split()


def score(expected, heard):
    return difflib.SequenceMatcher(None, norm(expected), norm(heard)).ratio()


def fx(x, pitch, tempo, cartoon):
    with tempfile.TemporaryDirectory() as td:
        src, dst = os.path.join(td, 'a.wav'), os.path.join(td, 'b.wav')
        sf.write(src, x, SR)
        formant = 'shifted' if cartoon else 'preserved'
        chain = []
        if pitch or tempo != 1:
            chain.append(f'rubberband=pitch={2 ** (pitch / 12):.5f}:tempo={tempo:.4f}:formant={formant}:transients=smooth:window=long')
        chain += ['highpass=f=80', 'acompressor=threshold=-22dB:ratio=2.5:attack=8:release=120', 'loudnorm=I=-16:TP=-1.5:LRA=9']
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', src, '-af', ','.join(chain), '-ar', str(SR), '-ac', '1', dst], check=True)
        y, _ = sf.read(dst, dtype='float32')
        return y


def best_part(eng, text, lang, cast, speed):
    """Genera una parte en varias versiones y se queda con la que Whisper entiende mejor."""
    eng_name, voice = cast['voices'].get(lang) or cast['voices'].get(EN) or next(iter(cast['voices'].values()))
    klang = lang if (lang != GB or eng_name == 'k') else EN
    best = None
    for sp in (speed, speed * 0.9, speed * 1.08, speed * 0.82):
        raw = trim(eng.say(eng_name, voice, text, klang, sp))
        y = fx(raw, cast['pitch'], 1.0, cast.get('cartoon', False))
        heard = eng.hear(y, lang)
        sc = 1.0 if heard is None else score(text, heard)
        if best is None or sc > best[0] + 0.02:
            best = (sc, raw, heard)
        if sc >= 0.99:
            break
    return best


def main():
    d = sys.argv[1]
    only = set(sys.argv[2:])
    eng = Engines(d)
    os.makedirs(OUT, exist_ok=True)
    data = json.load(open(DIALOGUE, encoding='utf-8'))
    lines = data['lines']
    for i, l in enumerate(lines):
        if only and l['id'] not in only:
            continue
        cfg = LINES[l['id']]
        cast = CAST[cfg.get('cast', l['who'])]
        base_speed = cfg.get('speed', cast['speed'])
        nxt = [m['at'] for m in lines[i + 1:] if m['scene'] == l['scene']]
        limit = (nxt[0] if nxt else SCENE_DUR[l['scene']]) - l['at'] - 0.15
        pieces, notes, worst = [], [], 1.0
        for text, lang in cfg['parts']:
            sc, raw, heard = best_part(eng, text, lang, cast, base_speed)
            pieces += [raw, np.zeros(int(GAP * SR), dtype=np.float32)]
            notes.append(f'[{lang[:2]}] {heard}')
            worst = min(worst, sc)
        raw = np.concatenate(pieces[:-1])
        tempo = max(1.0, min(1.3, (len(raw) / SR) / limit))
        y = fx(raw, cast['pitch'], tempo, cast.get('cartoon', False))
        sc, heard = worst, ' + '.join(notes)
        sf.write(os.path.join(OUT, l['id'] + '.wav'), y, SR)
        final = len(y) / SR
        l['dur'] = round(min(limit + 0.15, max(final + 0.35, 1.2)), 2)
        warn = '' if sc >= 0.8 else '   <-- REVISAR'
        print(f"{l['id']} {final:4.1f}s/{limit:4.1f}s  calidad {sc:.2f}  oye: {heard}{warn}", flush=True)
    json.dump(data, open(DIALOGUE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('Listo.')


if __name__ == '__main__':
    main()
