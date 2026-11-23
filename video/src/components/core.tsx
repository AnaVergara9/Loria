import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  getStaticFiles,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {BODY, HAND, TITLE} from '../fonts';
import {Bubble, BubbleKind} from './Bubble';
import {GLOBOS, VOCES} from '../config';
import dialogue from '../dialogue.json';
import {C} from '../theme';
import {s, SCENES} from '../timeline';

// ---------- LETRAS ----------
export {TITLE, BODY, HAND};

// ---------- ANIMACION ----------
/** Rebote 0 -> 1 empezando en el segundo "at". */
export const usePop = (at: number, damping = 11, stiffness = 180) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: f - s(at), fps, config: {damping, stiffness}});
};

/** Interpolacion por segundos: tw(t, [0, 1], [10, 50]) */
export const tw = (t: number, secs: number[], vals: number[], ease = Easing.out(Easing.cubic)) =>
  interpolate(t, secs, vals, {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});

/** Segundo actual dentro de la escena. */
export const useT = () => useCurrentFrame() / 30;

/** Sacudida de camara (0..1 de intensidad). */
export const shake = (t: number, amount: number) => ({
  x: Math.sin(t * 91) * amount * 14,
  y: Math.cos(t * 77) * amount * 10,
});

// ---------- SONIDO ----------
export type SfxName =
  | 'pop' | 'whoosh' | 'buzzer' | 'ding' | 'sparkle' | 'scratch' | 'siren' | 'drumroll' | 'rewind'
  | 'static' | 'click' | 'stamp' | 'boing' | 'applause' | 'fanfare' | 'crayon' | 'crickets' | 'star'
  | 'crack' | 'kaching';

/** Efecto de sonido en el segundo "at" de la escena. */
export const Sfx: React.FC<{name: SfxName; at: number; volume?: number}> = ({name, at, volume = 0.8}) => (
  <Sequence from={s(at)} layout="none">
    <Audio src={staticFile(`sfx/${name}.wav`)} volume={volume} />
  </Sequence>
);

type Line = {
  id: string;
  scene: string;
  who: string;
  voz: string;
  at: number;
  dur: number;
  text: string;
  show?: string; // texto corto para el globo (con marcas ~ + *)
  bubble?: {x: number; y: number; tx: number; ty: number; kind?: BubbleKind; w?: number; label?: boolean};
};
const LINES = (dialogue as {lines: Line[]}).lines;

const findFile = (prefix: string) => {
  try {
    return getStaticFiles().find((f) => f.name.startsWith(prefix));
  } catch {
    return undefined;
  }
};

const WHO_COLOR: Record<string, string> = {
  LORIA: C.green,
  'LORIA BEBÉ': C.green,
  CAMILA: C.orange,
};

/**
 * Envuelve cada escena: pone las voces grabadas (si existen) y los subtitulos.
 * Asi cada escena funciona sola y tambien dentro del video completo.
 */
export const Scene: React.FC<{id: string; children: React.ReactNode; subs?: boolean; bg?: string; autoCam?: boolean}> = ({
  id,
  children,
  subs = true,
  bg = C.cream,
  autoCam = true,
}) => {
  const lines = LINES.filter((l) => l.scene === id);
  const t = useCurrentFrame() / 30;
  const cam = autoCam ? autoCamera(id, lines, t) : '';
  return (
    <AbsoluteFill style={{background: bg, overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: cam, transformOrigin: '50% 45%'}}>{children}</AbsoluteFill>
      {VOCES &&
        lines.map((l) => {
        const file = findFile(`voces/${l.id}.`);
        return file ? (
          <Sequence key={l.id} from={s(l.at)} layout="none">
            <Audio src={file.src} />
          </Sequence>
        ) : null;
      })}
      {subs &&
        lines
          .filter((l) => !(GLOBOS && l.show === ''))
          .map((l) => (
          <Sequence key={'sub' + l.id} from={s(l.at)} durationInFrames={s(l.dur)}>
            {GLOBOS && l.bubble ? (
              <Bubble {...l.bubble} text={l.show ?? l.text} dur={l.dur} who={l.bubble.label ? l.who : undefined} />
            ) : (
              <Subtitle who={l.who} text={l.text} />
            )}
          </Sequence>
        ))}
    </AbsoluteFill>
  );
};

