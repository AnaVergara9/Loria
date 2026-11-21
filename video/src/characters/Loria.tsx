import React from 'react';
import {useCurrentFrame} from 'remotion';
import {C} from '../theme';

/**
 * LORIA: la mascota dibujada como "titere" por piezas.
 * Todo esta en un lienzo de 896 x 1200 (el mismo tamano de la imagen original),
 * asi que las coordenadas coinciden con la ilustracion oficial.
 *
 * Cada prop mueve una pieza:
 *  - blink:     0 = ojos abiertos, 1 = cerrados
 *  - beakOpen:  0 = pico cerrado, 1 = pico bien abierto (para "hablar")
 *  - wingR:     grados que gira el ala derecha (negativo = la levanta)
 *  - wingL:     grados que gira el ala izquierda con el libro
 *  - headTilt:  grados que inclina la cabeza
 *  - lookX/lookY: hacia donde miran las pupilas (-1 a 1)
 *  - tail:      grados que mueve la cola
 *  - glasses / headphones / cap: accesorios encendidos o apagados
 *  - glassesDrop: 0 = gafas puestas, 1 = gafas arriba fuera del cuadro (para animar que se las pone)
 *  - book:      sin libro (por defecto) o {left, right} con el texto de cada pagina.
 *               Ej: book={{}} = libro original "ABC / Bonjour"; book={{left: '1', right: 'Hello'}}
 *  - showPencil: lapiz en el pico (apagado por defecto)
 */
export type LoriaPose = {
  blink?: number;
  beakOpen?: number;
  wingR?: number;
  wingL?: number;
  headTilt?: number;
  lookX?: number;
  lookY?: number;
  tail?: number;
  glasses?: boolean;
  glassesDrop?: number;
  headphones?: boolean;
  cap?: boolean;
  book?: {left?: string; right?: string} | false;
  showPencil?: boolean;
  showShadow?: boolean;
};

const O = C.outline;
const SW = 11; // grosor del contorno

