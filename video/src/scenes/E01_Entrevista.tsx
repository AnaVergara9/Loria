import React from 'react';
import {Ono} from '../components/Bubble';
import {CAMILA, JEFE, Person} from '../characters/Person';
import {blinkAt, Cam, Pos, Scene, Sfx, shake, Stamp, talkAmount, tw, useT} from '../components/core';
import {OldTV, SilentCard} from '../components/effects';
import {Desk, OfficeBG} from '../components/Sets';
import {C} from '../theme';

// E01 (0:03-0:10) Entrevista en blanco y negro: "How old are you?" / "I have 20 years!" -> congelado + ¡ERROR!
export const E01_Entrevista: React.FC = () => {
  const real = useT();
  const FREEZE = 4.3;
  const t = Math.min(real, FREEZE); // despues del congelado nada se mueve
  // camara: plano general -> jefe -> Camila -> congelado
  const shot = real < 1.0 ? 0 : real < 2.3 ? 1 : real < FREEZE ? 2 : 3;
  const cams = [
    {zoom: tw(real, [0, 0.6], [1, 1.06]), origin: '50% 50%'},
    {zoom: tw(real, [1.0, 2.3], [1.9, 2.05]), origin: '28% 30%'},
    {zoom: tw(real, [2.3, FREEZE], [2.0, 2.15]), origin: '74% 30%'},
    {zoom: tw(real, [FREEZE, FREEZE + 0.2, 7], [1.5, 1.25, 1.32]), origin: '55% 40%'},
  ][shot];
  const sh = real > FREEZE && real < FREEZE + 0.5 ? shake(real, 1 - (real - FREEZE) / 0.5) : {x: 0, y: 0};
  return (
    <Scene id="E01">
      <OldTV>
        <Cam zoom={cams.zoom} origin={cams.origin} x={sh.x} y={sh.y}>
          <OfficeBG />
          <Pos x={560} y={1180}>
            <Person {...JEFE} width={400} mood="angry" talk={talkAmount(t, 'E01', 'JEFE')} lookX={0.6} blink={blinkAt(t, 1)} armL={18} armR={18} />
          </Pos>
          <Desk x={180} y={740} w={760} />
          <Pos x={1420} y={1130}>
            <Person
              {...CAMILA}
              width={380}
              mood={t > 2.3 ? 'proud' : 'neutral'}
              talk={talkAmount(t, 'E01', 'CAMILA')}
              lookX={-0.6}
              blink={blinkAt(t, 2)}
              armR={t > 2.4 ? 60 : 10}
              foreR={t > 2.4 ? -70 : 0}
              headTilt={t > 2.4 ? 6 : 0}
            />
          </Pos>
        </Cam>
      </OldTV>
      <Stamp at={FREEZE + 0.1} text="¡ERROR!" size={190} />
      <Sfx name="pop" at={1.0} volume={0.4} />
      <Sfx name="pop" at={2.3} volume={0.4} />
      <Sfx name="buzzer" at={FREEZE} />
      <Sfx name="stamp" at={FREEZE + 0.12} />
      <SilentCard from={0} to={1.0} text={<>Lunes, 9:00 a.m.<br />La gran entrevista…</>} />
      <Ono at={FREEZE} text="¡BZZZT!" x={1500} y={860} size={110} dur={1.2} rot={-6} />
    </Scene>
  );
};
