import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Loria} from '../characters/Loria';
import {CAMILA, CAMILA_PJ, Person} from '../characters/Person';
import {blinkAt, Cam, Pos, Scene, Sfx, SlamText, Sparkle, talkAmount, tw, usePop, useT} from '../components/core';
import {Phone} from '../components/Phone';
import {Bed, BedroomBG, BusBG, KitchenBG, SoundWaves} from '../components/Sets';
import {StudioBG} from '../components/Studio';
import {C} from '../theme';

// E08 (1:10-1:38) Notas de voz.
// A: Loria se pone audifonos. B: tres cortes rapidos (bus, cocina, cama).
// C: cocina "I have tree brothers" -> aparece un arbol (pronunciacion). D: cama "Yesterday I eat pizza" -> "¡Pizza! ¡Pizza!" -> gafas.
// E: "Habla donde quieras. Loria te escucha."
const B = 2.8;
const CUT = 1.13;
const C0 = 6.2;
const TREE = 9.0;
const D0 = 14.4;
const PARROT = 17.2;
const GL = 18.8;
const E0 = 22.5;

// pose de "grabando nota de voz": celular cerca de la boca
const REC = {armR: 20, foreR: -165, phone: true};

export const E08_NotasVoz: React.FC = () => {
  const t = useT();
  return (
    <Scene id="E08">
      {t < B && <PartA t={t} />}
      {t >= B && t < C0 && <PartB t={t} />}
      {t >= C0 && t < D0 && <PartC t={t} />}
      {t >= D0 && t < E0 && <PartD t={t} />}
      {t >= E0 && <PartE t={t} />}
      <Sfx name="pop" at={0.3} />
      <Sfx name="whoosh" at={B - 0.1} />
      <Sfx name="stamp" at={B + 0.05} volume={0.4} />
      <Sfx name="stamp" at={B + CUT + 0.05} volume={0.4} />
      <Sfx name="stamp" at={B + 2 * CUT + 0.05} volume={0.4} />
      <Sfx name="whoosh" at={C0 - 0.1} />
      <Sfx name="boing" at={TREE} />
      <Sfx name="pop" at={9.6} />
      <Sfx name="pop" at={10.3} />
      <Sfx name="ding" at={10.35} volume={0.5} />
      <Sfx name="whoosh" at={D0 - 0.1} />
      <Sfx name="boing" at={PARROT} volume={0.5} />
      <Sfx name="scratch" at={GL - 0.2} volume={0.6} />
      <Sfx name="sparkle" at={GL + 0.2} />
      <Sfx name="ding" at={GL + 0.3} />
      <Sfx name="pop" at={19.3} />
      <Sfx name="whoosh" at={E0 - 0.1} />
      <Sfx name="stamp" at={E0 + 0.2} volume={0.5} />
      <Sfx name="stamp" at={E0 + 1.0} volume={0.5} />
      <Sfx name="applause" at={E0 + 1.2} volume={0.35} />
    </Scene>
  );
};

const PartA: React.FC<{t: number}> = ({t}) => {
  const hp = usePop(0.3, 8, 260);
  return (
    <AbsoluteFill>
      <StudioBG />
      <Cam zoom={tw(t, [0, 2.8], [1.15, 1.25])} origin="50% 40%">
        <Pos x={960} y={1150}>
          <Loria width={640} headphones={t > 0.3} beakOpen={talkAmount(t, 'E08', 'LORIA')} blink={blinkAt(t)} wingR={-30 + Math.sin(t * 8) * 10} wingL={-30} headTilt={Math.sin(t * 4) * 5} />
        </Pos>
      </Cam>
      {t > 0.3 && t < 0.6 && <AbsoluteFill style={{transform: `scale(${2 - hp})`, opacity: 1 - hp}} />}
    </AbsoluteFill>
  );
};

const PartB: React.FC<{t: number}> = ({t}) => {
  const i = Math.min(2, Math.floor((t - B) / CUT));
  const k = t - B - i * CUT;
  const labels = ['EN EL BUS', 'EN LA COCINA', '¡EN PIJAMA!'];
  return (
    <AbsoluteFill>
      <Cam zoom={1.05 + k * 0.1}>
        {i === 0 && <BusBG />}
        {i === 1 && <KitchenBG />}
        {i === 2 && <BedroomBG />}
        <Pos x={760} y={i === 2 ? 1120 : 1180}>
          <Person {...(i === 2 ? CAMILA_PJ : CAMILA)} width={420} {...REC} talk={Math.abs(Math.sin(k * 14)) * 0.7} lookX={0.4} id={`camb${i}`} />
        </Pos>
        {i === 2 && <Bed />}
        <SoundWaves x1={980} y1={400} x2={1900} y2={300} />
      </Cam>
      <SlamText at={B + i * CUT + 0.05} size={130} color={C.yellow} x={380} y={-300} rot={i % 2 ? 4 : -4}>
        {labels[i]}
      </SlamText>
    </AbsoluteFill>
  );
};

