import React from 'react';
import {Composition} from 'remotion';
import {LoriaTest} from './scenes/LoriaTest';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="LoriaTest" component={LoriaTest} durationInFrames={150} fps={30} width={1920} height={1080} />
    </>
  );
};
