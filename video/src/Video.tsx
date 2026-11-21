import React from 'react';
import {AbsoluteFill, Audio, Easing, interpolate, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {SCENE_COMPONENTS} from './scenes';
import {SCENES, s} from './timeline';
import {Music} from './components/core';
import {C} from './theme';

/**
 * TRANSICIONES entre escenas (como en los videos de referencia: barrido borroso).
 * Cada escena entra y sale con un movimiento rapido. "none" = la escena ya trae su propia transicion.
 *   left / right / up / down = barrido hacia ese lado    zoom = acercamiento brusco
 */
type Tr = 'left' | 'right' | 'up' | 'down' | 'zoom' | 'none';
const TRANSITIONS: Record<string, {enter: Tr; exit: Tr}> = {
  E00: {enter: 'none', exit: 'none'}, // se apaga como tele vieja
  E01: {enter: 'none', exit: 'left'},
  E02: {enter: 'left', exit: 'up'},
  E03: {enter: 'up', exit: 'none'}, // termina en estatica
  E04: {enter: 'none', exit: 'left'}, // entra con fogonazo
  E05: {enter: 'left', exit: 'zoom'},
  E06: {enter: 'zoom', exit: 'none'},
  E07: {enter: 'none', exit: 'right'}, // zoom brusco propio
  E08: {enter: 'right', exit: 'none'},
  E09: {enter: 'none', exit: 'none'}, // rebobinado
  E10: {enter: 'none', exit: 'none'}, // circulo de crayon / rebobinado
  E11: {enter: 'none', exit: 'left'},
  E12: {enter: 'left', exit: 'up'},
  E13: {enter: 'up', exit: 'zoom'},
  E14: {enter: 'zoom', exit: 'none'},
};
const IN = 7; // cuadros que dura la entrada
const OUT = 6; // cuadros que dura la salida

const move = (type: Tr, p: number, out: boolean): React.CSSProperties => {
  // p: 0 = en su sitio, 1 = totalmente fuera
  const d = out ? -1 : 1;
  const blur = p * 40;
  switch (type) {
    case 'left':
      return {transform: `translateX(${d * p * 1900}px) skewX(${-d * p * 8}deg)`, filter: `blur(${blur}px)`};
    case 'right':
      return {transform: `translateX(${-d * p * 1900}px) skewX(${d * p * 8}deg)`, filter: `blur(${blur}px)`};
    case 'up':
      return {transform: `translateY(${d * p * 1100}px)`, filter: `blur(${blur}px)`};
    case 'down':
      return {transform: `translateY(${-d * p * 1100}px)`, filter: `blur(${blur}px)`};
    case 'zoom':
      return {transform: `scale(${out ? 1 + p * 2.5 : 1 + p * 1.5}) rotate(${p * 12}deg)`, filter: `blur(${blur}px)`, opacity: 1 - p * 0.6};
    default:
      return {};
  }
};

const Transitioned: React.FC<{id: string; frames: number; children: React.ReactNode}> = ({id, frames, children}) => {
  const f = useCurrentFrame();
  const tr = TRANSITIONS[id] ?? {enter: 'none', exit: 'none'};
  let style: React.CSSProperties = {};
  if (tr.enter !== 'none' && f < IN) {
    style = move(tr.enter, interpolate(f, [0, IN], [1, 0], {easing: Easing.out(Easing.cubic)}), false);
  } else if (tr.exit !== 'none' && f >= frames - OUT) {
    style = move(tr.exit, interpolate(f, [frames - OUT, frames], [0, 1], {easing: Easing.in(Easing.cubic)}), true);
  }
  return <AbsoluteFill style={style}>{children}</AbsoluteFill>;
};

// EL VIDEO COMPLETO: pone las escenas una detras de otra segun timeline.ts
export const LoriaPromo: React.FC = () => {
  let from = 0;
  return (
    <AbsoluteFill style={{background: C.yellow}}>
      {SCENES.map((sc) => {
        const Comp = SCENE_COMPONENTS[sc.id];
        const start = from;
        from += s(sc.dur);
        const tr = TRANSITIONS[sc.id];
        return (
          <Sequence key={sc.id} from={start} durationInFrames={s(sc.dur)} name={`${sc.id} ${sc.name}`}>
            <Transitioned id={sc.id} frames={s(sc.dur)}>
              {Comp ? <Comp /> : <Placeholder id={sc.id} name={sc.name} />}
            </Transitioned>
            {tr && tr.exit !== 'none' && (
              <Sequence from={s(sc.dur) - OUT - 3} layout="none">
                <Audio src={staticFile('sfx/whoosh.wav')} volume={0.6} />
              </Sequence>
            )}
          </Sequence>
        );
      })}
      <Music />
    </AbsoluteFill>
  );
};

const Placeholder: React.FC<{id: string; name: string}> = ({id, name}) => (
  <AbsoluteFill style={{background: '#333', color: '#fff', justifyContent: 'center', alignItems: 'center', fontSize: 80, fontFamily: 'sans-serif'}}>
    {id} · {name} (pendiente)
  </AbsoluteFill>
);