export const Loria: React.FC<LoriaPose & {width?: number; style?: React.CSSProperties; id?: string}> = ({
  blink = 0,
  beakOpen = 0,
  wingR = 0,
  wingL = 0,
  headTilt = 0,
  lookX = 0,
  lookY = 0,
  tail = 0,
  glasses = false,
  glassesDrop = 0,
  headphones = false,
  cap = false,
  book = false,
  showPencil = false,
  showShadow = true,
  width = 896,
  style,
  id = 'loria',
}) => {
  // movimiento "vivo" automatico: respira, mece la cola, la cabeza y las alas
  const ft = useCurrentFrame() / 30;
  const idle = 1;
  tail += Math.sin(ft * 3.1) * 4 * idle;
  headTilt += Math.sin(ft * 2.2) * 1.8 * idle;
  wingR += Math.sin(ft * 2.6) * 3 * idle;
  wingL += Math.sin(ft * 2.6 + 1) * 3 * idle;
  const breath = Math.sin(ft * 2.6) * 0.014 * idle;
  const eyeScale = Math.max(0.08, 1 - blink);
  const px = lookX * 10;
  const py = lookY * 10;
  const jaw = -beakOpen * 30;
  const jawDrop = beakOpen * 34;
  const upper = beakOpen * 7;
  const g = (n: string) => `${id}-${n}`;

  return (
    <svg viewBox="0 0 896 1200" width={width} height={(width * 1200) / 896} style={{overflow: 'visible', ...style}}>
      <defs>
        <radialGradient id={g('belly')} cx="0.45" cy="0.3" r="0.75">
          <stop offset="0" stopColor="#E2342A" />
          <stop offset="0.45" stopColor="#EC6A2E" />
          <stop offset="1" stopColor="#F59A2C" />
        </radialGradient>
        <radialGradient id={g('cheek')} cx="0.5" cy="0.5" r="0.5">
          <stop offset="0" stopColor="#E2342A" stopOpacity="1" />
          <stop offset="0.6" stopColor="#E2342A" stopOpacity="0.85" />
          <stop offset="1" stopColor="#E2342A" stopOpacity="0" />
        </radialGradient>
        <linearGradient id={g('beak')} x1="0" y1="0" x2="0.3" y2="1">
          <stop offset="0" stopColor="#FBA455" />
          <stop offset="1" stopColor="#EE7424" />
        </linearGradient>
        <radialGradient id={g('iris')} cx="0.5" cy="0.75" r="0.75">
          <stop offset="0" stopColor="#7A3F1C" />
          <stop offset="0.55" stopColor="#3A120A" />
          <stop offset="1" stopColor="#220602" />
        </radialGradient>
        <radialGradient id={g('head')} cx="0.4" cy="0.25" r="0.85">
          <stop offset="0" stopColor="#8DC23F" />
          <stop offset="0.7" stopColor={C.green} />
          <stop offset="1" stopColor="#4E9A36" />
        </radialGradient>
        <linearGradient id={g('body')} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#5FA236" />
          <stop offset="0.5" stopColor={C.green} />
          <stop offset="1" stopColor="#4A9535" />
        </linearGradient>
        <linearGradient id={g('feather')} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#8CC9EE" />
          <stop offset="1" stopColor="#4F95CC" />
        </linearGradient>
        <clipPath id={g('headClip')}>
          <path d={HEAD} />
        </clipPath>
        <clipPath id={g('bowL')}>
          <path d="M292 686 C318 692 340 704 352 712 L352 730 C338 738 318 748 296 752 C286 728 286 704 292 686 Z" />
        </clipPath>
        <clipPath id={g('bowR')}>
          <path d="M372 712 C390 696 418 682 440 684 C452 708 450 736 436 756 C414 750 390 740 372 730 Z" />
        </clipPath>
      </defs>
      <g transform={`translate(448 1110) scale(${1 - breath} ${1 + breath}) translate(-448 -1110)`}>

      {/* Sombra en el piso */}
      {showShadow && <ellipse cx={465} cy={1112} rx={300} ry={42} fill="#C9C7DC" />}

      {/* COLA (detras de todo) */}
      <g transform={`rotate(${tail} 640 900)`}>
        <path
          d="M598 905 C668 780 760 640 868 540 C912 600 880 700 818 778 C776 830 726 884 672 932 Z"
          fill={`url(#${g('feather')})`}
          stroke={O}
          strokeWidth={SW}
          strokeLinejoin="round"
        />
        <path d="M680 850 C735 760 795 680 855 600" stroke={C.green} strokeWidth={46} strokeLinecap="round" fill="none" />
        <path
          d="M632 935 C712 850 798 756 866 700 C898 756 850 834 784 892 C744 928 702 956 660 976 Z"
          fill={`url(#${g('feather')})`}
          stroke={O}
          strokeWidth={SW}
          strokeLinejoin="round"
        />
        <path d="M700 905 C752 860 804 800 850 740" stroke={C.green} strokeWidth={34} strokeLinecap="round" fill="none" />
      </g>

      {/* PATAS */}
      <Foot x={355} flip={false} />
      <Foot x={565} flip />
      <ellipse cx={372} cy={1030} rx={52} ry={40} fill={C.greenDark} stroke={O} strokeWidth={SW} />
      <ellipse cx={540} cy={1030} rx={52} ry={40} fill={C.greenDark} stroke={O} strokeWidth={SW} />

      {/* CUERPO */}
      <path
        d="M290 660 C252 750 248 900 298 985 C335 1040 405 1052 462 1052 C540 1052 605 1020 630 955 C655 880 640 760 600 665 Z"
        fill={`url(#${g('body')})`}
        stroke={O}
        strokeWidth={SW}
        strokeLinejoin="round"
      />
      {/* Plumitas sueltas a los lados del cuerpo */}
      <path d="M262 900 L240 930 L272 925 Z M628 900 L652 925 L622 935 Z" fill={C.green} stroke={O} strokeWidth={7} strokeLinejoin="round" />
      {/* Pecho rojo-naranja */}
      <path
        d="M305 712 C278 800 288 930 340 990 C380 1028 470 1030 515 990 C556 930 552 790 528 712 Z"
        fill={`url(#${g('belly')})`}
      />
      {/* Brillos de plumas en el pecho */}
      <path d="M350 880 q20 18 40 0 M420 905 q20 18 40 0 M380 950 q20 18 40 0" stroke="#F7B04A" strokeWidth={6} fill="none" strokeLinecap="round" opacity={0.7} />

      {/* COLLAR AZUL */}
      <path d="M282 686 Q450 742 612 680 L616 712 Q450 772 286 716 Z" fill={C.navy} stroke={O} strokeWidth={8} strokeLinejoin="round" />

      {/* ALA DERECHA (se puede aletear) */}
      <g transform={`rotate(${wingR} 548 712)`}>
        <WingShape g={g} />
      </g>

      {/* CABEZA (todo lo de arriba gira junto) */}
      <g transform={`rotate(${headTilt} 450 670)`}>
        {/* Cresta */}
        <path
          d="M300 150 C318 118 372 112 402 140 L382 62 C432 74 462 116 466 152 L516 102 C542 128 544 176 524 210 L330 215 C306 192 296 172 300 150 Z"
          fill={C.green}
          stroke={O}
          strokeWidth={SW}
          strokeLinejoin="round"
        />
        <path d="M318 148 C340 130 368 132 382 145" stroke={C.greenLight} strokeWidth={9} fill="none" strokeLinecap="round" />
        <path d="M400 92 C425 105 440 125 444 145" stroke={C.greenLight} strokeWidth={9} fill="none" strokeLinecap="round" />

        {/* Forma de la cabeza */}
        <path d={HEAD} fill={`url(#${g('head')})`} stroke={O} strokeWidth={SW} strokeLinejoin="round" />
        <g clipPath={`url(#${g('headClip')})`}>
          {/* brillo de la frente */}
          <ellipse cx={330} cy={250} rx={60} ry={22} fill="#B6DE6E" opacity={0.75} transform="rotate(-20 330 250)" />
          {/* mancha roja */}
          <ellipse cx={330} cy={315} rx={105} ry={80} fill={`url(#${g('cheek')})`} />
          {/* parche amarillo del ojo izquierdo */}
          <ellipse cx={212} cy={398} rx={52} ry={100} fill={C.yellow} />
        </g>

        {/* OJO GRANDE (derecha) */}
        <ellipse cx={535} cy={398} rx={120} ry={136} fill={C.yellow} />
        <g transform={`translate(0 ${412 * (1 - eyeScale)}) scale(1 ${eyeScale})`}>
          <ellipse cx={535} cy={412} rx={82} ry={92} fill="#EDEAF2" stroke={O} strokeWidth={SW} />
          <g transform={`translate(${px} ${py})`}>
            <ellipse cx={538} cy={410} rx={66} ry={76} fill={`url(#${g('iris')})`} />
            <circle cx={503} cy={378} r={21} fill="#fff" />
            <circle cx={530} cy={399} r={7} fill="#fff" />
            <circle cx={562} cy={448} r={10} fill="#fff" />
          </g>
        </g>
        {blink > 0.5 && <path d="M455 412 Q535 440 615 412" stroke={O} strokeWidth={SW} fill="none" strokeLinecap="round" />}
        <path d="M502 282 Q536 262 572 282" stroke={O} strokeWidth={13} fill="none" strokeLinecap="round" />

        {/* OJO PEQUENO (izquierda, medio escondido) */}
        <g transform={`translate(0 ${398 * (1 - eyeScale)}) scale(1 ${eyeScale})`}>
          <ellipse cx={222} cy={398} rx={34} ry={64} fill="#EDEAF2" stroke={O} strokeWidth={9} />
          <g transform={`translate(${px * 0.6} ${py})`}>
            <ellipse cx={230} cy={400} rx={26} ry={52} fill={`url(#${g('iris')})`} />
            <circle cx={218} cy={368} r={11} fill="#fff" />
            <circle cx={236} cy={430} r={5} fill="#fff" />
          </g>
        </g>
        <path d="M200 282 Q220 266 242 278" stroke={O} strokeWidth={11} fill="none" strokeLinecap="round" />

        {/* BOCA: interior oscuro (se ve al abrir el pico) */}
        <g opacity={beakOpen > 0.02 ? 1 : 0}>
          <path d="M310 530 C360 526 410 510 428 482 C452 560 420 640 345 646 C312 630 300 580 310 530 Z" fill="#7A1A12" stroke={O} strokeWidth={9} />
          <ellipse cx={378} cy={612} rx={34} ry={16} fill="#E56B6B" />
        </g>

        {/* MANDIBULA + LAPIZ (bajan juntos al hablar) */}
        <g transform={`translate(0 ${jawDrop}) rotate(${jaw} 422 496)`}>
          <path
            d="M322 540 C362 536 402 520 420 494 C436 524 428 566 396 584 C368 600 334 596 318 578 Z"
            fill="#E8762A"
            stroke={O}
            strokeWidth={SW}
            strokeLinejoin="round"
          />
          {showPencil && <Pencil />}
        </g>

        {/* PICO DE ARRIBA */}
        <g transform={`rotate(${upper} 410 380)`}>

        <path
          d="M244 366 C282 326 380 322 416 368 C444 404 442 474 420 510 C402 540 364 546 340 556 C324 578 312 614 288 628 C252 604 220 554 216 486 C213 434 223 392 244 366 Z"
          fill={`url(#${g('beak')})`}
          stroke={O}
          strokeWidth={SW}
          strokeLinejoin="round"
        />
        <ellipse cx={292} cy={405} rx={22} ry={34} fill="#FDD3A8" opacity={0.9} transform="rotate(25 292 405)" />
        <ellipse cx={262} cy={470} rx={9} ry={14} fill="#FDD3A8" opacity={0.8} />
        <path d="M360 342 C380 360 392 385 395 410" stroke={O} strokeWidth={7} fill="none" strokeLinecap="round" opacity={0.6} />
        {/* sonrisa */}
        <path d="M388 498 Q410 510 432 484" stroke={O} strokeWidth={9} fill="none" strokeLinecap="round" />
        </g>

        {/* ACCESORIOS DE CABEZA */}
        {headphones && <Headphones />}
        {cap && <Cap />}
        {(glasses || glassesDrop > 0) && (
          <g transform={`translate(0 ${-glassesDrop * 900})`} opacity={glassesDrop > 0.98 ? 0 : 1}>
            <Glasses />
          </g>
        )}
      </g>


      {/* ALA IZQUIERDA: con libro, o un ala normal (espejo de la derecha) */}
      {book ? (
        <g transform={`rotate(${wingL} 285 760)`}>
          <path
            d="M300 720 C262 735 244 780 236 830 C228 870 214 900 190 915 L230 930 C268 905 292 860 300 810 Z"
            fill={C.green}
            stroke={O}
            strokeWidth={SW}
            strokeLinejoin="round"
          />
          <Book left={book.left ?? 'ABC'} right={book.right ?? 'Bonjour'} />
          {/* "mano" de plumas azules agarrando el libro */}
          <path
            d="M246 800 C278 840 262 900 222 922 C192 936 160 930 138 916 C108 900 104 868 126 852 C146 840 168 850 180 866 C190 842 214 822 246 800 Z"
            fill={`url(#${g('feather')})`}
            stroke={O}
            strokeWidth={SW}
            strokeLinejoin="round"
          />
          <path d="M170 880 L150 900 M200 878 L190 912 M228 862 L226 900" stroke={O} strokeWidth={6} strokeLinecap="round" />
        </g>
      ) : (
        <g transform="translate(888 0) scale(-1 1)">
          <g transform={`rotate(${-wingL} 548 712)`}>
            <WingShape g={g} />
          </g>
        </g>
      )}
      {/* MONO CON BANDERAS */}
      <Bow g={g} />
      </g>
    </svg>
  );
};

