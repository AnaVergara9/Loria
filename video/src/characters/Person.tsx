import React from 'react';
import {C} from '../theme';

/**
 * PERSONA: personaje humano de caricatura con volumen (sombras y brillos),
 * contorno grueso como Loria. De aqui salen Camila, el jefe, el mesero, los testimonios...
 * Lienzo: 400 x 1000. Los pies tocan el piso en y = 985.
 */
export type Mood = 'neutral' | 'happy' | 'sad' | 'angry' | 'shock' | 'skeptic' | 'shy' | 'proud';
export type Hair = 'bun' | 'short' | 'bald' | 'grayBun' | 'slick' | 'long' | 'curly' | 'kid';
export type Outfit = 'hoodie' | 'suit' | 'shirt' | 'vest' | 'cardigan' | 'pajama' | 'sweater';

export type PersonProps = {
  skin?: string;
  hair?: Hair;
  hairColor?: string;
  outfit?: Outfit;
  top?: string;
  accent?: string;
  pants?: string;
  shoes?: string;
  mood?: Mood;
  talk?: number; // 0..1 abre la boca
  blink?: number; // 0..1
  lookX?: number;
  lookY?: number;
  armL?: number; // grados (positivo = levanta hacia afuera)
  armR?: number;
  foreL?: number; // doblar antebrazo
  foreR?: number;
  headTilt?: number;
  glasses?: boolean;
  mustache?: boolean;
  beard?: boolean;
  blush?: boolean;
  phone?: boolean; // celular en la mano derecha
  sweat?: boolean;
  width?: number;
  id?: string;
  style?: React.CSSProperties;
  onlyBust?: boolean; // solo de la cintura para arriba
};

const O = C.outline;

const MOODS: Record<Mood, {brow: string; mouth: string; eyes?: string}> = {
  neutral: {brow: 'flat', mouth: 'smile'},
  happy: {brow: 'up', mouth: 'grin', eyes: 'happy'},
  sad: {brow: 'worried', mouth: 'sad'},
  angry: {brow: 'angry', mouth: 'flat'},
  shock: {brow: 'up', mouth: 'o', eyes: 'wide'},
  skeptic: {brow: 'skeptic', mouth: 'flat'},
  shy: {brow: 'worried', mouth: 'small'},
  proud: {brow: 'up', mouth: 'grin'},
};

