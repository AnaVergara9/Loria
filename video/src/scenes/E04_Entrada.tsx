import React from 'react';
import {Ono} from '../components/Bubble';
import {Loria} from '../characters/Loria';
import {blinkAt, Cam, Confetti, Pos, Scene, Sfx, talkAmount, tw, usePop, useT} from '../components/core';
import {Flash} from '../components/effects';
import {C} from '../theme';
import {Counter, Logo, StudioBG, Tagline} from '../components/Studio';

// E04 (0:28-0:36) Explosion de color: estudio de teletienda, Loria entra volando y aterriza en el mostrador.
// "¡No sufras mas! ¡Llego Loria!" + logo que cae y rebota + lema.
export const E04_Entrada: React.FC = () => {
  const t = useT();
  const LAND = 1.1;
  const flying = t < LAND;
  // vuelo en curva desde arriba a la derecha
  const fx = tw(t, [0, LAND], [2300, 1330]);
  const fy = tw(t, [0, LAND], [-200, 850]);
  const land = usePop(LAND, 6, 300); // aplastamiento al aterrizar
  const squash = flying ? 1 : 1 - Math.sin(land * Math.PI) * 0.12 * (1 - land);
  const flap = flying ? Math.sin(t * 40) * 40 - 20 : t > 1.3 && t < 4 ? Math.sin(t * 14) * 18 - 10 : 0;
  const logo = usePop(4.2, 7, 160);
  const tag = usePop(5.0, 12, 200);
  return (
    <Scene id="E04">
      <Cam zoom={tw(t, [0, 8], [1.0, 1.08])}>
        <StudioBG />
        <Counter x={1330} y={1080} width={760} />
        <div style={{position: 'absolute', left: 0, top: 0, transform: `scale(1, ${squash})`, transformOrigin: `${fx}px ${fy}px`, width: 1920, height: 1080}}>
          <Pos x={fx} y={fy} rot={flying ? -15 : 0}>
            <Loria
              width={560}
              wingR={flap}
              wingL={flap}
              tail={Math.sin(t * 10) * 6}
              beakOpen={talkAmount(t, 'E04', 'LORIA')}
              blink={blinkAt(t)}
              headTilt={t > 1.3 ? Math.sin(t * 5) * 5 : 0}
              lookX={-0.4}
              showShadow={!flying}
            />
          </Pos>
        </div>
        {t > 4.2 && (
          <div style={{position: 'absolute', left: 120, top: tw(logo, [0, 1], [-500, 170], (x) => x), transform: `rotate(${-6 + (1 - logo) * 10}deg)`}}>
            <Logo size={250} />
          </div>
        )}
        {t > 5.0 && (
          <div style={{position: 'absolute', left: 90, top: 520, transform: `scale(${tag})`, transformOrigin: '0 50%'}}>
            <Tagline size={44} />
          </div>
        )}
      </Cam>
      <Flash at={0} dur={0.35} />
      <Confetti at={0.1} count={140} />
      <Confetti at={4.2} count={90} />
      <Sfx name="fanfare" at={0.05} />
      <Sfx name="applause" at={0.3} volume={0.5} />
      <Sfx name="whoosh" at={0.2} />
      <Sfx name="boing" at={LAND} />
      <Sfx name="whoosh" at={4.0} volume={0.5} />
      <Sfx name="boing" at={4.45} />
      <Sfx name="pop" at={5.0} />
      <Sfx name="applause" at={5.2} volume={0.4} />
      <Ono at={0.15} text="¡TA-DÁ!" x={460} y={760} size={110} burst={C.red} dur={1.0} rot={-8} />
      <Ono at={LAND} text="¡BOING!" x={1700} y={760} size={90} burst={C.green} dur={0.7} rot={8} />
      <Ono at={4.45} text="¡PLOP!" x={900} y={420} size={90} burst={C.blue} dur={0.6} rot={-4} />
    </Scene>
  );
};
