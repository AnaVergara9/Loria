import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Loria} from '../characters/Loria';

// Escena de prueba: Loria original (izquierda) vs. Loria titere animada (derecha).
export const LoriaTest: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const talk = Math.max(0, Math.sin(f * 0.9)) * (f > 20 && f < 70 ? 1 : 0);
  const blink = f % 50 > 46 ? 1 : 0;
  const flap = f > 75 && f < 115 ? Math.sin(f * 0.8) * 25 - 10 : 0;
  const hop = f > 75 && f < 115 ? -Math.abs(Math.sin(f * 0.4)) * 40 : 0;
  const glasses = spring({frame: f - 120, fps, config: {damping: 12}});
  return (
    <AbsoluteFill style={{background: '#FFF6E5', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-around'}}>
      <Img src={staticFile('loria-original.jpg')} style={{height: 900}} />
      <div style={{transform: `translateY(${hop}px)`}}>
        <Loria
          width={672}
          beakOpen={talk}
          blink={blink}
          wingR={flap}
          wingL={flap * -0.4}
          headTilt={interpolate(f, [0, 20, 40], [0, -4, 0], {extrapolateRight: 'clamp'})}
          glasses={f >= 120}
          glassesDrop={f >= 120 ? 1 - glasses : 0}
          tail={Math.sin(f * 0.2) * 3}
        />
      </div>
    </AbsoluteFill>
  );
};
