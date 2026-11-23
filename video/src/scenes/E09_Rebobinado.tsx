import React from 'react';
import {Ono} from '../components/Bubble';
import {AbsoluteFill, Freeze, interpolate} from 'remotion';
import {Loria} from '../characters/Loria';
import {blinkAt, Cam, Pos, Scene, Sfx, talkAmount, tw, usePop, useT} from '../components/core';
import {Rewind} from '../components/effects';
import {StudioBG} from '../components/Studio';
import {C} from '../theme';
import {E08_NotasVoz} from './E08_NotasVoz';
import {E06_Escribele} from './E06_Escribele';

// E09 (1:38-1:42) El video se rebobina rapidisimo (escenas anteriores al reves) y frena en seco.
// Loria: "Un momento... ¿y para los mas pequenos?"
const STOP = 1.0;

export const E09_Rebobinado: React.FC = () => {
  const t = useT();
  const q = usePop(STOP + 0.9, 8, 220);
  return (
    <Scene id="E09" bg="#000">
      {t < STOP * 0.6 && (
        <Freeze frame={Math.round(interpolate(t, [0, STOP * 0.6], [830, 0]))}>
          <E08_NotasVoz />
        </Freeze>
      )}
      {t >= STOP * 0.6 && t < STOP && (
        <Freeze frame={Math.round(interpolate(t, [STOP * 0.6, STOP], [400, 0]))}>
          <E06_Escribele />
        </Freeze>
      )}
      <Rewind from={0} to={STOP} />
      {t >= STOP && (
        <AbsoluteFill>
          <StudioBG />
          <Cam zoom={tw(t, [STOP, STOP + 0.12, 4], [1.25, 1.1, 1.18])} origin="50% 45%">
            <Pos x={960} y={1150}>
              <Loria
                width={620}
                beakOpen={talkAmount(t, 'E09', 'LORIA')}
                blink={blinkAt(t)}
                headTilt={tw(t, [STOP, 2.2, 3.0], [0, 14, -10])}
                lookX={Math.sin(t * 2) * 0.8}
                lookY={-0.3}
                wingR={-60}
                wingL={10}
              />
            </Pos>
          </Cam>
          {t > STOP + 0.9 && (
            <div style={{position: 'absolute', left: 430, top: 150, transform: `scale(${q}) rotate(12deg)`, fontFamily: 'Arial Black', fontSize: 220, color: C.yellow, WebkitTextStroke: `10px ${C.outline}`}}>?</div>
          )}
        </AbsoluteFill>
      )}
      <Sfx name="rewind" at={0} />
      <Sfx name="pop" at={STOP} />
      <Sfx name="pop" at={STOP + 0.9} volume={0.6} />
      <Ono at={STOP} text="¡CLAC!" x={1560} y={850} size={100} burst={C.yellow} dur={0.6} rot={-6} />
    </Scene>
  );
};