/**
 * CAMARA AUTOMATICA: como un editor que cambia de plano.
 * Cada vez que alguien empieza a hablar (y cada ~2 s en momentos largos) salta a otro encuadre,
 * con un pequeno "golpe" de zoom. Entre cortes la camara se acerca despacio y se mece un poco.
 */
const SHOTS = [
  {z: 1.0, x: 0, y: 0},
  {z: 1.07, x: -40, y: -12},
  {z: 1.035, x: 36, y: 10},
  {z: 1.09, x: 14, y: -22},
];
const autoCamera = (id: string, lines: Line[], t: number) => {
  const dur = SCENES.find((sc) => sc.id === id)?.dur ?? 10;
  const cuts = new Set<number>([0]);
  lines.forEach((l) => {
    cuts.add(Math.round(l.at * 10) / 10);
    for (let k = l.at + 2.1; k < l.at + l.dur - 0.8; k += 2.1) cuts.add(Math.round(k * 10) / 10);
  });
  const sorted = [...cuts].sort((a, b) => a - b);
  // rellenar silencios largos con cortes cada ~2.2 s
  const all: number[] = [];
  sorted.forEach((c, i) => {
    all.push(c);
    const next = sorted[i + 1] ?? dur;
    for (let k = c + 2.2; k < next - 1.0; k += 2.2) all.push(k);
  });
  let idx = 0;
  for (let i = 0; i < all.length; i++) if (t >= all[i]) idx = i;
  const shot = SHOTS[idx % SHOTS.length];
  const since = t - all[idx];
  const z = shot.z + since * 0.012 + 0.035 * Math.exp(-since * 14);
  const rot = Math.sin(t * 0.8) * 0.3;
  const hx = Math.sin(t * 1.3) * 4;
  const hy = Math.cos(t * 1.1) * 3;
  return `translate(${shot.x + hx}px, ${shot.y + hy}px) scale(${z}) rotate(${rot}deg)`;
};

const Subtitle: React.FC<{who: string; text: string}> = ({who, text}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: f, fps, config: {damping: 13, stiffness: 220}});
  const color = WHO_COLOR[who] ?? '#5B6CC4';
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 46}}>
      <div
        style={{
          transform: `translateY(${(1 - p) * 60}px) scale(${0.85 + p * 0.15})`,
          opacity: p,
          display: 'flex',
          alignItems: 'center',
          gap: 18,
          background: 'rgba(255,248,232,0.96)',
          border: `6px solid ${C.outline}`,
          borderRadius: 26,
          padding: '12px 30px 12px 14px',
          boxShadow: `0 8px 0 ${C.outline}`,
          maxWidth: 1500,
        }}
      >
        <span
          style={{
            fontFamily: TITLE,
            fontSize: 30,
            color: '#fff',
            background: color,
            border: `4px solid ${C.outline}`,
            borderRadius: 14,
            padding: '6px 14px 0',
            whiteSpace: 'nowrap',
            letterSpacing: 1,
          }}
        >
          {who}
        </span>
        <span style={{fontFamily: BODY, fontWeight: 800, fontSize: 44, color: C.outline, lineHeight: 1.15}}>{text}</span>
      </div>
    </AbsoluteFill>
  );
};

/**
 * Musica de fondo: el archivo de audio que este dentro de public/music/ suena en todo el video.
 * Baja sola de volumen (a "duck") mientras alguien habla, para que se entiendan las voces.
 */