export const Person: React.FC<PersonProps> = ({
  skin = '#F2C29B',
  hair = 'short',
  hairColor = '#3B2216',
  outfit = 'shirt',
  top = C.yellow,
  accent = C.red,
  pants = '#3E5C9A',
  shoes = '#4A2C1E',
  mood = 'neutral',
  talk = 0,
  blink = 0,
  lookX = 0,
  lookY = 0,
  armL = 8,
  armR = 8,
  foreL = 0,
  foreR = 0,
  headTilt = 0,
  glasses = false,
  mustache = false,
  beard = false,
  blush = true,
  phone = false,
  sweat = false,
  width = 400,
  id = 'p',
  style,
  onlyBust = false,
}) => {
  const g = (n: string) => `${id}-${n}`;
  const m = MOODS[mood];
  const skinDark = shade(skin, -28);
  const topDark = shade(top, -40);
  const vb = onlyBust ? '0 120 400 560' : '0 0 400 1000';
  const h = onlyBust ? (width * 560) / 400 : (width * 1000) / 400;

  const Arm = ({side, a, fa}: {side: 'L' | 'R'; a: number; fa: number}) => {
    const sx = side === 'L' ? 104 : 296;
    const rot = side === 'L' ? a : -a;
    const frot = side === 'L' ? fa : -fa;
    return (
      <g transform={`translate(${sx} 520) rotate(${rot})`}>
        <rect x={-25} y={-10} width={50} height={135} rx={25} fill={`url(#${g('top')})`} stroke={O} strokeWidth={8} />
        <g transform={`translate(0 112) rotate(${frot})`}>
          <rect x={-23} y={-8} width={46} height={120} rx={23} fill={`url(#${g('top')})`} stroke={O} strokeWidth={8} />
          <circle cx={0} cy={124} r={27} fill={skin} stroke={O} strokeWidth={8} />
          {phone && side === 'R' && (
            <g transform="translate(-22 92) rotate(-8)">
              <rect x={0} y={0} width={46} height={82} rx={9} fill="#2B2E3A" stroke={O} strokeWidth={6} />
              <rect x={6} y={8} width={34} height={62} rx={4} fill="#7FD3F7" />
            </g>
          )}
        </g>
      </g>
    );
  };

  return (
    <svg viewBox={vb} width={width} height={h} style={{overflow: 'visible', ...style}}>
      <defs>
        <radialGradient id={g('skin')} cx="0.4" cy="0.35" r="0.75">
          <stop offset="0" stopColor={shade(skin, 18)} />
          <stop offset="0.75" stopColor={skin} />
          <stop offset="1" stopColor={skinDark} />
        </radialGradient>
        <linearGradient id={g('top')} x1="0" y1="0" x2="1" y2="0.3">
          <stop offset="0" stopColor={shade(top, 20)} />
          <stop offset="0.6" stopColor={top} />
          <stop offset="1" stopColor={topDark} />
        </linearGradient>
        <linearGradient id={g('pants')} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor={shade(pants, 15)} />
          <stop offset="1" stopColor={shade(pants, -30)} />
        </linearGradient>
        <linearGradient id={g('hair')} x1="0" y1="0" x2="0.4" y2="1">
          <stop offset="0" stopColor={shade(hairColor, 35)} />
          <stop offset="0.5" stopColor={hairColor} />
          <stop offset="1" stopColor={shade(hairColor, -25)} />
        </linearGradient>
      </defs>

      {!onlyBust && <ellipse cx={200} cy={985} rx={150} ry={22} fill="rgba(42,9,4,0.18)" />}

      {/* PIERNAS */}
      <path d="M128 760 L140 950 L196 950 L200 790 L204 950 L260 950 L272 760 Z" fill={`url(#${g('pants')})`} stroke={O} strokeWidth={8} strokeLinejoin="round" />
      <path d="M200 795 L200 940" stroke={O} strokeWidth={5} opacity={0.5} />
      <ellipse cx={162} cy={962} rx={48} ry={24} fill={shoes} stroke={O} strokeWidth={8} />
      <ellipse cx={240} cy={962} rx={48} ry={24} fill={shoes} stroke={O} strokeWidth={8} />
      <ellipse cx={150} cy={954} rx={14} ry={6} fill="#fff" opacity={0.35} />
      <ellipse cx={228} cy={954} rx={14} ry={6} fill="#fff" opacity={0.35} />

      {/* BRAZO TRASERO IZQUIERDO */}
      <Arm side="L" a={armL} fa={foreL} />

      {/* TORSO */}
      <path
        d="M112 500 C150 476 250 476 288 500 C300 590 306 690 300 772 C240 798 160 798 100 772 C94 690 100 590 112 500 Z"
        fill={`url(#${g('top')})`}
        stroke={O}
        strokeWidth={8}
        strokeLinejoin="round"
      />
      <OutfitDetails outfit={outfit} top={top} accent={accent} skin={skin} />

      {/* BRAZO DERECHO */}
      <Arm side="R" a={armR} fa={foreR} />

      {/* CABEZA */}
      <g transform={`rotate(${headTilt} 200 460)`}>
        <rect x={176} y={410} width={48} height={80} rx={18} fill={skinDark} stroke={O} strokeWidth={7} />
        <HairBack hair={hair} fill={`url(#${g('hair')})`} />
        {/* orejas */}
        <ellipse cx={84} cy={318} rx={22} ry={30} fill={skin} stroke={O} strokeWidth={7} />
        <ellipse cx={316} cy={318} rx={22} ry={30} fill={skin} stroke={O} strokeWidth={7} />
        <ellipse cx={200} cy={300} rx={118} ry={130} fill={`url(#${g('skin')})`} stroke={O} strokeWidth={8} />
        {beard && <path d="M95 330 C100 420 150 440 200 440 C250 440 300 420 305 330 C290 390 250 400 200 400 C150 400 110 390 95 330 Z" fill={`url(#${g('hair')})`} stroke={O} strokeWidth={6} />}
        <HairFront hair={hair} fill={`url(#${g('hair')})`} color={hairColor} />

        {/* cejas */}
        <Brows kind={m.brow} color={hair === 'bald' || hair === 'grayBun' ? '#8A8A8A' : shade(hairColor, -10)} />

        {/* ojos */}
        <Eyes kind={m.eyes ?? 'normal'} blink={blink} lx={lookX} ly={lookY} />

        {blush && <ellipse cx={128} cy={362} rx={24} ry={13} fill="#F58A8A" opacity={0.5} />}
        {blush && <ellipse cx={272} cy={362} rx={24} ry={13} fill="#F58A8A" opacity={0.5} />}
        {/* nariz */}
        <path d="M192 338 Q204 356 192 362" stroke={skinDark} strokeWidth={6} fill="none" strokeLinecap="round" />
        {mustache && <path d="M150 384 C170 366 192 372 200 380 C208 372 230 366 250 384 C232 392 212 390 200 386 C188 390 168 392 150 384 Z" fill={hair === 'bald' ? '#7A7A7A' : hairColor} stroke={O} strokeWidth={5} />}
        <Mouth kind={m.mouth} talk={talk} />
        {glasses && (
          <g fill="rgba(200,230,255,0.25)" stroke={O} strokeWidth={7}>
            <circle cx={152} cy={312} r={40} />
            <circle cx={248} cy={312} r={40} />
            <path d="M192 306 Q200 298 208 306" fill="none" />
          </g>
        )}
        {sweat && <path d="M318 230 C330 250 336 266 324 274 C312 280 302 268 310 250 Z" fill="#8FD3FF" stroke={O} strokeWidth={5} />}
      </g>
    </svg>
  );
};

