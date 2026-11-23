import React from 'react';
import {Ono} from '../components/Bubble';
import {AbsoluteFill} from 'remotion';
import {CAMILA, MESERO, Person} from '../characters/Person';
import {blinkAt, Cam, Pos, Scene, Sfx, SlamText, talkAmount, tw, usePop, useT} from '../components/core';
import {OldTV, StaticBurst} from '../components/effects';
import {AirportBG, CafeBG, CafeTable, CallTile, CallUI} from '../components/Sets';
import {C} from '../theme';

// E02 (0:10-0:20) Tres fallos rapidos (2.5 s c/u) y luego pantalla partida en tres con X rojas.
// Cada mini-escena recibe "t" (su propio tiempo) para poder congelarla en la pantalla partida.

const CUT1 = 2.5;
const CUT2 = 5.0;
const SPLIT = 7.5;

const Cafe: React.FC<{t: number; g: number}> = ({t, g}) => (
  <AbsoluteFill>
    <Cam zoom={1 + t * 0.03}>
      <CafeBG />
      <Pos x={620} y={1180}>
        <Person {...CAMILA} width={400} mood="shy" talk={talkAmount(g, 'E02', 'CAMILA')} lookX={0.6} blink={blinkAt(t, 3)} armR={40} foreR={-50} id="cam-cafe" />
      </Pos>
      <Pos x={1340} y={1180}>
        <Person {...MESERO} width={420} mood={t > 1.4 ? 'skeptic' : 'neutral'} lookX={-0.7} armL={20} armR={70} foreR={-90} id="mes-cafe" />
      </Pos>
      <CafeTable x={980} y={720} />
      {t > 1.6 && <Bubble x={1520} y={180} text="?" at={1.6} t={t} />}
    </Cam>
  </AbsoluteFill>
);

const Airport: React.FC<{t: number; g: number}> = ({t, g}) => {
  const turn = tw(t, [1.0, 1.25], [0, 1]);
  const crowd = [
    {x: 230, top: '#5B8DB8', hair: 'long' as const, hc: '#7A4A2A', flip: false},
    {x: 470, top: '#9C6ADE', hair: 'curly' as const, hc: '#1E1A1A', flip: false},
    {x: 1450, top: '#D8443A', hair: 'short' as const, hc: '#C98E3A', flip: true},
    {x: 1700, top: '#3FA37A', hair: 'bald' as const, hc: '#555', flip: true},
  ];
  return (
    <AbsoluteFill>
      <Cam zoom={1.05 + t * 0.03}>
        <AirportBG />
        {crowd.map((p, i) => (
          <Pos key={i} x={p.x} y={1120}>
            <Person top={p.top} hair={p.hair} hairColor={p.hc} width={300} mood={turn > 0.5 ? 'shock' : 'neutral'} lookX={(p.x < 960 ? 1 : -1) * turn} headTilt={(p.x < 960 ? 6 : -6) * turn} id={`crowd${i}`} />
          </Pos>
        ))}
        <Pos x={960} y={1160}>
          <Person {...CAMILA} width={400} mood="shy" talk={talkAmount(g, 'E02', 'CAMILA')} blink={blinkAt(t, 1)} armL={60} foreL={-40} sweat={t > 1.3} id="cam-air" />
        </Pos>
        {t > 1.3 && <Bubble x={300} y={240} text="!?" at={1.3} t={t} />}
        {t > 1.4 && <Bubble x={1620} y={240} text="!?" at={1.4} t={t} />}
      </Cam>
    </AbsoluteFill>
  );
};

const Call: React.FC<{t: number; g: number}> = ({t, g}) => {
  const muted = t > 1.5;
  const camOff = t > 1.9;
  return (
    <AbsoluteFill style={{background: '#0E1014'}}>
      <CallTile x={40} y={90} w={900} h={430} name="Laura (jefa)" bg="#61708C">
        <Pos x={450} y={800}>
          <Person hair="long" hairColor="#2A1A12" top="#3E7FB5" outfit="suit" accent="#fff" width={340} talk={talkAmount(g, 'E02', 'COLEGA')} blink={blinkAt(t, 4)} id="laura" />
        </Pos>
      </CallTile>
      <CallTile x={980} y={90} w={900} h={430} name="Mike" bg="#7A6A8C">
        <Pos x={450} y={800}>
          <Person hair="short" hairColor="#C98E3A" top="#5BA35B" width={340} lookX={-0.5} blink={blinkAt(t, 5)} id="mike" />
        </Pos>
      </CallTile>
      <CallTile x={40} y={545} w={900} h={430} name="Sophie" bg="#8C7A61">
        <Pos x={450} y={800}>
          <Person hair="curly" hairColor="#1E1A1A" skin="#8D5A3B" top="#E07A5F" width={340} blink={blinkAt(t, 6)} id="sophie" />
        </Pos>
      </CallTile>
      <CallTile x={980} y={545} w={900} h={430} name="Camila" bg="#5E7F6A" off={camOff}>
        <Pos x={450} y={800}>
          <Person {...CAMILA} width={340} mood={muted ? 'shock' : 'shy'} sweat blink={blinkAt(t, 7)} id="cam-call" />
        </Pos>
      </CallTile>
      <CallUI muted={muted} camOff={camOff} />
    </AbsoluteFill>
  );
};

