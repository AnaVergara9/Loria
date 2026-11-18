import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Loria} from '../characters/Loria';
import {blinkAt, Pos, Scene, Sfx, talkAmount, tw, usePop, useT} from '../components/core';
import {StudioBG} from '../components/Studio';
import {C} from '../theme';

// E00 (0:00-0:03) Loria salta frente a la camara: "¿Hablas ingles? ¿Si? ...A ver." y apaga la tele con el control.
export const E00_Gancho: React.FC = () => {
  const t = useT();
  const enter = usePop(0, 9, 160);
  const press = t > 2.25 && t < 2.45;
  // la tele "se apaga": se aplasta en una linea y desaparece
  const offY = tw(t, [2.45, 2.7], [1, 0.012]);
  const offX = tw(t, [2.7, 2.9], [1, 0]);
  return (
    <Scene id="E00" bg="#000">
      <AbsoluteFill style={{transform: `scale(${offX}, ${offY})`, background: '#000'}}>
        <StudioBG />
        <Pos x={880} y={1560 + (1 - enter) * 1000} scale={1}>
          <Loria
            width={1100}
            beakOpen={talkAmount(t, 'E00', 'LORIA')}
            blink={blinkAt(t)}
            headTilt={tw(t, [0.3, 1.2, 2.0], [0, 8, -4])}
            lookX={0.3}
            wingR={tw(t, [1.6, 2.0], [0, -55])}
            wingL={Math.sin(t * 8) * 6}
          />
        </Pos>
        {/* control remoto */}
        <div
          style={{
            position: 'absolute',
            left: 1480,
            top: tw(t, [1.7, 2.0], [1200, 560]),
            transform: `rotate(-18deg) scale(${press ? 0.94 : 1})`,
          }}
        >
          <svg width={180} height={420} viewBox="0 0 180 420">
            <rect x={10} y={10} width={160} height={400} rx={40} fill="#2B2E3A" stroke={C.outline} strokeWidth={10} />
            <circle cx={90} cy={80} r={34} fill={press ? '#FF8A80' : C.red} stroke={C.outline} strokeWidth={8} />
            {[0, 1, 2].map((r) =>
              [0, 1].map((c) => <rect key={`${r}${c}`} x={38 + c * 60} y={160 + r * 70} width={44} height={44} rx={10} fill="#5A6070" stroke={C.outline} strokeWidth={5} />),
            )}
          </svg>
        </div>
      </AbsoluteFill>
      {t > 2.5 && <div style={{position: 'absolute', left: 0, right: 0, top: 538, height: 4, background: '#fff', opacity: tw(t, [2.7, 2.95], [1, 0]), boxShadow: '0 0 30px #fff'}} />}
      <Sfx name="boing" at={0.05} />
      <Sfx name="whoosh" at={1.65} volume={0.5} />
      <Sfx name="click" at={2.25} />
      <Sfx name="static" at={2.45} volume={0.5} />
    </Scene>
  );
};
