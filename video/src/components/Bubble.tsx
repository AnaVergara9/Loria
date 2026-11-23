import React from 'react';
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {C} from '../theme';
import {BODY, HAND, TITLE} from '../fonts';

/**
 * GLOBO DE DIALOGO estilo comic.
 *  x, y   = donde va el borde del globo que mira hacia el personaje (en pixeles de pantalla)
 *  tx, ty = la punta de la colita (la boca del personaje)
 *  kind   = talk (normal) | shout (grito) | whisper (bajito)
 *  text   = admite marcas:  ~palabra~ = rojo tachado   +palabra+ = verde grande   *palabra* = resaltada
 * Las palabras aparecen una por una, como si se dijeran.
 */
export type BubbleKind = 'talk' | 'shout' | 'whisper' | 'silent' | 'crayon';

export const Bubble: React.FC<{
  x: number;
  y: number;
  tx: number;
  ty: number;
  text: string;
  dur: number; // segundos en pantalla
  kind?: BubbleKind;
  w?: number;
  who?: string;
}> = ({x: x0, y, tx, ty, text, dur, kind = 'talk', w: w0 = 640, who}) => {
  const w = Math.min(1500, w0 * 1.3);
  const x = Math.max(w / 2 + 20, Math.min(1900 - w / 2, x0)); // siempre dentro de la pantalla
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  const p = spring({frame: f, fps, config: {damping: 11, stiffness: 240}});
  const out = Math.max(0, Math.min(1, (dur - t) / 0.15));
  const sc = (0.3 + 0.7 * p) * out;
  const down = ty > y; // la colita apunta hacia abajo
  const segs = parse(text);
  const totalWords = segs.reduce((a, s) => a + s.words.length, 0);
  const shown = Math.min(totalWords, Math.floor(t * 9) + 1); // 9 palabras por segundo
  const shout = kind === 'shout';
  const whisper = kind === 'whisper';
  const silent = kind === 'silent'; // cine mudo: carton negro, letra clasica
  const crayon = kind === 'crayon'; // modo ninos: letra a mano
  const fill = silent ? '#111' : whisper ? '#F4F1EA' : crayon ? '#FFFDF4' : '#fff';
  const fs = shout ? 70 : whisper ? 50 : 58;
  const shakeX = shout ? Math.sin(f * 2.1) * 4 : 0;
  const shakeY = shout ? Math.cos(f * 1.7) * 3 : 0;
  const border = shout ? '#E2342A' : silent ? '#F2EDE0' : crayon ? '#5A3A1A' : C.outline;
  const bx = Math.max(x - w / 2 + 50, Math.min(x + w / 2 - 50, tx));
  const by = y + (down ? -6 : 6);
  let count = 0;
  return (
    <AbsoluteFill style={{pointerEvents: 'none', transform: `translate(${shakeX}px, ${shakeY}px)`}}>
      {/* colita */}
      <svg width="1920" height="1080" style={{position: 'absolute', opacity: out}}>
        <g transform={`translate(${tx} ${ty}) scale(${sc}) translate(${-tx} ${-ty})`}>
          <path
            d={`M${bx - 34} ${by} Q${(bx + tx) / 2 - 10} ${(by + ty) / 2} ${tx} ${ty} Q${(bx + tx) / 2 + 22} ${(by + ty) / 2} ${bx + 34} ${by} Z`}
            fill={fill}
            stroke={border}
            strokeWidth={8}
            strokeLinejoin="round"
            strokeDasharray={whisper ? '14 10' : undefined}
          />
        </g>
      </svg>
      <div
        style={{
          position: 'absolute',
          left: x,
          top: y,
          width: w,
          transform: `translate(-50%, ${down ? '-100%' : '0'}) scale(${sc}) rotate(${shout ? -2 : 0}deg)`,
          transformOrigin: `${50 + ((bx - x) / w) * 100}% ${down ? '100%' : '0%'}`,
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            background: fill,
            border: `${shout ? 10 : 8}px ${whisper ? 'dashed' : 'solid'} ${border}`,
            borderRadius: shout ? 24 : silent ? 10 : 46,
            outline: silent ? '3px solid #F2EDE0' : undefined,
            outlineOffset: silent ? -18 : undefined,
            padding: shout ? '18px 34px 10px' : silent ? '26px 46px 22px' : '16px 32px 10px',
            boxShadow: `0 10px 0 ${shout ? '#7A1A12' : 'rgba(42,9,4,0.35)'}`,
            fontFamily: shout ? TITLE : silent ? 'Georgia, "Times New Roman", serif' : crayon ? HAND : BODY,
            fontWeight: 800,
            fontSize: fs,
            lineHeight: 1.12,
            color: silent ? '#F2EDE0' : whisper ? '#6B5A50' : crayon ? '#2F7CC0' : C.outline,
            textAlign: 'center',
            letterSpacing: shout ? 1 : 0,
            fontStyle: whisper ? 'italic' : 'normal',
            position: 'relative',
          }}
        >
          {who && (
            <div style={{position: 'absolute', top: -30, left: 26, fontFamily: TITLE, fontSize: 26, color: '#fff', background: who === 'LORIA' ? C.green : who === 'CAMILA' ? C.orange : '#5B6CC4', border: `4px solid ${C.outline}`, borderRadius: 12, padding: '4px 12px 0'}}>{who}</div>
          )}
          {segs.map((sg, i) => (
            <span key={i}>
              {sg.words.map((wd, j) => {
                count++;
                const vis = count <= shown;
                if (wd === '/') return <br key={j} />;
                return (
                  <span key={j} style={{opacity: vis ? 1 : 0, display: 'inline-block', transform: vis ? 'none' : 'translateY(10px)'}}>
                    <span style={segStyle(sg.mark, fs)}>{wd}</span>
                    {j < sg.words.length - 1 ? ' ' : ''}
                  </span>
                );
              })}{' '}
            </span>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

type Seg = {mark: '' | '~' | '+' | '*'; words: string[]};
const parse = (text: string): Seg[] =>
  text
    .split(/(~[^~]+~|\+[^+]+\+|\*[^*]+\*)/)
    .filter((x) => x.trim())
    .map((x) => {
      const m = /^([~+*])(.*)\1$/.exec(x);
      return m ? {mark: m[1] as Seg['mark'], words: m[2].trim().split(/\s+/)} : {mark: '' as const, words: x.trim().split(/\s+/)};
    });

const segStyle = (mark: Seg['mark'], fs: number): React.CSSProperties => {
  switch (mark) {
    case '~':
      return {color: '#D02B20', textDecoration: 'line-through', textDecorationThickness: 6};
    case '+':
      return {color: '#2E8B2E', fontFamily: TITLE, fontSize: fs * 1.15, letterSpacing: 1};
    case '*':
      return {background: C.yellow, borderRadius: 10, padding: '0 8px', boxShadow: `0 4px 0 ${C.outline}`};
    default:
      return {};
  }
};

/**
 * ONOMATOPEYA de comic (¡BZZZ!, ¡ÑIIIC!, ¡DING!...) con estallido detras.
 * at = segundo de la escena en que aparece; dur = cuanto dura.
 */
export const Ono: React.FC<{
  at: number;
  text: string;
  x: number;
  y: number;
  dur?: number;
  size?: number;
  color?: string;
  burst?: string;
  rot?: number;
  noBurst?: boolean;
}> = ({at, text, x, y, dur = 0.9, size = 110, color = C.yellow, burst = '#E2342A', rot = -10, noBurst = false}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const k = f / fps - at;
  if (k < 0 || k > dur) return null;
  const p = spring({frame: f - Math.round(at * fps), fps, config: {damping: 8, stiffness: 300}});
  const out = Math.min(1, (dur - k) / 0.15);
  const pts = new Array(28)
    .fill(0)
    .map((_, i) => {
      const a = (i / 28) * Math.PI * 2;
      const r = i % 2 ? 0.62 : 1;
      return `${Math.cos(a) * r * 100},${Math.sin(a) * r * 62}`;
    })
    .join(' ');
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        transform: `translate(-50%, -50%) rotate(${rot + Math.sin(k * 30) * 2}deg) scale(${p * out})`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        pointerEvents: 'none',
      }}
    >
      {!noBurst && (
        <svg width={size * 5} height={size * 3.2} viewBox="-110 -70 220 140" style={{position: 'absolute'}}>
          <polygon points={pts} fill={burst} stroke={C.outline} strokeWidth={4} strokeLinejoin="round" />
        </svg>
      )}
      <div
        style={{
          position: 'relative',
          fontFamily: TITLE,
          fontSize: size,
          color,
          WebkitTextStroke: `${size / 11}px ${C.outline}`,
          paintOrder: 'stroke fill',
          textShadow: `0 ${size / 12}px 0 ${C.outline}`,
          whiteSpace: 'nowrap',
          paddingTop: size * 0.12,
        }}
      >
        {text}
      </div>
    </div>
  );
};