const HEAD =
  'M430 176 C565 170 692 240 724 372 C740 440 730 502 720 548 L740 618 L708 598 L712 642 L678 614 C638 662 560 694 452 694 C342 694 262 662 222 604 L186 594 L202 562 L150 548 L176 522 L140 502 L172 470 C166 398 176 330 216 270 C270 210 342 180 430 176 Z';

const Foot: React.FC<{x: number; flip: boolean}> = ({x, flip}) => {
  const s = flip ? -1 : 1;
  const toes = 'M0 0 Q-50 18 -92 48 M0 0 Q-8 45 -18 86 M0 0 Q45 25 78 62 M0 0 Q28 -10 52 -14';
  return (
    <g transform={`translate(${x} 1060) scale(${s} 1)`}>
      <path d={toes} stroke={O} strokeWidth={38} strokeLinecap="round" fill="none" />
      <path d={toes} stroke="#8C7A73" strokeWidth={22} strokeLinecap="round" fill="none" />
      <path d="M-8 -2 Q-48 14 -80 38" stroke="#A8968E" strokeWidth={6} strokeLinecap="round" fill="none" />
      <path d="M-104 50 l-18 16 l24 0 Z M-20 98 l-6 22 l18 -14 Z M88 70 l20 14 l-22 6 Z" fill="#3A3436" stroke={O} strokeWidth={6} strokeLinejoin="round" />
    </g>
  );
};

