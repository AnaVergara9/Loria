import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Loria} from '../characters/Loria';
import {Person} from '../characters/Person';
import {blinkAt, HAND, Pos, Scene, Sfx, talkAmount, tw, usePop, useT} from '../components/core';
import {Rewind} from '../components/effects';
import {C} from '../theme';

// E10 (1:42-2:08) CORTE SORPRESA: modo ninos en estilo crayon sobre hoja de cuaderno.
// Huevo -> pollito -> loro -> loro con gafas -> loro con gorra. Cada palabra del nino gana una estrella.
const HATCH = 3.5;
const S1 = 7.6; // estrella 1 ("Apple!")
const GROW1 = 10.5; // pollito -> loro
const S2 = 13.0; // estrella 2 ("Le chat!") -> gafas
const S3 = 17.0; // estrella 3 ("Thank you!") -> gorra
const MSG = 19.2;
const REW = 24.0;

const stageAt = (t: number) => (t < HATCH ? 0 : t < GROW1 ? 1 : t < S2 + 0.4 ? 2 : t < S3 + 0.4 ? 3 : 4);

export const E10_ModoNinos: React.FC = () => {
  const t = useT();
  const f = useCurrentFrame();
  const seed = Math.floor(f / 4); // las lineas "tiemblan" como dibujo a mano
  const stage = stageAt(t);
  const stars = t >= S3 ? 3 : t >= S2 ? 2 : t >= S1 ? 1 : 0;
  const wipe = tw(t, [0, 0.45], [0, 100]);
  return (
    <Scene id="E10" bg="#000" autoCam={false}>
      <AbsoluteFill style={{clipPath: `circle(${wipe * 1.3}% at 50% 50%)`}}>
        <svg width={0} height={0} style={{position: 'absolute'}}>
          <filter id="crayon">
            <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves={2} seed={seed} result="n" />
            <feDisplacementMap in="SourceGraphic" in2="n" scale={11} />
          </filter>
          <filter id="grain">
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={1} seed={3} />
            <feColorMatrix values="0 0 0 0 0.4  0 0 0 0 0.3  0 0 0 0 0.2  0 0 0 0.35 0" />
          </filter>
        </svg>
        <Paper />
        <AbsoluteFill style={{filter: 'url(#crayon) saturate(1.25)'}}>
          {/* titulo escrito a mano */}
          <div style={{position: 'absolute', left: 200, top: 40, fontFamily: HAND, fontSize: 96, color: '#E2342A', transform: 'rotate(-3deg)'}}>
            ¡Modo <span style={{color: '#2F7CC0'}}>niños</span>! ⭐
          </div>
          <Doodles t={t} />
          {/* el nino */}
          <Pos x={tw(t, [4, 4.6], [-300, 400])} y={830}>
            <Person hair="kid" hairColor="#5A3A1A" top="#E2342A" pants="#2F7CC0" width={300} mood={t > 6.4 ? 'happy' : 'neutral'} talk={talkAmount(t, 'E10', 'NIÑO')} blink={blinkAt(t, 2)} armL={t > 6.4 ? 140 : 10} armR={t > 6.4 ? 140 : 10} lookX={0.6} id="kid" />
          </Pos>
          <Pet t={t} stage={stage} />
          <LevelBar stage={stage} stars={stars} t={t} />
          {t > MSG && <Message t={t} />}
        </AbsoluteFill>
        <AbsoluteFill style={{filter: 'url(#grain)', mixBlendMode: 'multiply', opacity: 0.6}}>
          <svg width="1920" height="1080">
            <rect width="1920" height="1080" filter="url(#grain)" />
          </svg>
        </AbsoluteFill>
        {[S1, S2, S3].map((s, i) => (
          <FlyingStar key={i} at={s} t={t} />
        ))}
      </AbsoluteFill>
      <Rewind from={REW} to={26} label="◀◀" />
      <Sfx name="crayon" at={0} />
      <Sfx name="pop" at={0.3} />
      <Sfx name="crack" at={2.6} volume={0.6} />
      <Sfx name="crack" at={3.1} volume={0.8} />
      <Sfx name="crack" at={HATCH} />
      <Sfx name="star" at={HATCH + 0.05} />
      <Sfx name="pop" at={6.5} />
      <Sfx name="star" at={S1} />
      <Sfx name="sparkle" at={GROW1} />
      <Sfx name="pop" at={12.0} />
      <Sfx name="star" at={S2} />
      <Sfx name="ding" at={S2 + 0.4} />
      <Sfx name="pop" at={16.0} />
      <Sfx name="star" at={S3} />
      <Sfx name="ding" at={S3 + 0.4} />
      <Sfx name="crayon" at={MSG} />
      <Sfx name="applause" at={MSG + 1} volume={0.35} />
      <Sfx name="rewind" at={REW} />
    </Scene>
  );
};