const Eyes: React.FC<{kind: string; blink: number; lx: number; ly: number}> = ({kind, blink, lx, ly}) => {
  if (kind === 'happy' || blink > 0.6) {
    const d = kind === 'happy' && blink <= 0.6 ? 'M126 318 Q152 290 178 318 M222 318 Q248 290 274 318' : 'M126 312 Q152 326 178 312 M222 312 Q248 326 274 312';
    return <path d={d} stroke={O} strokeWidth={8} fill="none" strokeLinecap="round" />;
  }
  const big = kind === 'wide' ? 1.25 : 1;
  const ir = kind === 'wide' ? 13 : 19;
  return (
    <g>
      {[152, 248].map((cx) => (
        <g key={cx}>
          <ellipse cx={cx} cy={312} rx={28 * big} ry={34 * big} fill="#fff" stroke={O} strokeWidth={7} />
          <circle cx={cx + 3 + lx * 9} cy={316 + ly * 9} r={ir} fill="#3A1A0E" />
          <circle cx={cx - 4 + lx * 9} cy={307 + ly * 9} r={ir * 0.38} fill="#fff" />
        </g>
      ))}
    </g>
  );
};

const Brows: React.FC<{kind: string; color: string}> = ({kind, color}) => {
  const d: Record<string, string> = {
    flat: 'M120 256 Q152 248 180 256 M220 256 Q248 248 280 256',
    up: 'M120 246 Q152 226 180 242 M220 242 Q248 226 280 246',
    angry: 'M120 244 Q152 250 184 268 M216 268 Q248 250 280 244',
    worried: 'M122 262 Q150 250 182 240 M218 240 Q250 250 278 262',
    skeptic: 'M120 260 Q152 256 180 262 M220 236 Q250 214 280 236',
  };
  return <path d={d[kind] ?? d.flat} stroke={color} strokeWidth={12} fill="none" strokeLinecap="round" />;
};

const Mouth: React.FC<{kind: string; talk: number}> = ({kind, talk}) => {
  if (talk > 0.05) {
    const hgt = 10 + talk * 34;
    return (
      <g>
        <ellipse cx={200} cy={396 + hgt / 3} rx={30 + talk * 6} ry={hgt / 2 + 4} fill="#7A1A12" stroke={O} strokeWidth={7} />
        <ellipse cx={200} cy={400 + hgt / 1.6} rx={16} ry={Math.max(2, hgt / 5)} fill="#E56B6B" />
        <rect x={180} y={388} width={40} height={8} rx={3} fill="#fff" />
      </g>
    );
  }
  switch (kind) {
    case 'grin':
      return (
        <g>
          <path d="M152 384 Q200 448 248 384 Z" fill="#7A1A12" stroke={O} strokeWidth={7} strokeLinejoin="round" />
          <path d="M162 388 Q200 400 238 388 L236 396 Q200 408 164 396 Z" fill="#fff" />
          <ellipse cx={200} cy={420} rx={18} ry={8} fill="#E56B6B" />
        </g>
      );
    case 'sad':
      return <path d="M166 410 Q200 380 234 410" stroke={O} strokeWidth={8} fill="none" strokeLinecap="round" />;
    case 'flat':
      return <path d="M172 398 L228 398" stroke={O} strokeWidth={8} strokeLinecap="round" />;
    case 'o':
      return <ellipse cx={200} cy={402} rx={20} ry={26} fill="#7A1A12" stroke={O} strokeWidth={7} />;
    case 'small':
      return <path d="M184 400 Q200 410 216 400" stroke={O} strokeWidth={7} fill="none" strokeLinecap="round" />;
    default:
      return <path d="M164 392 Q200 424 236 392" stroke={O} strokeWidth={8} fill="none" strokeLinecap="round" />;
  }
};

