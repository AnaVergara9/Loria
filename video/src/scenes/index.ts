import React from 'react';
import {E00_Gancho} from './E00_Gancho';
import {E01_Entrevista} from './E01_Entrevista';
import {E02_Montaje} from './E02_Montaje';
import {E03_Pregunta} from './E03_Pregunta';
import {E04_Entrada} from './E04_Entrada';
import {E05_ChisteLoro} from './E05_ChisteLoro';
import {E06_Escribele} from './E06_Escribele';
import {E07_PeroEspera} from './E07_PeroEspera';
import {E08_NotasVoz} from './E08_NotasVoz';
import {E09_Rebobinado} from './E09_Rebobinado';
import {E10_ModoNinos} from './E10_ModoNinos';
import {E11_Botones} from './E11_Botones';
import {E12_Testimonios} from './E12_Testimonios';
import {E13_Oferta} from './E13_Oferta';
import {E14_Final} from './E14_Final';

// Lista de escenas: el id (E00, E01...) conecta cada archivo con su duracion en timeline.ts
export const SCENE_COMPONENTS: Record<string, React.FC> = {
  E00: E00_Gancho,
  E01: E01_Entrevista,
  E02: E02_Montaje,
  E03: E03_Pregunta,
  E04: E04_Entrada,
  E05: E05_ChisteLoro,
  E06: E06_Escribele,
  E07: E07_PeroEspera,
  E08: E08_NotasVoz,
  E09: E09_Rebobinado,
  E10: E10_ModoNinos,
  E11: E11_Botones,
  E12: E12_Testimonios,
  E13: E13_Oferta,
  E14: E14_Final,
};
