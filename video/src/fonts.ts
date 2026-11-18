import {continueRender, delayRender, staticFile} from 'remotion';

// Carga las letras guardadas en public/fonts (no necesita internet).
const FONTS = [
  {family: 'LuckiestGuy', file: 'LuckiestGuy.woff2', weight: '400'},
  {family: 'Baloo2', file: 'Baloo2-600.woff2', weight: '600'},
  {family: 'Baloo2', file: 'Baloo2-800.woff2', weight: '800'},
  {family: 'PatrickHand', file: 'PatrickHand.woff2', weight: '400'},
];

if (typeof document !== 'undefined') {
  const handle = delayRender('Cargando letras');
  Promise.all(
    FONTS.map((f) => {
      const face = new FontFace(f.family, `url(${staticFile('fonts/' + f.file)}) format('woff2')`, {weight: f.weight});
      return face.load().then((loaded) => (document.fonts as unknown as Set<FontFace>).add(loaded));
    }),
  )
    .then(() => continueRender(handle))
    .catch((e) => {
      console.error(e);
      continueRender(handle);
    });
}

export const TITLE = 'LuckiestGuy, Impact, sans-serif';
export const BODY = 'Baloo2, Arial, sans-serif';
export const HAND = 'PatrickHand, "Comic Sans MS", cursive';
