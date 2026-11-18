// ORDEN Y DURACION DE LAS ESCENAS (en segundos). Suman 180 s = 3:00 exactos.
// Si alargas una escena, acorta otra para que el total siga en 180.
export const FPS = 30;
export const s = (sec: number) => Math.round(sec * FPS);

export const SCENES = [
  {id: 'E00', name: 'Gancho', dur: 3},
  {id: 'E01', name: 'Entrevista', dur: 7},
  {id: 'E02', name: 'Montaje de fallos', dur: 10},
  {id: 'E03', name: 'La pregunta', dur: 8},
  {id: 'E04', name: 'Llega Loria', dur: 8},
  {id: 'E05', name: 'El chiste del loro', dur: 16},
  {id: 'E06', name: 'Escribele', dur: 14},
  {id: 'E07', name: 'Pero espera', dur: 4},
  {id: 'E08', name: 'Notas de voz', dur: 28},
  {id: 'E09', name: 'Rebobinado', dur: 4},
  {id: 'E10', name: 'Modo ninos', dur: 26},
  {id: 'E11', name: 'Botones', dur: 14},
  {id: 'E12', name: 'Testimonios', dur: 18},
  {id: 'E13', name: 'La oferta', dur: 8},
  {id: 'E14', name: 'Final', dur: 12},
] as const;

export type SceneId = (typeof SCENES)[number]['id'];
export const TOTAL = SCENES.reduce((a, b) => a + b.dur, 0);