const Pencil: React.FC = () => (
  <g transform="translate(185 515) rotate(17.8)">
    <path d="M0 0 L34 -13 L34 13 Z" fill="#F5C99A" stroke={O} strokeWidth={7} strokeLinejoin="round" />
    <path d="M0 0 L12 -4.5 L12 4.5 Z" fill="#3A3436" />
    <rect x={34} y={-13} width={210} height={26} fill="#F7C531" stroke={O} strokeWidth={7} />
    <rect x={34} y={-5} width={210} height={6} fill="#E7A51F" />
    <rect x={244} y={-14} width={18} height={28} fill="#C9C9CF" stroke={O} strokeWidth={7} />
    <rect x={262} y={-14} width={24} height={28} rx={8} fill="#F08A9A" stroke={O} strokeWidth={7} />
  </g>
);

const WingShape: React.FC<{g: (n: string) => string}> = ({g}) => (
  <g>
    <path
      d="M528 700 C600 686 660 735 690 800 C718 860 745 905 752 958 C705 965 640 948 598 925 C552 898 520 858 512 800 C506 760 510 722 528 700 Z"
      fill={C.green}
      stroke={O}
      strokeWidth={SW}
      strokeLinejoin="round"
    />
    <path d="M560 740 C600 750 640 790 660 840" stroke={C.greenLight} strokeWidth={12} fill="none" strokeLinecap="round" opacity={0.8} />
    <path
      d="M590 870 C640 885 712 915 752 958 C700 966 640 950 592 925 C575 912 575 885 590 870 Z"
      fill={`url(#${g('feather')})`}
      stroke={O}
      strokeWidth={SW}
      strokeLinejoin="round"
    />
    <path d="M620 900 L700 935 M600 915 L660 945" stroke={O} strokeWidth={6} strokeLinecap="round" />
    <path d="M600 820 C630 830 660 860 690 900" stroke={C.greenDark} strokeWidth={7} fill="none" strokeLinecap="round" />
      </g>
);

