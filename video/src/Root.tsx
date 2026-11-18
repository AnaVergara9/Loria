import React from 'react';
import {Composition, Folder} from 'remotion';
import {LoriaTest} from './scenes/LoriaTest';
import {CastTest} from './scenes/CastTest';
import {LoriaPromo} from './Video';
import {SCENE_COMPONENTS} from './scenes';
import {SCENES, s, TOTAL} from './timeline';

// Aqui se "registran" los videos que aparecen en el Studio:
// - LoriaPromo: el video completo de 3 minutos.
// - Una composicion por escena (carpeta "Escenas") para verlas sueltas.
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="LoriaPromo" component={LoriaPromo} durationInFrames={s(TOTAL)} fps={30} width={1920} height={1080} />
      <Folder name="Escenas">
        {SCENES.filter((sc) => SCENE_COMPONENTS[sc.id]).map((sc) => (
          <Composition key={sc.id} id={sc.id} component={SCENE_COMPONENTS[sc.id]} durationInFrames={s(sc.dur)} fps={30} width={1920} height={1080} />
        ))}
      </Folder>
      <Folder name="Pruebas">
        <Composition id="LoriaTest" component={LoriaTest} durationInFrames={150} fps={30} width={1920} height={1080} />
        <Composition id="CastTest" component={CastTest} durationInFrames={30} fps={30} width={1920} height={1080} />
      </Folder>
    </>
  );
};
