import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Loria} from '../characters/Loria';
import {blinkAt, Cam, Pos, Scene, Sfx, SlamText, talkAmount, tw, usePop, useT} from '../components/core';
import {Phone} from '../components/Phone';
import {StudioBG} from '../components/Studio';
import {C} from '../theme';
import {TITLE} from '../fonts';

// E06 (0:52-1:06) Escribele: celular gigante con el chat. Dos correcciones (ingles y frances)
// con contador +1, +2. Termina con "¡En ingles y en frances!".
const FLIP = 6.4; // el celular gira y cambia al ejemplo en frances
const END = 10.6;

export const E06_Escribele: React.FC = () => {
  const t = useT();
  const enter = usePop(0, 12, 120);
  const spin = tw(t, [FLIP - 0.2, FLIP + 0.3], [0, 360]);
  const french = t >= FLIP + 0.05;
  const zoom = t < 3.2 ? 1 : t < FLIP - 0.3 ? tw(t, [3.2, 3.5], [1, 1.35]) : t < 9.0 ? 1.05 : t < END ? tw(t, [9.0, 9.3], [1.05, 1.35]) : tw(t, [END, END + 0.3], [1.35, 1]);
  const msgsEN = [
    {at: 1.0, from: 'me' as const, text: "She don't like coffee", wrong: true, strikeAt: 2.8},
    {at: 3.3, from: 'loria' as const, fix: "She doesn't like coffee", why: 'Con "she" se usa "doesn\'t".'},
  ];
  const msgsFR = [
    {at: 7.0, from: 'me' as const, text: 'Je vais au la plage', wrong: true, strikeAt: 8.6},
    {at: 9.0, from: 'loria' as const, fix: 'Je vais à la plage', why: '"au" = à + le. Con "la" se dice "à la".'},
  ];
  const count = t >= 9.0 ? 2 : t >= 3.3 ? 1 : 0;
  return (
    <Scene id="E06">
      <StudioBG floor={false} />
      <Cam zoom={zoom} origin="38% 32%">
        <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
          <div style={{transform: `translateY(${(1 - enter) * 1200}px) rotateZ(${(1 - enter) * 25}deg)`, marginLeft: -280}}>
            <div style={{transform: `perspective(1600px) rotateY(${spin}deg)`}}>
              <Phone width={500} rotY={-10} msgs={french ? msgsFR : msgsEN} />
            </div>
          </div>
        </AbsoluteFill>
      </Cam>
      {/* Loria a un lado, senalando el celular */}
      <Pos x={1500} y={1180 + (1 - enter) * 600}>
        <Loria width={620} glasses wingL={t % 2 < 1 ? -50 : -40} wingR={Math.sin(t * 6) * 6} blink={blinkAt(t)} lookX={-0.7} headTilt={-4} beakOpen={talkAmount(t, 'E06', 'LORIA')} />
      </Pos>
      {/* banderita del idioma */}
      <div style={{position: 'absolute', left: 300, top: 70, transform: `scale(${t > 0.6 ? 1 : 0}) rotate(-8deg)`, fontFamily: TITLE, fontSize: 64, color: '#fff', background: french ? '#1F4FB0' : '#C0392B', border: `7px solid ${C.outline}`, borderRadius: 18, padding: '10px 26px 0'}}>
        {french ? '🇫🇷 FRANCÉS' : '🇬🇧 INGLÉS'}
      </div>
      <Counter n={count} />
      <SlamText at={END + 0.2} size={120} color={C.yellow} y={-280}>
        ¡En inglés <span style={{color: '#8DD14F'}}>y en francés!</span>
      </SlamText>
      <Sfx name="whoosh" at={0.05} />
      <Sfx name="pop" at={1.0} />
      <Sfx name="buzzer" at={2.8} volume={0.35} />
      <Sfx name="pop" at={3.3} />
      <Sfx name="ding" at={3.35} />
      <Sfx name="whoosh" at={FLIP - 0.2} />
      <Sfx name="pop" at={7.0} />
      <Sfx name="buzzer" at={8.6} volume={0.35} />
      <Sfx name="pop" at={9.0} />
      <Sfx name="ding" at={9.05} />
      <Sfx name="stamp" at={END + 0.2} volume={0.5} />
      <Sfx name="applause" at={END + 0.4} volume={0.35} />
    </Scene>
  );
};

/** Contador de frases corregidas (arriba a la derecha). */
const Counter: React.FC<{n: number}> = ({n}) => {
  const t = useT();
  if (n === 0) return null;
  const bump = n === 0 ? 0 : Math.max(0, 1 - ((t - (n === 1 ? 3.3 : 9.0)) / 0.3)) * 0.35;
  return (
    <div
      style={{
        position: 'absolute',
        right: 60,
        top: 60,
        transform: `scale(${1 + bump}) rotate(4deg)`,
        background: C.green,
        border: `8px solid ${C.outline}`,
        borderRadius: 28,
        padding: '14px 30px 4px',
        fontFamily: TITLE,
        color: '#fff',
        textAlign: 'center',
        boxShadow: `0 10px 0 ${C.outline}`,
      }}
    >
      <div style={{fontSize: 96, lineHeight: 1, color: C.yellow, WebkitTextStroke: `5px ${C.outline}`, paintOrder: 'stroke fill'}}>+{n}</div>
      <div style={{fontSize: 34}}>{n === 1 ? 'frase corregida' : 'frases corregidas'}</div>
    </div>
  );
};
