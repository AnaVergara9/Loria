import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {C} from '../theme';
import {BODY, TITLE} from './core';

const O = C.outline;

/** Oficina: pared, ventana con persianas, planta y escritorio. */
export const OfficeBG: React.FC = () => (
  <AbsoluteFill style={{background: 'linear-gradient(180deg, #E9DCC4, #D6C3A3)'}}>
    <div style={{position: 'absolute', left: 1150, top: 120, width: 560, height: 440, background: 'linear-gradient(180deg, #A9D6F5, #E3F3FF)', border: `12px solid ${O}`, borderRadius: 12, overflow: 'hidden'}}>
      {new Array(9).fill(0).map((_, i) => (
        <div key={i} style={{height: 22, marginTop: 24, background: 'rgba(255,255,255,0.75)', borderBottom: '3px solid rgba(0,0,0,0.15)'}} />
      ))}
      <div style={{position: 'absolute', bottom: 0, left: 40, width: 80, height: 180, background: '#7C8AA0'}} />
      <div style={{position: 'absolute', bottom: 0, left: 150, width: 110, height: 260, background: '#64738C'}} />
      <div style={{position: 'absolute', bottom: 0, left: 300, width: 90, height: 140, background: '#8592A8'}} />
    </div>
    <div style={{position: 'absolute', left: 200, top: 160, width: 260, height: 180, background: '#fff', border: `10px solid ${O}`, borderRadius: 8, display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', padding: 20}}>
      {[60, 100, 80, 140].map((h, i) => (
        <div key={i} style={{width: 34, height: h, background: [C.green, C.orange, C.yellow, C.red][i], border: `4px solid ${O}`}} />
      ))}
    </div>
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 200, background: 'linear-gradient(180deg, #9C7A55, #7A5A3A)', borderTop: `10px solid ${O}`}} />
  </AbsoluteFill>
);

/** Escritorio (va delante de los personajes). */
export const Desk: React.FC<{x: number; y: number; w?: number}> = ({x, y, w = 760}) => (
  <div style={{position: 'absolute', left: x, top: y, width: w, height: 400}}>
    <div style={{position: 'absolute', top: 0, left: -20, right: -20, height: 46, background: 'linear-gradient(180deg, #A97B4F, #8A5F38)', border: `9px solid ${O}`, borderRadius: 12}} />
    <div style={{position: 'absolute', top: 40, left: 0, right: 0, bottom: 0, background: 'linear-gradient(180deg, #8A5F38, #6B4527)', border: `9px solid ${O}`}} />
    <div style={{position: 'absolute', top: -70, left: 80, width: 120, height: 80, background: '#fff', border: `6px solid ${O}`, transform: 'rotate(-6deg)'}} />
    <div style={{position: 'absolute', top: -90, right: 120, width: 70, height: 90, background: C.red, border: `6px solid ${O}`, borderRadius: '6px 6px 20px 20px'}} />
  </div>
);

/** Cafe en Paris: cielo, Torre Eiffel, toldo de rayas y mesita. */
export const CafeBG: React.FC = () => (
  <AbsoluteFill style={{background: 'linear-gradient(180deg, #8EC9EE, #FCE7C2)'}}>
    <svg width="1920" height="1080" style={{position: 'absolute'}}>
      <g transform="translate(1500 120)" fill="#6E7A8A" stroke={O} strokeWidth={8} strokeLinejoin="round">
        <path d="M0 0 L20 0 L60 300 L130 620 L60 620 Q10 520 -40 620 L-110 620 L-40 300 Z" />
        <path d="M-60 300 L80 300 L80 330 L-60 330 Z M-90 470 L110 470 L110 500 L-90 500 Z" />
      </g>
      <rect x={0} y={680} width={1920} height={400} fill="#C9A27A" stroke={O} strokeWidth={10} />
      {new Array(12).fill(0).map((_, i) => (
        <path key={i} d={`M${i * 170 - 40} 0 L${i * 170 + 130} 0 L${i * 170 + 130} 150 Q${i * 170 + 45} 200 ${i * 170 - 40} 150 Z`} fill={i % 2 ? '#fff' : '#D8443A'} stroke={O} strokeWidth={8} />
      ))}
    </svg>
  </AbsoluteFill>
);

export const CafeTable: React.FC<{x: number; y: number}> = ({x, y}) => (
  <svg style={{position: 'absolute', left: x - 200, top: y}} width={400} height={360} viewBox="0 0 400 360">
    <ellipse cx={200} cy={40} rx={190} ry={36} fill="#fff" stroke={O} strokeWidth={8} />
    <rect x={185} y={60} width={30} height={260} fill="#444" stroke={O} strokeWidth={6} />
    <ellipse cx={200} cy={330} rx={90} ry={18} fill="#444" stroke={O} strokeWidth={6} />
    <path d="M150 30 q10 -40 40 -30 q30 -10 30 30 Z" fill="#E7B060" stroke={O} strokeWidth={5} />
    <rect x={250} y={0} width={44} height={36} rx={8} fill="#fff" stroke={O} strokeWidth={5} />
  </svg>
);

