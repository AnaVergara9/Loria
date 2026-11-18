import React from 'react';
import {AbsoluteFill} from 'remotion';
import {ANDRES, CAMILA, CAMILA_PJ, CAMILA_SUIT, JEFE, MARTA, MESERO, Person} from '../characters/Person';

// Prueba del elenco (no va en el video final).
export const CastTest: React.FC = () => (
  <AbsoluteFill style={{background: '#FFF3D6', flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-around', paddingBottom: 40}}>
    <Person {...CAMILA} width={250} />
    <Person {...CAMILA} mood="shy" width={250} armR={150} foreR={-120} phone id="c2" />
    <Person {...CAMILA_SUIT} mood="happy" width={250} armL={130} armR={130} />
    <Person {...CAMILA_PJ} mood="neutral" talk={0.7} width={250} />
    <Person {...JEFE} mood="angry" width={250} />
    <Person {...MESERO} mood="skeptic" width={250} />
    <Person {...ANDRES} mood="happy" width={250} />
    <Person {...MARTA} mood="happy" width={220} />
  </AbsoluteFill>
);