const PartC: React.FC<{t: number}> = ({t}) => {
  const tree = usePop(TREE, 8, 200);
  return (
    <AbsoluteFill>
      {/* izquierda: Camila en la cocina */}
      <div style={{position: 'absolute', left: 0, top: 0, width: 960, height: 1080, overflow: 'hidden'}}>
        <div style={{position: 'absolute', left: -300, top: 0, width: 1920, height: 1080}}>
          <KitchenBG />
          <Pos x={1040} y={1170}>
            <Person {...CAMILA} width={420} {...REC} talk={talkAmount(t, 'E08', 'CAMILA')} mood={t > TREE + 0.3 ? 'shock' : 'neutral'} lookX={t > TREE + 0.3 ? -0.9 : 0.3} blink={blinkAt(t, 3)} id="camc" />
          </Pos>
          {t >= TREE && (
            <div style={{position: 'absolute', left: 300, top: 250, transform: `scale(${tree * 0.85})`, transformOrigin: '50% 100%'}}>
              <TreeWithBrothers />
            </div>
          )}
        </div>
      </div>
      {/* derecha: Loria con audifonos escuchando */}
      <div style={{position: 'absolute', left: 960, top: 0, width: 960, height: 1080, overflow: 'hidden', borderLeft: `14px solid ${C.outline}`}}>
        <div style={{position: 'absolute', left: -480, top: 0, width: 1920, height: 1080}}>
          <StudioBG />
          <Pos x={960} y={1120}>
            <Loria width={560} headphones beakOpen={talkAmount(t, 'E08', 'LORIA')} blink={blinkAt(t)} lookX={-0.6} headTilt={t < 9 ? Math.sin(t * 6) * 4 : 6} wingR={t > 10.6 ? -40 : 0} />
          </Pos>
        </div>
      </div>
      <SoundWaves x1={560} y1={420} x2={1300} y2={380} on={t > 7 && t < 9.2} />
      {/* el chat con la correccion de pronunciacion */}
      {t >= 9.6 && (
        <div style={{position: 'absolute', left: 770, top: 60, transform: `translateY(${tw(t, [9.5, 9.8], [-1200, 0])}px)`}}>
          <Phone
            width={400}
            rotY={0}
            rotX={0}
            msgs={[
              {at: 9.6, from: 'me', voice: 3},
              {at: 10.3, from: 'loria', label: '🔊 PRONUNCIACIÓN', fix: 'three (tres) ≠ tree (árbol)', why: 'Pon la lengua entre los dientes: "th".'},
            ]}
          />
        </div>
      )}
    </AbsoluteFill>
  );
};

/** Arbol con tres hermanitos colgando (el chiste de "tree brothers"). */
const TreeWithBrothers: React.FC = () => (
  <div style={{position: 'relative', width: 520, height: 760}}>
    <svg width={520} height={760} viewBox="0 0 520 760" style={{position: 'absolute'}}>
      <path d="M220 760 L240 420 L170 330 M240 420 L330 320 L300 760 Z" fill="#8A5F38" stroke={C.outline} strokeWidth={10} strokeLinejoin="round" />
      <path d="M200 760 L230 420 L310 420 L320 760 Z" fill="#8A5F38" stroke={C.outline} strokeWidth={10} />
      {[[130, 240, 130], [260, 170, 160], [390, 250, 130], [190, 330, 110], [330, 330, 110]].map(([x, y, r], i) => (
        <circle key={i} cx={x} cy={y} r={r} fill={i % 2 ? C.green : '#8DC23F'} stroke={C.outline} strokeWidth={10} />
      ))}
      <path d="M80 330 L80 390 M260 400 L260 450 M440 330 L440 390" stroke={C.outline} strokeWidth={6} />
    </svg>
    {[[80, 385], [260, 450], [440, 385]].map(([x, y], i) => (
      <div key={i} style={{position: 'absolute', left: x - 45, top: y, transform: `rotate(${(i - 1) * 8}deg)`}}>
        <Person hair="kid" hairColor={['#3B2216', '#C98E3A', '#1E1A1A'][i]} top={[C.orange, C.blue, C.red][i]} width={90} mood="happy" armL={160} armR={160} id={`bro${i}`} />
      </div>
    ))}
  </div>
);

