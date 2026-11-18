import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {C} from '../theme';
import {BODY, TITLE} from './core';
import {LoriaAvatar} from './Studio';
import {s} from '../timeline';

/**
 * Celular con un chat de Telegram con Loria.
 * Los mensajes llegan en el segundo "at" (dentro de la escena).
 */
export type Msg =
  | {at: number; from: 'me'; text: string; wrong?: boolean; strikeAt?: number}
  | {at: number; from: 'me'; voice: number}
  | {at: number; from: 'loria'; fix: string; why: string; label?: string}
  | {at: number; from: 'loria'; text: string};

export const Phone: React.FC<{
  msgs: Msg[];
  width?: number;
  rotY?: number;
  rotX?: number;
  rotZ?: number;
  scroll?: number;
  style?: React.CSSProperties;
}> = ({msgs, width = 560, rotY = -14, rotX = 6, rotZ = 0, scroll = 0, style}) => {
  const h = width * 2.05;
  return (
    <div style={{perspective: 1800, ...style}}>
      <div
        style={{
          width,
          height: h,
          transform: `rotateY(${rotY}deg) rotateX(${rotX}deg) rotateZ(${rotZ}deg)`,
          transformStyle: 'preserve-3d',
          position: 'relative',
        }}
      >
        {/* grosor del telefono */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: width * 0.13,
            background: '#1E2230',
            transform: `translateZ(-28px) translateX(${rotY < 0 ? 14 : -14}px)`,
            border: `8px solid ${C.outline}`,
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: width * 0.13,
            background: 'linear-gradient(135deg, #3A4152, #1E2230)',
            border: `9px solid ${C.outline}`,
            padding: width * 0.035,
            boxShadow: '0 40px 80px rgba(0,0,0,0.35)',
          }}
        >
          <div
            style={{
              width: '100%',
              height: '100%',
              borderRadius: width * 0.1,
              overflow: 'hidden',
              background: '#DCEFD0',
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* patron del fondo del chat */}
            <div
              style={{
                position: 'absolute',
                inset: 0,
                opacity: 0.25,
                background: `radial-gradient(circle at 20% 30%, ${C.green} 0 6px, transparent 7px), radial-gradient(circle at 70% 60%, ${C.yellow} 0 5px, transparent 6px)`,
                backgroundSize: '90px 90px',
              }}
            />
            {/* barra superior */}
            <div
              style={{
                position: 'relative',
                zIndex: 2,
                background: '#4F8FCB',
                padding: `${width * 0.09}px ${width * 0.04}px ${width * 0.03}px`,
                display: 'flex',
                alignItems: 'center',
                gap: width * 0.03,
                borderBottom: `4px solid ${C.outline}`,
              }}
            >
              <LoriaAvatar size={width * 0.14} />
              <div>
                <div style={{fontFamily: BODY, fontWeight: 800, fontSize: width * 0.06, color: '#fff', lineHeight: 1}}>Loria</div>
                <div style={{fontFamily: BODY, fontWeight: 600, fontSize: width * 0.036, color: '#DDEBFF'}}>bot · en línea</div>
              </div>
            </div>
            {/* mensajes */}
            <div
              style={{
                position: 'relative',
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'flex-end',
                padding: width * 0.035,
                gap: width * 0.025,
                transform: `translateY(${-scroll}px)`,
              }}
            >
              {msgs.map((m, i) => (
                <Bubble key={i} m={m} w={width} />
              ))}
            </div>
          </div>
        </div>
        {/* brillo del vidrio */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: width * 0.13,
            background: 'linear-gradient(115deg, rgba(255,255,255,0.22) 0%, rgba(255,255,255,0) 35%)',
            pointerEvents: 'none',
          }}
        />
      </div>
    </div>
  );
};

const Bubble: React.FC<{m: Msg; w: number}> = ({m, w}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: f - s(m.at), fps, config: {damping: 12, stiffness: 200}});
  if (f < s(m.at)) return null;
  const me = m.from === 'me';
  const fs = w * 0.052;
  const base: React.CSSProperties = {
    alignSelf: me ? 'flex-end' : 'flex-start',
    maxWidth: '86%',
    background: me ? '#EFFFDE' : '#fff',
    border: `4px solid ${C.outline}`,
    borderRadius: me ? '22px 22px 6px 22px' : '22px 22px 22px 6px',
    padding: `${w * 0.022}px ${w * 0.035}px`,
    fontFamily: BODY,
    fontWeight: 600,
    fontSize: fs,
    color: C.outline,
    lineHeight: 1.2,
    transform: `scale(${interpolate(p, [0, 1], [0.3, 1])})`,
    transformOrigin: me ? '100% 100%' : '0% 100%',
    opacity: Math.min(1, p * 2),
    boxShadow: '0 4px 0 rgba(42,9,4,0.25)',
  };

  if ('voice' in m) {
    return (
      <div style={{...base, display: 'flex', alignItems: 'center', gap: w * 0.025}}>
        <div style={{width: fs * 1.6, height: fs * 1.6, borderRadius: '50%', background: '#4F8FCB', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: fs * 0.8}}>▶</div>
        <svg width={w * 0.38} height={fs * 1.4}>
          {new Array(22).fill(0).map((_, i) => {
            const hh = (0.25 + 0.75 * Math.abs(Math.sin(i * 1.7 + (f - s(m.at)) * 0.15))) * fs * 1.2;
            return <rect key={i} x={i * ((w * 0.38) / 22)} y={(fs * 1.4 - hh) / 2} width={(w * 0.38) / 22 - 3} height={hh} rx={3} fill="#4F8FCB" />;
          })}
        </svg>
        <span style={{fontSize: fs * 0.7}}>0:0{m.voice}</span>
      </div>
    );
  }
  if ('fix' in m) {
    return (
      <div style={base}>
        <div style={{fontFamily: TITLE, fontSize: fs * 0.7, color: C.greenDark, letterSpacing: 1}}>{m.label ?? '✔ ASÍ SE DICE'}</div>
        <div style={{fontWeight: 800, color: '#2E8B2E', fontSize: fs * 1.08}}>{m.fix}</div>
        <div style={{fontSize: fs * 0.82, marginTop: 4, color: '#5A3A30'}}>💡 {m.why}</div>
      </div>
    );
  }
  const wrong = 'wrong' in m && m.wrong;
  const struck = 'strikeAt' in m && m.strikeAt !== undefined && f >= s(m.strikeAt);
  const strikeP = 'strikeAt' in m && m.strikeAt !== undefined ? Math.min(1, Math.max(0, (f - s(m.strikeAt)) / 8)) : 0;
  return (
    <div style={{...base, color: wrong ? '#D02B20' : C.outline, position: 'relative'}}>
      {m.text}
      {struck && (
        <div
          style={{
            position: 'absolute',
            left: '6%',
            top: '50%',
            height: 6,
            width: `${88 * strikeP}%`,
            background: '#D02B20',
            borderRadius: 3,
            transform: 'rotate(-3deg)',
          }}
        />
      )}
    </div>
  );
};