const HairBack: React.FC<{hair: Hair; fill: string}> = ({hair, fill}) => {
  switch (hair) {
    case 'bun':
      return (
        <g>
          <circle cx={205} cy={160} r={58} fill={fill} stroke={O} strokeWidth={8} />
          <path d="M160 190 Q205 172 250 190" stroke={C.yellow} strokeWidth={14} fill="none" strokeLinecap="round" />
        </g>
      );
    case 'grayBun':
      return <circle cx={200} cy={172} r={50} fill={fill} stroke={O} strokeWidth={8} />;
    case 'long':
      return <path d="M80 300 C70 160 330 160 320 300 L340 520 C300 540 100 540 60 520 Z" fill={fill} stroke={O} strokeWidth={8} strokeLinejoin="round" />;
    case 'curly':
      return (
        <g fill={fill} stroke={O} strokeWidth={7}>
          {[[90, 250], [120, 190], [170, 160], [230, 160], [280, 190], [310, 250], [80, 320], [320, 320]].map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r={48} />
          ))}
        </g>
      );
    default:
      return null;
  }
};

const HairFront: React.FC<{hair: Hair; fill: string; color: string}> = ({hair, fill, color}) => {
  const shine = <path d="M130 200 Q170 172 215 175" stroke="#fff" strokeWidth={9} fill="none" strokeLinecap="round" opacity={0.35} />;
  switch (hair) {
    case 'bun':
    case 'long':
      return (
        <g>
          <path
            d="M82 310 C66 190 150 156 205 158 C268 158 338 192 318 312 C300 258 262 228 214 232 C184 252 140 250 112 262 C94 276 86 292 82 310 Z"
            fill={fill}
            stroke={O}
            strokeWidth={8}
            strokeLinejoin="round"
          />
          <path d="M84 300 C76 340 80 380 92 410 L104 330 Z M316 300 C324 340 320 380 308 410 L296 330 Z" fill={fill} stroke={O} strokeWidth={6} strokeLinejoin="round" />
          {shine}
        </g>
      );
    case 'short':
    case 'slick':
      return (
        <g>
          <path
            d="M84 296 C70 176 150 146 206 148 C278 150 338 192 316 296 C306 250 290 220 262 208 C222 220 170 214 132 218 C106 234 92 258 84 296 Z"
            fill={fill}
            stroke={O}
            strokeWidth={8}
            strokeLinejoin="round"
          />
          {hair === 'slick' && <path d="M150 166 Q190 200 175 216" stroke={O} strokeWidth={5} fill="none" />}
          {shine}
        </g>
      );
    case 'bald':
      return (
        <g>
          <ellipse cx={90} cy={300} rx={22} ry={44} fill={fill} stroke={O} strokeWidth={6} />
          <ellipse cx={310} cy={300} rx={22} ry={44} fill={fill} stroke={O} strokeWidth={6} />
          <ellipse cx={170} cy={200} rx={40} ry={16} fill="#fff" opacity={0.45} transform="rotate(-15 170 200)" />
        </g>
      );
    case 'grayBun':
      return (
        <g>
          <path d="M84 300 C70 190 150 168 200 170 C255 170 330 190 316 300 C300 240 250 214 200 216 C150 214 100 240 84 300 Z" fill={fill} stroke={O} strokeWidth={8} />
          <path d="M120 230 Q160 205 200 210 M200 210 Q245 205 282 232" stroke="#fff" strokeWidth={5} fill="none" opacity={0.6} />
        </g>
      );
    case 'curly':
      return (
        <g fill={fill} stroke={O} strokeWidth={6}>
          {[[110, 220], [150, 192], [196, 184], [242, 192], [286, 222]].map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r={36} />
          ))}
        </g>
      );
    case 'kid':
      return (
        <path
          d="M86 290 C72 180 150 150 205 150 C275 152 334 190 316 290 L290 236 L266 262 L246 226 L222 258 L200 222 L176 256 L156 224 L134 258 L114 232 Z"
          fill={fill}
          stroke={O}
          strokeWidth={8}
          strokeLinejoin="round"
        />
      );
    default:
      return null;
  }
};

