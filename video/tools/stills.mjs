// Saca varias imagenes de prueba de una vez.
// Uso: node tools/stills.mjs carpeta_salida E01:30 E02:90 ...  (escena:cuadro)
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'node:path';

const [out, ...specs] = process.argv.slice(2);
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
for (const spec of specs) {
  const [id, frame] = spec.split(':');
  const composition = await selectComposition({serveUrl, id});
  await renderStill({composition, serveUrl, output: path.join(out, `${id}_${frame}.png`), frame: Number(frame), scale: 0.4});
  process.stdout.write('.');
}
console.log(' listo');
