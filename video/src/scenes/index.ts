import React from 'react';
import {E00_Gancho} from './E00_Gancho';
import {E01_Entrevista} from './E01_Entrevista';
import {E02_Montaje} from './E02_Montaje';
import {E03_Pregunta} from './E03_Pregunta';

// Lista de escenas: el id (E00, E01...) conecta cada archivo con su duracion en timeline.ts
export const SCENE_COMPONENTS: Record<string, React.FC> = {
  E00: E00_Gancho,
  E01: E01_Entrevista,
  E02: E02_Montaje,
  E03: E03_Pregunta,
};