const OutfitDetails: React.FC<{outfit: Outfit; top: string; accent: string; skin: string}> = ({outfit, top, accent, skin}) => {
  switch (outfit) {
    case 'hoodie':
      return (
        <g>
          <path d="M140 494 C160 540 240 540 260 494" stroke={O} strokeWidth={8} fill={shade(top, -25)} />
          <path d="M180 530 L176 600 M220 530 L224 600" stroke="#fff" strokeWidth={6} strokeLinecap="round" />
          <path d="M140 670 L260 670 L250 740 L150 740 Z" fill={shade(top, -15)} stroke={O} strokeWidth={6} strokeLinejoin="round" />
        </g>
      );
    case 'suit':
      return (
        <g>
          <path d="M160 486 L200 600 L240 486 Z" fill="#fff" stroke={O} strokeWidth={6} />
          <path d="M192 510 L208 510 L214 600 L200 620 L186 600 Z" fill={accent} stroke={O} strokeWidth={5} strokeLinejoin="round" />
          <path d="M150 490 L200 640 L130 560 Z M250 490 L200 640 L270 560 Z" fill={shade(top, -20)} stroke={O} strokeWidth={6} strokeLinejoin="round" />
          <circle cx={200} cy={690} r={7} fill={O} />
        </g>
      );
    case 'vest':
      return (
        <g>
          <path d="M150 490 C170 520 230 520 250 490 L270 770 L130 770 Z" fill="#fff" stroke={O} strokeWidth={0} />
          <path d="M150 490 L200 620 L200 785 L104 770 L112 500 Z M250 490 L200 620 L200 785 L296 770 L288 500 Z" fill="#2B2B33" stroke={O} strokeWidth={6} strokeLinejoin="round" />
          <path d="M176 500 L200 512 L224 500 L224 524 L200 512 L176 524 Z" fill={accent} stroke={O} strokeWidth={5} strokeLinejoin="round" />
        </g>
      );
    case 'cardigan':
      return (
        <g>
          <path d="M160 490 L200 560 L240 490" stroke={O} strokeWidth={6} fill={skin} />
          <path d="M200 560 L200 780" stroke={O} strokeWidth={6} />
          {[600, 650, 700].map((y) => (
            <circle key={y} cx={214} cy={y} r={7} fill={C.yellow} stroke={O} strokeWidth={4} />
          ))}
        </g>
      );
    case 'pajama':
      return (
        <g>
          {[[150, 560], [240, 590], [180, 660], [260, 700], [140, 720], [210, 740]].map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r={12} fill="#fff" opacity={0.7} />
          ))}
          <path d="M160 492 L200 540 L240 492" stroke={O} strokeWidth={6} fill="none" />
        </g>
      );
    case 'sweater':
      return (
        <g>
          <path d="M150 494 C170 520 230 520 250 494" stroke={O} strokeWidth={8} fill={shade(top, -20)} />
          <path d="M104 600 L296 600 M100 640 L300 640" stroke={shade(top, -25)} strokeWidth={10} />
        </g>
      );
    default:
      return <path d="M160 490 L200 530 L240 490 L222 520 L200 540 L178 520 Z" fill="#fff" stroke={O} strokeWidth={6} strokeLinejoin="round" />;
  }
};

/** Aclara (+) u oscurece (-) un color hex. */
export function shade(hex: string, amt: number) {
  const n = parseInt(hex.replace('#', ''), 16);
  const c = (v: number) => Math.max(0, Math.min(255, v + amt));
  const r = c(n >> 16);
  const g = c((n >> 8) & 255);
  const b = c(n & 255);
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`;
}

// ---------- ELENCO ----------
export const CAMILA: PersonProps = {skin: '#E9B48C', hair: 'bun', hairColor: '#3B2216', outfit: 'hoodie', top: '#F7B733', pants: '#3E5C9A', id: 'camila'};
export const CAMILA_SUIT: PersonProps = {...CAMILA, outfit: 'suit', top: '#2E4A7D', accent: C.orange, pants: '#2E4A7D', id: 'camilasuit'};
export const CAMILA_PJ: PersonProps = {...CAMILA, outfit: 'pajama', top: '#9AC7EE', pants: '#9AC7EE', id: 'camilapj'};
export const JEFE: PersonProps = {skin: '#E8B98F', hair: 'bald', hairColor: '#9A9A9A', outfit: 'suit', top: '#4B5563', accent: '#C0392B', pants: '#3A4150', mustache: true, glasses: true, blush: false, id: 'jefe'};
export const MESERO: PersonProps = {skin: '#F3CDA8', hair: 'slick', hairColor: '#1E1A1A', outfit: 'vest', top: '#ffffff', accent: '#C0392B', pants: '#222', mustache: true, blush: false, id: 'mesero'};
export const ANDRES: PersonProps = {skin: '#C98E64', hair: 'short', hairColor: '#2A1A12', outfit: 'shirt', top: C.green, pants: '#5B4636', beard: true, id: 'andres'};
export const MARTA: PersonProps = {skin: '#F0C5A2', hair: 'grayBun', hairColor: '#C9C9CF', outfit: 'cardigan', top: '#C0504D', pants: '#5A4A6A', glasses: true, id: 'marta'};
