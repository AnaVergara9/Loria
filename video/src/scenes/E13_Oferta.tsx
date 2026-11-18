import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Loria} from '../characters/Loria';
import {blinkAt, Confetti, Pos, Scene, Sfx, SlamText, talkAmount, TITLE, tw, usePop, useT} from '../components/core';
import {QRBox} from '../components/EndCard';
import {StudioBG} from '../components/Studio';
import {C} from '../theme';

// E13 (2:40-2:48) La oferta: "$99.999" se tacha y aparece "¡GRATIS!". Luego el QR y @loriaabot parpadeando.
const STRIKE = 1.8;
const FREE = 2.3;
const QR = 4.2;

export const E13_Oferta: React.FC = () => {
  const t = useT();
  const tag = usePop(0.2, 9, 200);
  const qr = usePop(QR, 10, 180);
  const strike = tw(t, [STRIKE, STRIKE + 0.25], [0, 1]);
  const moveUp = tw(t, [QR - 0.2, QR + 0.2], [0, 1]);
  return (
    <Scene id="E13">
      <StudioBG />
      {/* etiqueta de precio */}
      <div style={{position: 'absolute', left: 260 - moveUp * 160, top: 150 - moveUp * 90, transform: `scale(${tag * (1 - moveUp * 0.35)}) rotate(-6deg)`, transformOrigin: '0 0'}}>
        <div style={{position: 'relative', background: '#fff', border: `12px solid ${C.outline}`, borderRadius: 40, padding: '30px 70px 10px', boxShadow: `0 18px 0 ${C.outline}`}}>
          <div style={{fontFamily: TITLE, fontSize: 70, color: C.outline}}>ANTES</div>
          <div style={{fontFamily: TITLE, fontSize: 210, color: '#C0392B', lineHeight: 1}}>$99.999</div>
          <svg width={900} height={300} viewBox="0 0 900 300" style={{position: 'absolute', left: 10, top: 60}}>
            <path d="M20 220 C250 140 600 120 880 60" stroke="#E2342A" strokeWidth={34} fill="none" strokeLinecap="round" strokeDasharray={1000} strokeDashoffset={1000 * (1 - strike)} />
          </svg>
        </div>
      </div>
      {t >= FREE && (
        <AbsoluteFill style={{transform: `scale(${1 - moveUp * 0.4})`, transformOrigin: '8% 75%'}}>
          <SlamText at={FREE} size={230} color={C.yellow} x={-260} y={120} rot={-8}>
            ¡GRATIS!
          </SlamText>
        </AbsoluteFill>
      )}
      <Pos x={1520} y={1150}>
        <Loria width={540} beakOpen={talkAmount(t, 'E13', 'LORIA')} blink={blinkAt(t)} wingR={t > FREE ? -80 + Math.sin(t * 16) * 20 : -10} wingL={t > FREE ? -80 + Math.sin(t * 16 + 1) * 20 : -10} headTilt={Math.sin(t * 5) * 6} lookX={-0.5} />
      </Pos>
      {t >= QR && (
        <div style={{position: 'absolute', left: 760, top: 300, transform: `scale(${qr})`, transformOrigin: '50% 50%'}}>
          <QRBox size={330} blink />
        </div>
      )}
      <Confetti at={FREE} count={160} />
      <Sfx name="whoosh" at={0.15} />
      <Sfx name="stamp" at={0.3} volume={0.5} />
      <Sfx name="scratch" at={STRIKE} volume={0.7} />
      <Sfx name="kaching" at={FREE} />
      <Sfx name="applause" at={FREE + 0.1} volume={0.6} />
      <Sfx name="pop" at={QR} />
      <Sfx name="ding" at={QR + 0.1} volume={0.5} />
    </Scene>
  );
};