/** Aeropuerto: tablero de vuelos, ventanales y avion. */
export const AirportBG: React.FC = () => {
  const f = useCurrentFrame();
  const rows = ['PARIS     CDG  14:05', 'LONDON    LHR  14:30', 'NEW YORK  JFK  15:10', 'TORONTO   YYZ  15:45'];
  return (
    <AbsoluteFill style={{background: 'linear-gradient(180deg, #D7E3EC, #B8C7D3)'}}>
      <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: 560, background: 'linear-gradient(180deg, #9BD0F2, #DDF1FF)', borderBottom: `10px solid ${O}`}}>
        {new Array(7).fill(0).map((_, i) => (
          <div key={i} style={{position: 'absolute', left: i * 300, top: 0, width: 14, height: 560, background: '#6B7A88'}} />
        ))}
        <div style={{position: 'absolute', left: ((f * 6) % 2600) - 400, top: 120, fontSize: 200, transform: 'scaleX(-1)'}}>✈</div>
      </div>
      <div style={{position: 'absolute', left: 560, top: 70, width: 800, padding: 24, background: '#1E1E24', border: `10px solid ${O}`, borderRadius: 14}}>
        <div style={{fontFamily: TITLE, fontSize: 40, color: C.yellow, marginBottom: 10}}>DEPARTURES</div>
        {rows.map((r, i) => (
          <div key={i} style={{fontFamily: 'monospace', fontWeight: 900, fontSize: 40, color: '#FFD84A', whiteSpace: 'pre', borderTop: '2px solid #333', padding: '4px 0'}}>
            {r}
          </div>
        ))}
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 520, background: 'linear-gradient(180deg, #E6E1D8, #C8C1B4)'}}>
        <div style={{position: 'absolute', inset: 0, background: 'repeating-linear-gradient(90deg, transparent 0 158px, rgba(0,0,0,0.08) 158px 162px)'}} />
      </div>
    </AbsoluteFill>
  );
};

/** Mesa grande para esconderse debajo (va delante). */
export const HideTable: React.FC = () => (
  <svg width="1920" height="1080" style={{position: 'absolute'}}>
    <rect x={-40} y={330} width={2000} height={110} fill="#B9824F" stroke={O} strokeWidth={12} />
    <rect x={-40} y={330} width={2000} height={26} fill="#D7A06A" />
    <rect x={140} y={435} width={90} height={900} fill="#8A5F38" stroke={O} strokeWidth={10} />
    <rect x={1690} y={435} width={90} height={900} fill="#8A5F38" stroke={O} strokeWidth={10} />
  </svg>
);

/** Panel de videollamada: cuadritos de personas y barra de botones. */
export const CallUI: React.FC<{muted: boolean; camOff: boolean}> = ({muted, camOff}) => (
  <>
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 110, background: '#1C1F26', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 40}}>
      <CallBtn icon="🎤" off={muted} />
      <CallBtn icon="📷" off={camOff} />
      <div style={{width: 120, height: 70, borderRadius: 35, background: '#D23B32', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 40}}>📞</div>
    </div>
    <div style={{position: 'absolute', left: 30, top: 24, fontFamily: BODY, fontWeight: 800, fontSize: 34, color: '#fff'}}>Reunión de equipo · 12:00</div>
  </>
);

const CallBtn: React.FC<{icon: string; off: boolean}> = ({icon, off}) => (
  <div style={{width: 80, height: 80, borderRadius: '50%', background: off ? '#D23B32' : '#3A3F4B', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 40, position: 'relative'}}>
    {icon}
    {off && <div style={{position: 'absolute', width: 80, height: 8, background: '#fff', transform: 'rotate(-45deg)', borderRadius: 4}} />}
  </div>
);

/** Cuadro de una persona en la videollamada. */
export const CallTile: React.FC<{x: number; y: number; w: number; h: number; name: string; bg?: string; children?: React.ReactNode; off?: boolean}> = ({
  x,
  y,
  w,
  h,
  name,
  bg = '#55607A',
  children,
  off,
}) => (
  <div style={{position: 'absolute', left: x, top: y, width: w, height: h, background: off ? '#15171C' : bg, borderRadius: 22, overflow: 'hidden', border: '6px solid #0E1014'}}>
    {!off && children}
    {off && (
      <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <div style={{width: 180, height: 180, borderRadius: '50%', background: C.orange, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: TITLE, fontSize: 90, color: '#fff', paddingTop: 14}}>C</div>
      </div>
    )}
    <div style={{position: 'absolute', left: 16, bottom: 14, fontFamily: BODY, fontWeight: 800, fontSize: 30, color: '#fff', background: 'rgba(0,0,0,0.5)', borderRadius: 10, padding: '2px 14px'}}>{name}</div>
  </div>
);