/** Libro: "left" y "right" son los textos de cada pagina. "ABC" pinta las letras de colores. */
const Book: React.FC<{left: string; right: string}> = ({left, right}) => (
  <g>
    {/* tapa roja */}
    <path d="M38 708 L150 716 L258 676 L270 830 L158 872 L62 860 Z" fill="#B8332B" stroke={O} strokeWidth={10} strokeLinejoin="round" />
    {/* pagina izquierda */}
    <path d="M52 700 C90 696 128 704 152 724 L160 852 C130 838 100 836 72 842 Z" fill={C.cream} stroke={O} strokeWidth={9} strokeLinejoin="round" />
    {/* pagina derecha */}
    <path d="M152 724 C180 700 220 684 248 682 L258 816 C226 822 190 834 160 852 Z" fill="#FBF6EA" stroke={O} strokeWidth={9} strokeLinejoin="round" />
    {left === 'ABC' ? (
      <g>
    <text x={78} y={770} fontFamily="Arial Black, Arial, sans-serif" fontWeight={900} fontSize={42} fill="#E2342A" stroke="#7a1a12" strokeWidth={1.5}>
        A
      </text>
      <text x={116} y={786} fontFamily="Arial Black, Arial, sans-serif" fontWeight={900} fontSize={42} fill="#4CA63A" stroke="#1f4d18" strokeWidth={1.5}>
        B
      </text>
      <text x={100} y={830} fontFamily="Arial Black, Arial, sans-serif" fontWeight={900} fontSize={42} fill="#2F7CC0" stroke="#173e63" strokeWidth={1.5}>
        C
      </text>
      </g>
    ) : (
      <text x={106} y={790} textAnchor="middle" fontFamily="Arial Black, Arial, sans-serif" fontWeight={900} fontSize={Math.min(40, 150 / Math.max(1, left.length) * 1.6)} fill="#E2342A" transform="rotate(8 106 790)">
        {left}
      </text>
    )}
    <text
      x={164}
      y={782}
      fontFamily="Arial, sans-serif"
      fontWeight={700}
      fontSize={22}
      fill={O}
      transform="rotate(-17 164 782)"
      textLength={right.length > 7 ? 86 : undefined}
      lengthAdjust="spacingAndGlyphs"
    >
      {right}
    </text>
  </g>
);

