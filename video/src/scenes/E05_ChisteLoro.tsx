import React from 'react';
import {Loria} from '../characters/Loria';
import {CAMILA, Person} from '../characters/Person';
import {blinkAt, Cam, Pos, Scene, Sfx, SlamText, Sparkle, talkAmount, tw, useT} from '../components/core';
import {Phone} from '../components/Phone';
import {Counter, StudioBG} from '../components/Studio';
import {C} from '../theme';

// E05 (0:36-0:52) El chiste del loro (vez 1 de 3):
// Camila dice "I have 20 years..." -> Loria lo repite como loro -> rayon de disco y silencio ->
// Loria se pone las gafas y corrige. En pantalla aparece la correccion en el chat.
const STOP = 5.4; // rayon de disco
const GLASSES = 7.2; // se pone las gafas
const SLAM = 13.6;

export const E05_ChisteLoro: React.FC = () => {
  const t = useT();
  const parrot = t >= 2.8 && t < STOP;
  const lt = t >= STOP && t < GLASSES ? STOP : t; // Loria se congela durante el silencio
  const flap = parrot ? Math.sin(t * 22) * 35 - 15 : 0;
  const hop = parrot ? -Math.abs(Math.sin(t * 11)) * 50 : 0;
  // planos de camara
  const stare = t >= STOP && t < GLASSES;
  const explain = t >= GLASSES && t < SLAM;
  const cam = stare
    ? {zoom: tw(t, [STOP, STOP + 0.15], [1, 2.4]) + (t - STOP) * 0.05, origin: '27% 30%'}
    : explain
      ? {zoom: tw(t, [GLASSES, GLASSES + 0.2], [1.5, 1.3]), origin: '72% 40%'}
      : t >= SLAM
        ? {zoom: tw(t, [SLAM, SLAM + 0.4], [1.3, 1]), origin: '50% 50%'}
        : {zoom: parrot ? 1.12 : 1, origin: '60% 50%'};
  const glassesDrop = t < GLASSES ? 1 : tw(t, [GLASSES, GLASSES + 0.3], [1, 0]);
  const camX = tw(t, [0, 0.8], [-700, 560]);
  return (
    <Scene id="E05">
      <Cam zoom={cam.zoom} origin={cam.origin}>
        <StudioBG />
        <Counter x={1330} y={1080} width={760} />
        <Pos x={1330} y={850 + hop}>
          <Loria
            width={560}
            wingR={flap}
            wingL={flap}
            tail={parrot ? Math.sin(t * 20) * 8 : 0}
            beakOpen={talkAmount(lt, 'E05', 'LORIA')}
            blink={stare ? 0 : blinkAt(t)}
            headTilt={parrot ? Math.sin(t * 16) * 10 : explain ? 4 : 0}
            lookX={-0.5}
            glasses={t >= GLASSES}
            glassesDrop={glassesDrop}
          />
        </Pos>
        <Pos x={camX} y={1110}>
          <Person
            {...CAMILA}
            width={400}
            mood={stare ? 'skeptic' : t > 9 ? 'happy' : 'shy'}
            talk={talkAmount(t, 'E05', 'CAMILA')}
            lookX={stare ? 0 : 0.7}
            blink={stare ? 0 : blinkAt(t, 3)}
            armL={stare ? 30 : 10}
            armR={stare ? 30 : 10}
            foreL={stare ? -110 : 0}
            foreR={stare ? -110 : 0}
            id="cam-e05"
          />
        </Pos>
      </Cam>
      {/* el chat con la correccion */}
      {explain && (
        <div style={{position: 'absolute', left: 70, top: 30, transform: `translateX(${tw(t, [8.2, 8.6], [-800, 0])}px)`}}>
          <Phone
            width={470}
            rotY={12}
            msgs={[
              {at: 8.3, from: 'me', text: 'I have 20 years', wrong: true, strikeAt: 9.0},
              {at: 9.4, from: 'loria', fix: 'I am 20 years old', why: 'La edad va con "to be", no con "tener".'},
            ]}
          />
        </div>
      )}
      <Sparkle at={GLASSES + 0.3} x={1440} y={420} size={160} />
      <SlamText at={SLAM} size={110} color={C.yellow}>
        Loria no solo repite.
        <br />
        <span style={{color: '#8DD14F'}}>¡Te corrige!</span>
      </SlamText>
      <Sfx name="whoosh" at={0.1} volume={0.5} />
      <Sfx name="scratch" at={STOP} />
      <Sfx name="crickets" at={STOP + 0.4} volume={0.5} />
      <Sfx name="whoosh" at={GLASSES} volume={0.5} />
      <Sfx name="sparkle" at={GLASSES + 0.25} />
      <Sfx name="ding" at={GLASSES + 0.35} />
      <Sfx name="pop" at={8.3} volume={0.5} />
      <Sfx name="pop" at={9.4} volume={0.5} />
      <Sfx name="ding" at={9.45} volume={0.5} />
      <Sfx name="stamp" at={SLAM} volume={0.6} />
      <Sfx name="applause" at={SLAM + 0.2} volume={0.4} />
    </Scene>
  );
};