/** Globo con signo ("?" o "!?") que aparece rebotando. */
const Bubble: React.FC<{x: number; y: number; text: string; at: number; t: number}> = ({x, y, text, at, t}) => {
  const p = Math.min(1, (t - at) / 0.2);
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        transform: `scale(${0.3 + p * 0.7 + Math.sin((t - at) * 10) * 0.04}) rotate(${-8 + Math.sin(t * 4) * 4}deg)`,
        width: 170,
        height: 170,
        borderRadius: '50%',
        background: '#fff',
        border: `9px solid ${C.outline}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'Arial Black, sans-serif',
        fontSize: 100,
        color: C.outline,
      }}
    >
      {text}
    </div>
  );
};

export const E02_Montaje: React.FC = () => {
  const t = useT();
  return (
    <Scene id="E02">
      <OldTV>
        {t < CUT1 && <Cafe t={t} g={t} />}
        {t >= CUT1 && t < CUT2 && <Airport t={t - CUT1} g={t} />}
        {t >= CUT2 && t < SPLIT && <Call t={t - CUT2} g={t} />}
        {t >= SPLIT && <Split t={t} />}
      </OldTV>
      {t >= SPLIT && <Xs t={t} />}
      <StaticBurst from={CUT1 - 0.05} to={CUT1 + 0.12} />
      <StaticBurst from={CUT2 - 0.05} to={CUT2 + 0.12} />
      <StaticBurst from={SPLIT - 0.05} to={SPLIT + 0.1} />
      <Sfx name="pop" at={1.6} volume={0.5} />
      <Sfx name="whoosh" at={CUT1 - 0.1} volume={0.5} />
      <Sfx name="pop" at={CUT1 + 1.3} volume={0.5} />
      <Sfx name="whoosh" at={CUT2 - 0.1} volume={0.5} />
      <Sfx name="click" at={CUT2 + 1.5} />
      <Sfx name="click" at={CUT2 + 1.9} />
      <Sfx name="whoosh" at={SPLIT - 0.1} volume={0.6} />
      {[0, 1, 2].map((i) => (
        <Sfx key={i} name="buzzer" at={SPLIT + 0.5 + i * 0.5} volume={0.6} />
      ))}
      <SlamText at={SPLIT + 1.8} size={110} color={C.yellow} y={-400}>
        ¿TE SUENA?
      </SlamText>
      <Sfx name="stamp" at={SPLIT + 1.8} volume={0.6} />
      <Ono at={CUT1 + 1.3} text="¿¡EH!?" x={1640} y={820} size={90} burst="#9C6ADE" dur={0.9} rot={6} />
      <Ono at={CUT2 + 1.5} text="¡CLIC!" x={1640} y={980} size={80} burst={C.yellow} dur={0.6} />
    </Scene>
  );
};

/** Pantalla partida en tres columnas (cada una congelada en su peor momento). */
const Split: React.FC<{t: number}> = ({t}) => {
  const panels = [
    {C: Cafe, freeze: 2.3, gt: 2.2, focus: 0.42},
    {C: Airport, freeze: 2.3, gt: CUT1 + 2.2, focus: 0.5},
    {C: Call, freeze: 2.4, gt: CUT2 + 2.3, focus: 0.75},
  ];
  return (
    <AbsoluteFill style={{flexDirection: 'row', background: '#000'}}>
      {panels.map((p, i) => {
        const drop = tw(t, [SPLIT + i * 0.12, SPLIT + i * 0.12 + 0.3], [-1100, 0]);
        return (
          <div key={i} style={{width: 640, height: 1080, overflow: 'hidden', position: 'relative', borderRight: `10px solid ${C.outline}`, transform: `translateY(${drop}px)`}}>
            <div style={{position: 'absolute', width: 1920, height: 1080, left: 320 - 1920 * p.focus, top: 0}}>
              <p.C t={p.freeze} g={p.gt} />
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const Xs: React.FC<{t: number}> = ({t}) => (
  <AbsoluteFill style={{flexDirection: 'row'}}>
    {[0, 1, 2].map((i) => (
      <div key={i} style={{width: 640, height: 1080, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <XMark at={SPLIT + 0.5 + i * 0.5} t={t} />
      </div>
    ))}
  </AbsoluteFill>
);

const XMark: React.FC<{at: number; t: number}> = ({at}) => {
  const p = usePop(at, 10, 300);
  const t = useT();
  if (t < at) return null;
  return (
    <svg width={420} height={420} viewBox="-100 -100 200 200" style={{transform: `scale(${2.5 - p * 1.5}) rotate(${(1 - p) * 30}deg)`, opacity: Math.min(1, p * 2)}}>
      <path d="M-70 -70 L70 70 M70 -70 L-70 70" stroke={C.outline} strokeWidth={46} strokeLinecap="round" />
      <path d="M-70 -70 L70 70 M70 -70 L-70 70" stroke="#E2342A" strokeWidth={30} strokeLinecap="round" />
    </svg>
  );
};
