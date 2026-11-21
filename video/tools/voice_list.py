# Genera GUION_VOCES.md a partir de src/dialogue.json
# Uso: python3 tools/voice_list.py
import json, os
base = os.path.join(os.path.dirname(__file__), '..')
d = json.load(open(os.path.join(base, 'src', 'dialogue.json'), encoding='utf-8'))['lines']
names = {
 'E00': 'Gancho', 'E01': 'La entrevista', 'E02': 'Montaje de fallos', 'E03': 'La pregunta', 'E04': 'Llega Loria',
 'E05': 'El chiste del loro', 'E06': 'Escríbele', 'E07': '¡Pero espera!', 'E08': 'Notas de voz', 'E09': 'Rebobinado',
 'E10': 'Modo niños', 'E11': 'Los botones', 'E12': 'Testimonios', 'E13': 'La oferta', 'E14': 'Final'}
starts, acc = {}, 0
for sid, dur in [('E00',3),('E01',7),('E02',10),('E03',8),('E04',8),('E05',16),('E06',14),('E07',4),('E08',28),('E09',4),('E10',26),('E11',14),('E12',18),('E13',8),('E14',12)]:
    starts[sid] = acc; acc += dur
def mmss(x):
    return f"{int(x // 60)}:{x % 60:04.1f}"
out = ['# Guion de voces de Loria', '',
       '> El video ya trae todas estas frases con **voz generada por IA** (en `public/voces/`). Esta lista sirve si quieren reemplazarlas por voces grabadas por ustedes.', '',
       'Cada frase tiene un **número de archivo**. Graben cada frase por separado y guárdenla con ese nombre',
       'en la carpeta `video/public/voces/` (por ejemplo `e05_03.mp3`; también sirve `.wav` o `.m4a`).',
       'El video la pone sola en el momento exacto. Si una frase no existe todavía, el video sigue funcionando con el subtítulo.', '',
       '- **Voz A**: Loria (y el jefe, la colega de la videollamada y Loria bebé, cambiando la voz).',
       '- **Voz B**: Camila (y los testimonios y el niño, cambiando la voz).', '',
       '**Duración**: el tiempo máximo que debe durar la frase. Si queda un poco más corta, no pasa nada; si queda más larga, se monta con la siguiente.', '']
cur = None
n = 0
for l in d:
    if l['scene'] != cur:
        cur = l['scene']
        out += ['', f"## {cur} · {names[cur]}", '', '| # | Archivo | Voz | Personaje | Frase | Empieza en | Duración | Cómo decirla |', '|---|---|---|---|---|---|---|---|']
    n += 1
    out.append(f"| {n} | `{l['id']}` | {l['voz']} | {l['who']} | {l['text']} | {mmss(starts[cur] + l['at'])} | {l['dur']:.1f} s | {l.get('note','')} |")
a = sum(1 for l in d if l['voz'] == 'A'); b = len(d) - a
out += ['', f'**Total**: {len(d)} frases ({a} para la voz A y {b} para la voz B).', '',
        '## Consejos para grabar', '',
        '- Graben con el celular cerca de la boca (un palmo), en un cuarto con cortinas o cobijas: suena mejor que un baño.',
        '- Dejen medio segundo de silencio antes y después; luego se puede recortar.',
        '- Loria (voz A): tono de presentadora de teletienda, aguda y con mucha energía. Cuando tiene **gafas** se calma y habla como profesora amable.',
        '- Cuando Loria "repite como loro" (e05_02, e08_06, e14_01), exageren: chillón, rápido y feliz.',
        '- Si una frase sale muy larga, díganla más rápido o avísenme y muevo los tiempos en `src/dialogue.json`.']
open(os.path.join(base, 'GUION_VOCES.md'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('ok', len(d))