const PartD: React.FC<{t: number}> = ({t}) => {
  const parrot = t >= PARROT && t < GL;
  if (t < PARROT) {
    return (
      <AbsoluteFill>
        <Cam zoom={tw(t, [D0, PARROT], [1.0, 1.15])} origin="45% 45%">
          <BedroomBG />
          <Pos x={900} y={1120}>
            <Person {...CAMILA_PJ} width={440} {...REC} talk={talkAmount(t, 'E08', 'CAMILA')} blink={t > 15 ? 0.7 : 0} mood="neutral" headTilt={-8} id="camd" />
          </Pos>
          <Bed />
          <SoundWaves x1={1100} y1={560} x2={1900} y2={420} on={t > 15 && t < 17.1} color="#FFF3B0" />
          <div style={{position: 'absolute', left: 1300, top: 520, fontSize: 80, color: '#fff', opacity: 0.8}}>z z z</div>
        </Cam>
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill>
      <StudioBG />
      <Cam zoom={parrot ? 1.2 : 1.05} origin="50% 45%">
        <Pos x={parrot ? 960 : 1300} y={1150 + (parrot ? -Math.abs(Math.sin(t * 11)) * 60 : 0)}>
          <Loria
            width={600}
            headphones
            glasses={t >= GL}
            glassesDrop={t < GL ? 1 : tw(t, [GL, GL + 0.25], [1, 0])}
            beakOpen={talkAmount(t, 'E08', 'LORIA')}
            blink={blinkAt(t)}
            wingR={parrot ? Math.sin(t * 22) * 35 - 15 : 0}
            wingL={parrot ? Math.sin(t * 22) * 35 - 15 : 0}
            headTilt={parrot ? Math.sin(t * 16) * 10 : 4}
            lookX={parrot ? 0 : -0.5}
          />
        </Pos>
        {parrot && <PizzaRain t={t - PARROT} />}
      </Cam>
      <Sparkle at={GL + 0.2} x={1400} y={400} size={150} />
      {t >= 19.3 && (
        <div style={{position: 'absolute', left: 120, top: 40, transform: `translateX(${tw(t, [19.2, 19.5], [-900, 0])}px)`}}>
          <Phone
            width={450}
            rotY={12}
            msgs={[
              {at: 19.3, from: 'me', voice: 2},
              {at: 19.9, from: 'loria', fix: 'Yesterday I ate pizza', why: '"eat" es irregular: su pasado es "ate".'},
            ]}
          />
        </div>
      )}
    </AbsoluteFill>
  );
};

const PizzaRain: React.FC<{t: number}> = ({t}) => (
  <AbsoluteFill>
    {new Array(14).fill(0).map((_, i) => (
      <div key={i} style={{position: 'absolute', left: (i * 151) % 1900, top: -150 + ((t * 700 + i * 260) % 1300), fontSize: 90, transform: `rotate(${t * 200 + i * 40}deg)`}}>
        🍕
      </div>
    ))}
  </AbsoluteFill>
);

const PartE: React.FC<{t: number}> = ({t}) => {
  const k = t - E0;
  const spots = [
    {x: 300, y: 250, icon: '🚌'},
    {x: 300, y: 760, icon: '🍳'},
    {x: 1620, y: 250, icon: '🛏️'},
    {x: 1620, y: 760, icon: '🚶'},
  ];
  return (
    <AbsoluteFill>
      <StudioBG />
      <Cam zoom={1 + k * 0.02}>
        {spots.map((sp, i) => {
          const p = Math.min(1, Math.max(0, (k - i * 0.15) / 0.25));
          return (
            <React.Fragment key={i}>
              <SoundWaves x1={sp.x} y1={sp.y} x2={960} y2={560} />
              <div style={{position: 'absolute', left: sp.x - 110, top: sp.y - 110, width: 220, height: 220, borderRadius: '50%', background: C.cream, border: `9px solid ${C.outline}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 110, transform: `scale(${p})`}}>
                {sp.icon}
              </div>
            </React.Fragment>
          );
        })}
        <Pos x={960} y={1120}>
          <Loria width={540} headphones blink={blinkAt(t)} headTilt={Math.sin(t * 5) * 6} wingR={-20 + Math.sin(t * 8) * 10} wingL={-20 + Math.sin(t * 8 + 1) * 10} />
        </Pos>
      </Cam>
      <SlamText at={E0 + 0.2} size={110} color={C.yellow} y={-380}>
        Habla donde quieras.
      </SlamText>
      <SlamText at={E0 + 1.0} size={110} color="#8DD14F" y={360} rot={3}>
        Loria te escucha.
      </SlamText>
    </AbsoluteFill>
  );
};
