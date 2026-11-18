import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Loria} from '../characters/Loria';
import {CAMILA_SUIT, Person} from '../characters/Person';
import {blinkAt, Cam, Confetti, Pos, Scene, Sfx, Sparkle, talkAmount, tw, usePop, useT} from '../components/core';
import {QRBox} from '../components/EndCard';
import {Counter, Logo, StudioBG, Tagline} from '../components/Studio';

// E14 (2:48-3:00) Ultimo chiste (vez 3 de 3): Loria repite "I am 20 years old!" emocionada,
// Camila: "Loria... tu no tienes 20 anos." Gafas + ding: "Cierto. Tengo dos semanas. Te espero en Telegram."
// Cierre: logo, lema, QR y @loriaabot.
const STOP = 3.0;
const GL = 5.6;
const CARD = 9.6;

export const E14_Final: React.FC = () => {
  const t = useT();
  const parrot = t < STOP;
  const card = usePop(CARD, 12, 140);
  const flap = parrot ? Math.sin(t * 22) * 35 - 15 : 0;
  const zoom = t < STOP ? 1.05 : t < GL ? tw(t, [STOP, STOP + 0.15], [1.05, 1.5]) : t < CARD ? tw(t, [GL, GL + 0.2], [1.5, 1.3]) : 1.3;
  const origin = t < STOP ? '50% 50%' : t < GL ? '30% 35%' : '70% 40%';
  return (
    <Scene id="E14">
      <Cam zoom={zoom} origin={origin}>
        <StudioBG />
        <Counter x={1330} y={1080} width={760} />
        <Pos x={1330} y={850 - (parrot ? Math.abs(Math.sin(t * 11)) * 50 : 0)}>
          <Loria
            width={560}
            wingR={flap}
            wingL={flap}
            beakOpen={talkAmount(t, 'E14', 'LORIA')}
            blink={blinkAt(t)}
            headTilt={parrot ? Math.sin(t * 16) * 10 : t > GL ? 6 : 0}
            lookX={t > GL ? 0 : -0.5}
            glasses={t >= GL}
            glassesDrop={t < GL ? 1 : tw(t, [GL, GL + 0.25], [1, 0])}
          />
        </Pos>
        <Pos x={560} y={1120}>
          <Person {...CAMILA_SUIT} width={400} mood={t > STOP ? 'skeptic' : 'happy'} talk={talkAmount(t, 'E14', 'CAMILA')} blink={blinkAt(t, 2)} lookX={0.7} armL={t > STOP ? 30 : 10} foreL={t > STOP ? -100 : 0} id="cam14" />
        </Pos>
      </Cam>
      <Sparkle at={GL + 0.2} x={1420} y={330} size={150} />
      {/* tarjeta final */}
      {t >= CARD && (
        <AbsoluteFill style={{clipPath: `circle(${card * 120}% at 70% 40%)`}}>
          <StudioBG floor={false} />
          <AbsoluteFill style={{flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 110}}>
            <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 30}}>
              <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
                <Loria width={300} glasses blink={blinkAt(t)} wingR={-40 + Math.sin(t * 8) * 10} showShadow={false} id="endloria" />
                <Logo size={230} />
              </div>
              <Tagline size={52} />
            </div>
            <QRBox size={330} />
          </AbsoluteFill>
          <Confetti at={CARD} count={120} />
        </AbsoluteFill>
      )}
      <Sfx name="boing" at={0.1} volume={0.5} />
      <Sfx name="scratch" at={STOP} />
      <Sfx name="crickets" at={STOP + 0.3} volume={0.4} />
      <Sfx name="whoosh" at={GL} volume={0.5} />
      <Sfx name="sparkle" at={GL + 0.2} />
      <Sfx name="ding" at={GL + 0.3} />
      <Sfx name="whoosh" at={CARD - 0.1} />
      <Sfx name="fanfare" at={CARD} />
      <Sfx name="applause" at={CARD + 0.2} volume={0.6} />
    </Scene>
  );
};
