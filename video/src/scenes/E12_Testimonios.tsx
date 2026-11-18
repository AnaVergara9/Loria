import React from 'react';
import {AbsoluteFill} from 'remotion';
import {ANDRES, CAMILA_SUIT, JEFE, MARTA, Person} from '../characters/Person';
import {blinkAt, BODY, Cam, Confetti, Pos, Scene, Sfx, talkAmount, TITLE, tw, useT} from '../components/core';
import {CornerTag, Swipe} from '../components/effects';
import {CafeBG, KitchenBG, OfficeBG} from '../components/Sets';
import {C} from '../theme';

// E12 (2:22-2:40) Testimonios de teletienda (6 s cada uno) con letrero de nombre y "Dramatizacion".
// Andres (cafe en Paris), Dona Marta (con su nieto), Camila (la misma oficina, ahora con el trabajo).
export const E12_Testimonios: React.FC = () => {
  const t = useT();
  const i = Math.min(2, Math.floor(t / 6));
  const k = t - i * 6;
  return (
    <Scene id="E12">
      <Cam zoom={1.05 + k * 0.025} origin="40% 45%">
        {i === 0 && (
          <>
            <CafeBG />
            <Pos x={760} y={1250}>
              <Person {...ANDRES} width={480} mood="happy" talk={talkAmount(t, 'E12', 'ANDRÉS, 34')} blink={blinkAt(t, 1)} armR={60} foreR={-110} armL={15} id="andres12" />
            </Pos>
            <div style={{position: 'absolute', left: 860, top: 420, fontSize: 120, transform: `rotate(${Math.sin(t * 3) * 10}deg)`}}>🥐</div>
          </>
        )}
        {i === 1 && (
          <>
            <KitchenBG />
            <Pos x={700} y={1230}>
              <Person {...MARTA} width={440} mood="happy" talk={talkAmount(t, 'E12', 'DOÑA MARTA, 60')} blink={blinkAt(t, 2)} armR={45} foreR={-30} id="marta12" />
            </Pos>
            <Pos x={1060} y={1130}>
              <Person hair="kid" hairColor="#3B2216" top={C.blue} pants="#2F4A7A" width={280} mood="happy" armL={130} armR={130} blink={blinkAt(t, 5)} lookX={-0.6} id="nieto" />
            </Pos>
          </>
        )}
        {i === 2 && (
          <>
            <OfficeBG />
            <Pos x={1400} y={1150}>
              <Person {...JEFE} width={360} mood="happy" armL={140} armR={140} foreL={-40} foreR={-40} blink={blinkAt(t, 3)} lookX={-0.6} id="jefe12" />
            </Pos>
            <Pos x={760} y={1230}>
              <Person {...CAMILA_SUIT} width={460} mood="proud" talk={talkAmount(t, 'E12', 'CAMILA')} blink={blinkAt(t, 4)} armL={t > 15 ? 150 : 20} armR={t > 15 ? 150 : 20} id="cam12" />
            </Pos>
          </>
        )}
      </Cam>
      <NameTag
        key={i}
        at={i * 6 + 0.3}
        name={['Andrés, 34 años', 'Doña Marta, 60 años', 'Camila, 20 años'][i]}
        note={['Viajero', 'Abuela estudiante', '¡Nueva empleada!'][i]}
      />
      <CornerTag text="Dramatización" />
      <Swipe at={5.8} />
      <Swipe at={11.8} dir={-1} />
      {i === 2 && <Confetti at={14.6} count={150} dur={3} />}
      <Sfx name="whoosh" at={0} volume={0.5} />
      <Sfx name="whoosh" at={5.8} />
      <Sfx name="whoosh" at={11.8} />
      <Sfx name="applause" at={4.3} volume={0.35} />
      <Sfx name="applause" at={10.0} volume={0.35} />
      <Sfx name="fanfare" at={14.6} volume={0.5} />
      <Sfx name="applause" at={14.7} volume={0.6} />
    </Scene>
  );
};

/** Letrero de nombre tipo comercial de television. */
const NameTag: React.FC<{at: number; name: string; note: string}> = ({at, name, note}) => {
  const t = useT();
  const x = tw(t, [at, at + 0.3], [-1000, 0]);
  return (
    <div style={{position: 'absolute', left: 1110, top: 740, transform: `translateX(${-x}px)`, opacity: t < at ? 0 : 1}}>
      <div style={{background: C.green, border: `8px solid ${C.outline}`, borderRadius: '24px 24px 0 0', padding: '12px 34px 2px', fontFamily: TITLE, fontSize: 60, color: '#fff', WebkitTextStroke: `3px ${C.outline}`, paintOrder: 'stroke fill'}}>{name}</div>
      <div style={{background: C.yellow, border: `8px solid ${C.outline}`, borderTop: 'none', borderRadius: '0 0 24px 24px', padding: '6px 34px', fontFamily: BODY, fontWeight: 800, fontSize: 40, color: C.outline}}>{note}</div>
    </div>
  );
};