export const Music: React.FC<{volume?: number; duck?: number}> = ({volume = 0.6, duck = VOCES ? 0.35 : 1}) => {
  let file;
  try {
    file = getStaticFiles().find((f) => f.name.startsWith('music/') && /\.(mp3|wav|m4a|aac|ogg)$/i.test(f.name));
  } catch {
    file = undefined;
  }
  if (!file) return null;
  // momentos (en segundos del video completo) en que alguien habla
  const starts: Record<string, number> = {};
  let acc = 0;
  for (const sc of SCENES) {
    starts[sc.id] = acc;
    acc += sc.dur;
  }
  const talking = LINES.map((l) => [starts[l.scene] + l.at, starts[l.scene] + l.at + l.dur] as const);
  const vol = (f: number) => {
    const t = f / 30;
    let k = 0;
    for (const [a, b] of talking) {
      const v = Math.min(1, Math.max(0, Math.min((t - a + 0.2) / 0.2, (b - t + 0.3) / 0.3)));
      k = Math.max(k, v);
    }
    return volume * (1 - (1 - duck) * k);
  };
  return <Audio src={file.src} volume={vol} />;
};

// ---------- CAMARA ----------
/** Mueve todo lo de adentro como una camara: zoom, paneo, giro y sacudida. */
export const Cam: React.FC<{
  zoom?: number;
  x?: number;
  y?: number;
  rot?: number;
  origin?: string;
  blur?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({zoom = 1, x = 0, y = 0, rot = 0, origin = '50% 50%', blur = 0, children, style}) => (
  <AbsoluteFill
    style={{
      transform: `translate(${x}px, ${y}px) scale(${zoom}) rotate(${rot}deg)`,
      transformOrigin: origin,
      filter: blur ? `blur(${blur}px)` : undefined,
      ...style,
    }}
  >
    {children}
  </AbsoluteFill>
);

// ---------- TEXTOS ----------
/** Texto grande que entra "de golpe" (aparece gigante y se estrella en su sitio). */
export const SlamText: React.FC<{
  at: number;
  children: React.ReactNode;
  size?: number;
  color?: string;
  stroke?: string;
  rot?: number;
  x?: number;
  y?: number;
  out?: number;
  style?: React.CSSProperties;
}> = ({at, children, size = 120, color = C.yellow, stroke = C.outline, rot = -3, x = 0, y = 0, out, style}) => {
  const t = useT();
  const p = usePop(at, 9, 260);
  if (t < at) return null;
  const o = out !== undefined ? tw(t, [out, out + 0.15], [1, 0]) : 1;
  const sc = interpolate(p, [0, 1], [2.6, 1]);
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', pointerEvents: 'none'}}>
      <div
        style={{
          transform: `translate(${x}px, ${y}px) scale(${sc * (out !== undefined ? 0.6 + 0.4 * o : 1)}) rotate(${rot}deg)`,
          opacity: Math.min(1, p * 2) * o,
          filter: `blur(${Math.max(0, 1 - p) * 16}px)`,
          fontFamily: TITLE,
          fontSize: size,
          color,
          WebkitTextStroke: `${Math.max(6, size / 11)}px ${stroke}`,
          paintOrder: 'stroke fill',
          textShadow: `0 ${size / 14}px 0 ${stroke}`,
          textAlign: 'center',
          lineHeight: 1.0,
          letterSpacing: 2,
          ...style,
        }}
      >
        {children}
      </div>
    </AbsoluteFill>
  );
};

