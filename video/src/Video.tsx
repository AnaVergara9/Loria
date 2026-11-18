import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import {SCENE_COMPONENTS} from './scenes';
import {SCENES, s} from './timeline';
import {Music} from './components/core';
import {C} from './theme';

// EL VIDEO COMPLETO: pone las escenas una detras de otra segun timeline.ts
export const LoriaPromo: React.FC = () => {
  let from = 0;
  return (
    <AbsoluteFill style={{background: C.cream}}>
      {SCENES.map((sc) => {
        const Comp = SCENE_COMPONENTS[sc.id];
        const start = from;
        from += s(sc.dur);
        return (
          <Sequence key={sc.id} from={start} durationInFrames={s(sc.dur)} name={`${sc.id} ${sc.name}`}>
            {Comp ? <Comp /> : <Placeholder id={sc.id} name={sc.name} />}
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
