import React from 'react';
import {AbsoluteFill} from 'remotion';
import {CAMILA, Person} from '../characters/Person';
import {blinkAt, Cam, Pos, Scene, Sfx, SlamText, tw, useT} from '../components/core';
import {OldTV, StaticBurst} from '../components/effects';
import {HideTable} from '../components/Sets';
import {C} from '../theme';

// E03 (0:20-0:28) Camila escondida debajo de la mesa. La voz de Loria (sin verse) pregunta.
// Las preguntas entran de golpe; la ultima crece hasta llenar la pantalla. Termina en estatica.
export const E03_Pregunta: React.FC = () => {
  const t = useT();
  const zoom = t < 0.3 ? 1 : tw(t, [0.3, 0.45], [1, 1.45]) + (t - 0.45) * 0.03;
  const tremble = Math.sin(t * 60) * 2;
  const big = tw(t, [4.8, 6.8], [1, 5.5]);
  return (
    <Scene id="E03" subs={false}>
      <OldTV>
        <Cam zoom={zoom} origin="50% 52%">
          <AbsoluteFill style={{background: 'linear-gradient(180deg, #CFC6B8, #A9A091)'}} />
          <AbsoluteFill style={{top: 900, background: '#8E8576'}} />
          <Pos x={960 + tremble} y={1780}>
            <Person {...CAMILA} width={560} mood="shy" sweat lookX={Math.sin(t * 2) * 0.8} blink={blinkAt(t, 2)} armL={25} foreL={-60} armR={25} foreR={-60} id="cam-hide" />
          </Pos>
          <HideTable />
        </Cam>
      </OldTV>
      <SlamText at={0.4} out={2.45} size={100} color={C.cream} y={-300}>
        ¿Te da pena hablar
        <br />
        en <span style={{color: C.yellow}}>inglés</span>?
      </SlamText>
      <SlamText at={2.6} out={4.65} size={100} color={C.cream} y={-300} rot={3}>
        ¿Te quedas callada
        <br />
        en <span style={{color: C.yellow}}>francés</span>?
      </SlamText>
      {t >= 4.8 && (
        <AbsoluteFill style={{transform: `scale(${big})`}}>
          <SlamText at={4.8} size={150} color={C.yellow} rot={-4}>
            ¿PENA DE
            <br />
            HABLAR?
          </SlamText>
        </AbsoluteFill>
      )}
      <StaticBurst from={6.85} to={8.01} />
      <Sfx name="whoosh" at={0.28} volume={0.6} />
      <Sfx name="stamp" at={0.42} volume={0.5} />
      <Sfx name="stamp" at={2.62} volume={0.5} />
      <Sfx name="stamp" at={4.82} volume={0.8} />
      <Sfx name="drumroll" at={5.5} volume={0.5} />
      <Sfx name="static" at={6.85} volume={0.6} />
    </Scene>
  );
};