/** Hoja de cuaderno. */
const Paper: React.FC = () => (
  <AbsoluteFill style={{background: '#FFFDF4'}}>
    <AbsoluteFill style={{background: 'repeating-linear-gradient(180deg, transparent 0 58px, #A9C8EC 58px 61px)'}} />
    <div style={{position: 'absolute', left: 150, top: 0, bottom: 0, width: 4, background: '#F08A9A'}} />
    {[200, 540, 880].map((y) => (
      <div key={y} style={{position: 'absolute', left: 50, top: y, width: 50, height: 50, borderRadius: '50%', background: '#E9E1CC', boxShadow: 'inset 3px 3px 6px rgba(0,0,0,0.2)'}} />
    ))}
  </AbsoluteFill>
);

/** La mascota segun el nivel: huevo, pollito o Loria (con gafas / gorra). */
const Pet: React.FC<{t: number; stage: number}> = ({t, stage}) => {
  const grow = usePop(stage === 1 ? HATCH : stage === 2 ? GROW1 : stage === 3 ? S2 + 0.4 : stage === 4 ? S3 + 0.4 : 0, 8, 220);
  const x = 1180;
  if (stage === 0) {
    const sh = tw(t, [0.5, HATCH], [0, 1]);
    return (
      <Pos x={x} y={800} rot={Math.sin(t * (10 + sh * 40)) * (4 + sh * 14)}>
        <svg width={300} height={380} viewBox="0 0 300 380">
          <ellipse cx={150} cy={210} rx={130} ry={165} fill="#FFF6E0" stroke="#5A3A1A" strokeWidth={10} />
          {[[90, 160], [200, 240], [150, 300], [210, 130]].map(([cx, cy], i) => (
            <circle key={i} cx={cx} cy={cy} r={18} fill={[C.green, C.orange, C.blue, C.yellow][i]} />
          ))}
          {t > 2.6 && <path d="M60 180 L100 210 L130 175 L165 215 L195 180" stroke="#5A3A1A" strokeWidth={8} fill="none" />}
          {t > 3.1 && <path d="M195 180 L230 205 L250 185" stroke="#5A3A1A" strokeWidth={8} fill="none" />}
        </svg>
      </Pos>
    );
  }
  if (stage === 1) {
    return (
      <Pos x={x} y={800} scale={0.4 + grow * 0.6}>
        <Chick t={t} />
      </Pos>
    );
  }
  return (
    <Pos x={x} y={830 - Math.abs(Math.sin(t * 6)) * (t > MSG ? 40 : 0)} scale={0.85 + grow * 0.15}>
      <Loria width={420} glasses={stage >= 3} cap={stage >= 4} blink={blinkAt(t)} wingR={Math.sin(t * 8) * 15 - 10} wingL={Math.sin(t * 8 + 1) * 15 - 10} lookX={-0.6} id="kidloria" />
    </Pos>
  );
};

/** Loria bebe: pollito verde con moño. */
const Chick: React.FC<{t: number}> = ({t}) => {
  const talk = talkAmount(t, 'E10', 'LORIA BEBÉ');
  const bl = blinkAt(t, 1);
  return (
    <svg width={340} height={360} viewBox="0 0 340 360">
      {/* cascaron de abajo */}
      <path d="M40 250 L80 220 L110 250 L150 215 L190 250 L230 218 L270 250 L300 225 Q300 350 170 350 Q40 350 40 250 Z" fill="#FFF6E0" stroke="#5A3A1A" strokeWidth={9} />
      <circle cx={170} cy={170} r={120} fill="#8DC23F" stroke="#2A0904" strokeWidth={10} />
      <path d="M150 52 Q160 20 175 50 Q190 25 195 58" stroke="#2A0904" strokeWidth={8} fill="#8DC23F" />
      <ellipse cx={170} cy={210} rx={70} ry={55} fill="#F59A2C" opacity={0.85} />
      {[125, 215].map((cx) => (
        <g key={cx}>
          <circle cx={cx} cy={150} r={30} fill={C.yellow} />
          {bl ? <path d={`M${cx - 18} 150 Q${cx} 162 ${cx + 18} 150`} stroke="#2A0904" strokeWidth={7} fill="none" /> : <><circle cx={cx} cy={152} r={18} fill="#2A0904" /><circle cx={cx - 6} cy={145} r={6} fill="#fff" /></>}
        </g>
      ))}
      <path d="M150 180 L190 180 L170 205 Z" fill={C.orange} stroke="#2A0904" strokeWidth={6} strokeLinejoin="round" />
      <path d={`M155 205 L185 205 L170 ${215 + talk * 25} Z`} fill="#E0661F" stroke="#2A0904" strokeWidth={6} strokeLinejoin="round" />
      <path d="M140 255 L170 270 L200 255 L200 285 L170 270 L140 285 Z" fill="#fff" stroke="#2A0904" strokeWidth={5} />
    </svg>
  );
};

