import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {C} from '../theme';
import {Loria} from '../characters/Loria';
import {BODY, TITLE} from './core';

/** Fondo de estudio de teletienda: rayos que giran, focos, bombillos y piso brillante. */
export const StudioBG: React.FC<{lights?: boolean; red?: boolean; floor?: boolean}> = ({lights = true, red = false, floor = true}) => {
  const f = useCurrentFrame();
  const c1 = red ? '#FF5A3C' : C.yellow;
  const c2 = red ? '#B3121F' : C.orange;
  return (
    <AbsoluteFill style={{background: red ? '#5A0A10' : '#B9471C', overflow: 'hidden'}}>
      {/* rayos */}
      <svg width="1920" height="1080" viewBox="-960 -540 1920 1080" style={{position: 'absolute'}}>
        <g transform={`rotate(${f * 0.4})`}>
          {new Array(24).fill(0).map((_, i) => {
            const a = (i / 24) * Math.PI * 2;
            const b = ((i + 0.5) / 24) * Math.PI * 2;
            return (
              <path
                key={i}
                d={`M0 0 L${Math.cos(a) * 2000} ${Math.sin(a) * 2000} L${Math.cos(b) * 2000} ${Math.sin(b) * 2000} Z`}
                fill={i % 2 ? c1 : c2}
              />
            );
          })}
        </g>
        <circle r={1300} fill="url(#vign)" />
        <defs>
          <radialGradient id="vign">
            <stop offset="0.15" stopColor="#fff" stopOpacity={0.35} />
            <stop offset="0.5" stopColor="#fff" stopOpacity={0} />
            <stop offset="1" stopColor="#3a0d00" stopOpacity={0.7} />
          </radialGradient>
        </defs>
      </svg>

      {/* marco de bombillos */}
      {lights && <Bulbs />}

      {/* focos que barren */}
      {lights &&
        [-1, 1].map((side) => (
          <div
            key={side}
            style={{
              position: 'absolute',
              top: -200,
              left: side < 0 ? 120 : 1800,
              width: 520,
              height: 1600,
              background: 'linear-gradient(180deg, rgba(255,255,230,0.55), rgba(255,255,230,0))',
              clipPath: 'polygon(46% 0, 54% 0, 100% 100%, 0 100%)',
              transformOrigin: '50% 0',
              transform: `translateX(-50%) rotate(${side * (25 + Math.sin(f * 0.05 + side) * 18)}deg)`,
              mixBlendMode: 'screen',
            }}
          />
        ))}

      {/* piso brillante */}
      {floor && (
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: 300,
            background: `linear-gradient(180deg, ${C.greenDark} 0%, #1F5A2A 100%)`,
            borderTop: `10px solid ${C.outline}`,
          }}
        >
          <div style={{position: 'absolute', inset: 0, background: 'repeating-linear-gradient(90deg, rgba(255,255,255,0.06) 0 120px, transparent 120px 240px)'}} />
          <div style={{position: 'absolute', left: '20%', right: '20%', top: 10, height: 60, background: 'rgba(255,255,255,0.18)', borderRadius: '50%', filter: 'blur(14px)'}} />
        </div>
      )}
    </AbsoluteFill>
  );
};

const Bulbs: React.FC = () => {
  const f = useCurrentFrame();
  const pts: [number, number][] = [];
  for (let x = 40; x < 1920; x += 80) pts.push([x, 34]);
  for (let y = 114; y < 760; y += 80) {
    pts.push([34, y]);
    pts.push([1886, y]);
  }
  return (
    <svg width="1920" height="1080" style={{position: 'absolute'}}>
      {pts.map(([x, y], i) => {
        const on = (i + Math.floor(f / 4)) % 3 !== 0;
        return (
          <g key={i}>
            {on && <circle cx={x} cy={y} r={26} fill="#FFF6B0" opacity={0.45} />}
            <circle cx={x} cy={y} r={14} fill={on ? '#FFFBE0' : '#C9A050'} stroke={C.outline} strokeWidth={4} />
          </g>
        );
      })}
    </svg>
  );
};

/** Mostrador de teletienda con el logo al frente. */
export const Counter: React.FC<{x?: number; y?: number; width?: number}> = ({x = 960, y = 1080, width = 900}) => (
  <div style={{position: 'absolute', left: x - width / 2, top: y - 300, width, height: 330}}>
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: -20,
        right: -20,
        height: 54,
        background: `linear-gradient(180deg, #FFE08A, ${C.yellow})`,
        border: `8px solid ${C.outline}`,
        borderRadius: 22,
        zIndex: 2,
      }}
    />
    <div
      style={{
        position: 'absolute',
        top: 40,
        left: 0,
        right: 0,
        bottom: 0,
        background: `linear-gradient(180deg, ${C.green}, ${C.greenDark})`,
        border: `8px solid ${C.outline}`,
        borderRadius: '0 0 30px 30px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      <Logo size={130} />
    </div>
  </div>
);

/** Logo LORIA: letras gruesas con relieve. */
export const Logo: React.FC<{size?: number; style?: React.CSSProperties}> = ({size = 200, style}) => {
  const depth = Math.round(size / 18);
  const shadow = new Array(depth)
    .fill(0)
    .map((_, i) => `${i + 1}px ${i + 1}px 0 ${C.outline}`)
    .join(',');
  return (
    <div
      style={{
        fontFamily: TITLE,
        fontSize: size,
        lineHeight: 1,
        letterSpacing: size / 30,
        color: C.yellow,
        WebkitTextStroke: `${size / 16}px ${C.outline}`,
        paintOrder: 'stroke fill',
        textShadow: shadow,
        paddingTop: size * 0.12,
        ...style,
      }}
    >
      L<span style={{color: C.orange}}>O</span>R<span style={{color: '#8DD14F'}}>I</span>A
    </div>
  );
};

export const TAGLINE = 'Escríbele o háblale. Loria te corrige.';

export const Tagline: React.FC<{size?: number; style?: React.CSSProperties}> = ({size = 54, style}) => (
  <div
    style={{
      fontFamily: BODY,
      fontWeight: 800,
      fontSize: size,
      color: C.outline,
      background: C.cream,
      border: `6px solid ${C.outline}`,
      borderRadius: 999,
      padding: `${size * 0.12}px ${size * 0.6}px ${size * 0.05}px`,
      boxShadow: `0 8px 0 ${C.outline}`,
      ...style,
    }}
  >
    {TAGLINE}
  </div>
);

/** Cabeza de Loria en un circulo (avatar del chat). */
export const LoriaAvatar: React.FC<{size?: number; glasses?: boolean}> = ({size = 80, glasses = false}) => (
  <div
    style={{
      width: size,
      height: size,
      borderRadius: '50%',
      overflow: 'hidden',
      background: C.yellow,
      border: `${Math.max(3, size / 22)}px solid ${C.outline}`,
      position: 'relative',
      flexShrink: 0,
    }}
  >
    <div style={{position: 'absolute', left: -size * 0.32, top: -size * 0.16}}>
      <Loria width={size * 1.65} glasses={glasses} showShadow={false} id={`av${size}`} />
    </div>
  </div>
);