/** Sello que cae de golpe (ej. "¡ERROR!"). */
export const Stamp: React.FC<{at: number; text: string; color?: string; size?: number; rot?: number; x?: number; y?: number}> = ({
  at,
  text,
  color = '#E2342A',
  size = 170,
  rot = -12,
  x = 0,
  y = 0,
}) => {
  const t = useT();
  const p = usePop(at, 14, 320);
  if (t < at) return null;
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
      <div
        style={{
          transform: `translate(${x}px, ${y}px) rotate(${rot}deg) scale(${interpolate(p, [0, 1], [3.2, 1])})`,
          opacity: Math.min(1, p * 3),
          border: `${size / 9}px solid ${color}`,
          borderRadius: size / 5,
          padding: `${size / 12}px ${size / 3.5}px 0`,
          fontFamily: TITLE,
          fontSize: size,
          color,
          background: 'rgba(255,255,255,0.12)',
          boxShadow: `0 0 0 ${size / 30}px rgba(255,255,255,0.6) inset`,
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

/** Lluvia de confeti con los colores de Loria. */
export const Confetti: React.FC<{at: number; count?: number; dur?: number}> = ({at, count = 120, dur = 3}) => {
  const t = useT() - at;
  if (t < 0 || t > dur + 1) return null;
  const colors = [C.green, C.yellow, C.orange, C.red, C.blue, '#fff'];
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {new Array(count).fill(0).map((_, i) => {
        const r = (n: number) => {
          const v = Math.sin(i * 12.9898 + n * 78.233) * 43758.5453;
          return v - Math.floor(v);
        };
        const x0 = 960 + (r(1) - 0.5) * 300;
        const vx = (r(2) - 0.5) * 2600;
        const vy = -900 - r(3) * 1300;
        const x = x0 + vx * t * 0.6 + Math.sin(t * 6 + i) * 30;
        const y = 700 + vy * t + 1500 * t * t;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: 18 + r(4) * 16,
              height: 10 + r(5) * 10,
              background: colors[i % colors.length],
              border: `2px solid ${C.outline}`,
              borderRadius: i % 3 === 0 ? 20 : 3,
              transform: `rotate(${t * 600 * (r(6) - 0.5) + i * 40}deg) scaleX(${Math.cos(t * 10 + i)})`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/** Destello / brillo en forma de estrella. */
export const Sparkle: React.FC<{at: number; x: number; y: number; size?: number; color?: string}> = ({at, x, y, size = 120, color = '#fff'}) => {
  const t = useT() - at;
  if (t < 0 || t > 0.6) return null;
  const sc = Math.sin((t / 0.6) * Math.PI);
  return (
    <svg style={{position: 'absolute', left: x - size, top: y - size}} width={size * 2} height={size * 2} viewBox="-100 -100 200 200">
      <g transform={`scale(${sc}) rotate(${t * 200})`}>
        <path d="M0 -100 L18 -18 L100 0 L18 18 L0 100 L-18 18 L-100 0 L-18 -18 Z" fill={color} stroke={C.yellow} strokeWidth={6} />
      </g>
    </svg>
  );
};

// ---------- BOCA Y PARPADEO AUTOMATICOS ----------
/**
 * Devuelve cuanto abrir la boca (0..1) en el segundo t, segun los dialogos
 * de esa escena y ese personaje. Asi la boca se mueve sola cuando habla.
 */
export const talkAmount = (t: number, scene: string, who: string | string[]) => {
  const names = Array.isArray(who) ? who : [who];
  const l = LINES.find((x) => x.scene === scene && names.includes(x.who) && t >= x.at && t <= x.at + x.dur - 0.25);
  if (!l) return 0;
  const k = t - l.at;
  return Math.max(0, Math.sin(k * 17) * 0.5 + Math.sin(k * 7.3) * 0.5) * 0.95;
};

/** Parpadeo: 1 durante 3 cuadros cada ~3 segundos. */
export const blinkAt = (t: number, seed = 0) => {
  const period = 2.7 + (seed % 3) * 0.4;
  return (t + seed * 0.37) % period < 0.1 ? 1 : 0;
};

/** Coloca un personaje con los pies en (x, y). */
export const Pos: React.FC<{x: number; y: number; children: React.ReactNode; scale?: number; rot?: number; flip?: boolean; z?: number}> = ({
  x,
  y,
  children,
  scale = 1,
  rot = 0,
  flip = false,
  z,
}) => (
  <div
    style={{
      position: 'absolute',
      left: x,
      top: y,
      zIndex: z,
      transform: `translate(-50%, -100%) rotate(${rot}deg) scale(${flip ? -scale : scale}, ${scale})`,
      transformOrigin: '50% 100%',
    }}
  >
    {children}
  </div>
);