/** Dibujitos que aparecen con cada palabra del nino. */
const Doodles: React.FC<{t: number}> = ({t}) => {
  const items = [
    {at: 6.5, x: 560, y: 150, el: '🍎', word: 'An apple!'},
    {at: 12.0, x: 790, y: 130, el: '🐱', word: "C'est un chat!"},
    {at: 16.0, x: 1430, y: 150, el: '💛', word: 'Thank you!'},
  ];
  return (
    <>
      {items.map((it) => {
        const p = Math.min(1, Math.max(0, (t - it.at) / 0.25));
        if (p <= 0) return null;
        return (
          <div key={it.word} style={{position: 'absolute', left: it.x, top: it.y, textAlign: 'center', transform: `scale(${p}) rotate(${Math.sin(it.at) * 10}deg)`}}>
            <div style={{fontSize: 130}}>{it.el}</div>
            <div style={{fontFamily: HAND, fontSize: 56, color: '#2F7CC0'}}>{it.word}</div>
          </div>
        );
      })}
    </>
  );
};

/** Barra de niveles: huevo, pollito, loro, gafas, gorra. */
const LevelBar: React.FC<{stage: number; stars: number; t: number}> = ({stage, stars}) => {
  const icons = ['🥚', '🐣', '🦜', '🤓', '🧢'];
  return (
    <div style={{position: 'absolute', left: 560, top: 845, width: 1240, display: 'flex', alignItems: 'center', gap: 16}}>
      <div style={{position: 'absolute', left: 40, right: 40, top: 46, height: 22, background: '#E9E1CC', borderRadius: 11, border: '5px solid #5A3A1A'}}>
        <div style={{width: `${(stage / 4) * 100}%`, height: '100%', background: C.green, borderRadius: 11}} />
      </div>
      {icons.map((ic, i) => (
        <div key={i} style={{position: 'relative', flex: 1, display: 'flex', justifyContent: 'center'}}>
          <div style={{width: 110, height: 110, borderRadius: '50%', background: i <= stage ? C.yellow : '#F2EEE2', border: `6px solid ${i === stage ? '#E2342A' : '#5A3A1A'}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 62, transform: `scale(${i === stage ? 1.18 : 1})`, opacity: i <= stage ? 1 : 0.55}}>
            {ic}
          </div>
        </div>
      ))}
      <div style={{position: 'absolute', right: -10, top: -110, fontSize: 70, fontFamily: HAND, color: '#5A3A1A'}}>
        {'⭐'.repeat(stars)}
        {'☆'.repeat(3 - stars)}
      </div>
    </div>
  );
};

/** Estrella que vuela del nino a la barra de estrellas. */
const FlyingStar: React.FC<{at: number; t: number}> = ({at, t}) => {
  const k = t - at;
  if (k < -0.6 || k > 0) return null;
  const p = (k + 0.6) / 0.6;
  const x = 420 + (1680 - 420) * p;
  const y = 450 - Math.sin(p * Math.PI) * 300 + (800 - 450) * p;
  return <div style={{position: 'absolute', left: x - 60, top: y - 60, fontSize: 120, transform: `rotate(${p * 720}deg) scale(${1 + Math.sin(p * Math.PI) * 0.6})`}}>⭐</div>;
};

const Message: React.FC<{t: number}> = ({t}) => {
  const p = Math.min(1, (t - MSG) / 0.4);
  return (
    <div style={{position: 'absolute', left: 420, top: 110, width: 1080, fontFamily: HAND, fontSize: 92, lineHeight: 1.1, color: '#E2342A', transform: `rotate(-4deg) scale(${0.6 + p * 0.4})`, opacity: p, textAlign: 'center', background: 'rgba(255,253,244,0.85)', borderRadius: 30, padding: 20}}>
      ¡Aprende <span style={{color: '#2F7CC0'}}>jugando</span>, con <span style={{color: '#E0A000'}}>estrellas</span> y <span style={{color: '#3E8537'}}>niveles</span>!
    </div>
  );
};