const Bow: React.FC<{g: (n: string) => string}> = ({g}) => (
  <g>
    {/* lado Francia */}
    <g clipPath={`url(#${g('bowL')})`}>
      <rect x={280} y={670} width={26} height={100} fill="#1F4FB0" />
      <rect x={306} y={670} width={22} height={100} fill="#fff" />
      <rect x={328} y={670} width={30} height={100} fill="#E2342A" />
    </g>
    <path d="M292 686 C318 692 340 704 352 712 L352 730 C338 738 318 748 296 752 C286 728 286 704 292 686 Z" fill="none" stroke={O} strokeWidth={9} strokeLinejoin="round" />
    {/* lado Reino Unido */}
    <g clipPath={`url(#${g('bowR')})`}>
      <rect x={360} y={670} width={100} height={100} fill="#1F3F99" />
      <path d="M360 670 L460 770 M460 670 L360 770" stroke="#fff" strokeWidth={18} />
      <path d="M360 670 L460 770 M460 670 L360 770" stroke="#E2342A" strokeWidth={6} />
      <path d="M410 670 V770 M360 720 H460" stroke="#fff" strokeWidth={22} />
      <path d="M410 670 V770 M360 720 H460" stroke="#E2342A" strokeWidth={12} />
    </g>
    <path d="M372 712 C390 696 418 682 440 684 C452 708 450 736 436 756 C414 750 390 740 372 730 Z" fill="none" stroke={O} strokeWidth={9} strokeLinejoin="round" />
    {/* nudo */}
    <rect x={346} y={704} width={30} height={34} rx={9} fill="#fff" stroke={O} strokeWidth={9} />
    <rect x={354} y={708} width={8} height={26} fill="#E2342A" />
  </g>
);

export const Glasses: React.FC = () => (
  <g>
    <path d="M300 372 Q360 330 440 380" stroke={O} strokeWidth={14} fill="none" strokeLinecap="round" />
    <circle cx={535} cy={410} r={112} fill="rgba(190,225,255,0.22)" stroke={O} strokeWidth={16} />
    <ellipse cx={222} cy={400} rx={62} ry={96} fill="rgba(190,225,255,0.22)" stroke={O} strokeWidth={14} />
    <path d="M478 340 Q500 322 528 318" stroke="#fff" strokeWidth={10} fill="none" strokeLinecap="round" opacity={0.85} />
    <path d="M647 405 L722 380" stroke={O} strokeWidth={14} strokeLinecap="round" />
  </g>
);

const Headphones: React.FC = () => (
  <g>
    <path d="M175 420 C170 200 300 130 450 130 C600 130 735 200 730 420" stroke={O} strokeWidth={34} fill="none" strokeLinecap="round" />
    <path d="M175 420 C170 200 300 130 450 130 C600 130 735 200 730 420" stroke="#E2342A" strokeWidth={18} fill="none" strokeLinecap="round" />
    <rect x={128} y={380} width={78} height={130} rx={34} fill="#E2342A" stroke={O} strokeWidth={12} />
    <rect x={700} y={380} width={78} height={130} rx={34} fill="#E2342A" stroke={O} strokeWidth={12} />
    <rect x={146} y={400} width={20} height={70} rx={10} fill="#F47A6A" />
    <rect x={718} y={400} width={20} height={70} rx={10} fill="#F47A6A" />
  </g>
);

const Cap: React.FC = () => (
  <g>
    <path d="M250 255 C270 140 380 92 470 95 C590 98 680 160 690 260 C560 225 380 225 250 255 Z" fill={C.yellow} stroke={O} strokeWidth={13} strokeLinejoin="round" />
    <path d="M470 98 C480 140 488 190 490 232" stroke={O} strokeWidth={8} fill="none" />
    <path d="M250 255 C190 262 130 285 110 310 C180 305 260 290 320 262 Z" fill={C.orange} stroke={O} strokeWidth={13} strokeLinejoin="round" />
    <circle cx={470} cy={97} r={16} fill={C.orange} stroke={O} strokeWidth={9} />
    <path d="M330 170 Q350 150 380 145" stroke="#fff" strokeWidth={10} fill="none" strokeLinecap="round" opacity={0.7} />
  </g>
);
