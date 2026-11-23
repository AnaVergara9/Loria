import React from 'react';
import {Ono} from '../components/Bubble';
import {AbsoluteFill} from 'remotion';
import {Loria} from '../characters/Loria';
import {Cam, Pos, Scene, Sfx, shake, SlamText, talkAmount, tw, useT} from '../components/core';
import {SpeedLines} from '../components/effects';
import {StudioBG} from '../components/Studio';
import {C} from '../theme';

// E07 (1:06-1:10) "¡PERO ESPERA, HAY MAS!" Zoom brusco, luces rojas, sirena. A Loria se le esponjan las plumas.
export const E07_PeroEspera: React.FC = () => {
  const t = useT();
  const zoom = tw(t, [0, 0.15], [1, 1.55]);
  const sh = shake(t, t > 0.4 && t < 3 ? 0.7 : 0.1);
  const puff = 1 + Math.max(0, Math.sin(Math.min(1, (t - 0.5) / 0.3) * Math.PI / 2)) * 0.12;
  return (
    <Scene id="E07" subs={false}>
      <Cam zoom={zoom} origin="50% 40%" x={sh.x} y={sh.y}>
        <StudioBG red />
        <SpeedLines opacity={0.35} />
        {/* luz roja que gira */}
        <AbsoluteFill style={{background: `conic-gradient(from ${t * 720}deg at 50% 0%, rgba(255,40,40,0.55) 0deg, transparent 40deg, transparent 180deg, rgba(255,40,40,0.55) 220deg, transparent 260deg)`, mixBlendMode: 'screen'}} />
        <Pos x={960} y={1240} scale={puff}>
          <Loria width={760} beakOpen={talkAmount(t, 'E07', 'LORIA')} wingR={-70 + Math.sin(t * 30) * 15} wingL={-70 + Math.sin(t * 30 + 1) * 15} lookY={-0.2} tail={Math.sin(t * 25) * 10} />
        </Pos>
        <Feathers t={t} />
      </Cam>
      <SlamText at={0.5} size={150} color={C.yellow} y={-300} rot={-5}>
        ¡PERO ESPERA,
        <br />
        <span style={{color: '#fff'}}>HAY MÁS!</span>
      </SlamText>
      <Sfx name="whoosh" at={0} />
      <Sfx name="siren" at={0.15} volume={0.6} />
      <Sfx name="stamp" at={0.5} />
      <Sfx name="drumroll" at={2.4} volume={0.6} />
      <Ono at={0.2} text="¡UIUIUI!" x={1560} y={900} size={90} burst={C.yellow} color="#E2342A" dur={1.6} rot={6} />
    </Scene>
  );
};

/** Plumas que salen volando cuando Loria se esponja. */
const Feathers: React.FC<{t: number}> = ({t}) => {
  const k = t - 0.55;
  if (k < 0) return null;
  return (
    <AbsoluteFill>
      {new Array(16).fill(0).map((_, i) => {
        const a = (i / 16) * Math.PI * 2;
        const d = 200 + k * 700;
        return (
          <svg key={i} width={70} height={30} viewBox="0 0 70 30" style={{position: 'absolute', left: 960 + Math.cos(a) * d, top: 640 + Math.sin(a) * d * 0.7 + k * k * 300, transform: `rotate(${a * 57 + k * 400}deg)`, opacity: Math.max(0, 1 - k / 2.5)}}>
            <path d="M2 15 Q35 -5 68 15 Q35 35 2 15 Z" fill={i % 3 === 0 ? C.blue : C.green} stroke={C.outline} strokeWidth={4} />
          </svg>
        );
      })}
    </AbsoluteFill>
  );
};
