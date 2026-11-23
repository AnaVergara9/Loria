import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {C} from '../theme';
import {TITLE, tw, useT} from './core';

/** Television vieja: blanco y negro, rayas, vineta y temblor. Envuelve la escena. */
export const OldTV: React.FC<{children: React.ReactNode; amount?: number}> = ({children, amount = 1}) => {
  const f = useCurrentFrame();
  const jitter = f % 17 === 0 ? 6 : f % 11 === 0 ? -4 : 0;
  return (
    <AbsoluteFill>
      <AbsoluteFill
        style={{
          filter: `grayscale(${amount}) contrast(${1 + 0.25 * amount}) brightness(${1 - 0.05 * amount}) sepia(${0.12 * amount})`,
          transform: `translateX(${jitter * amount}px)`,
        }}
      >
        {children}
      </AbsoluteFill>
      {amount > 0 && (
        <>
          <AbsoluteFill
            style={{
              opacity: 0.22 * amount,
              background: 'repeating-linear-gradient(0deg, rgba(0,0,0,0.9) 0px, rgba(0,0,0,0.9) 2px, transparent 3px, transparent 6px)',
            }}
          />
          <AbsoluteFill style={{opacity: amount, background: 'radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.65) 100%)'}} />
          <AbsoluteFill
            style={{
              opacity: 0.15 * amount,
              background: `linear-gradient(180deg, transparent ${(f * 7) % 120 - 20}%, rgba(255,255,255,0.8) ${(f * 7) % 120 - 10}%, transparent ${(f * 7) % 120}%)`,
            }}
          />
          <Noise opacity={0.12 * amount} />
        </>
      )}
    </AbsoluteFill>
  );
};

/** Ruido de television (granulado). */
export const Noise: React.FC<{opacity?: number}> = ({opacity = 1}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{opacity, mixBlendMode: 'overlay'}}>
      <svg width="1920" height="1080">
        <filter id={`n${f}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={f % 50} />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="1920" height="1080" filter={`url(#n${f})`} />
      </svg>
    </AbsoluteFill>
  );
};

/** Estatica fuerte de canal (entre t0 y t1 segundos). */
export const StaticBurst: React.FC<{from: number; to: number}> = ({from, to}) => {
  const t = useT();
  if (t < from || t > to) return null;
  const o = Math.min(tw(t, [from, from + 0.1], [0, 1]), tw(t, [to - 0.1, to], [1, 0]));
  return (
    <AbsoluteFill style={{opacity: o, background: '#777'}}>
      <Noise opacity={1} />
      <AbsoluteFill style={{background: 'repeating-linear-gradient(0deg, rgba(0,0,0,0.5) 0 3px, transparent 3px 7px)'}} />
    </AbsoluteFill>
  );
};

/** Efecto de rebobinado de casete (rayas, desplazamiento y simbolo ◀◀). */
export const Rewind: React.FC<{from: number; to: number; label?: string}> = ({from, to, label = '◀◀ REW'}) => {
  const t = useT();
  const f = useCurrentFrame();
  if (t < from || t > to) return null;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {new Array(6).fill(0).map((_, i) => {
        const y = ((f * 53 + i * 197) % 1200) - 60;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: 0,
              right: 0,
              top: y,
              height: 18 + (i % 3) * 14,
              background: 'rgba(255,255,255,0.55)',
              mixBlendMode: 'difference',
              transform: `translateX(${Math.sin(f + i) * 60}px)`,
            }}
          />
        );
      })}
      <Noise opacity={0.35} />
      <div
        style={{
          position: 'absolute',
          left: 70,
          top: 50,
          fontFamily: 'monospace',
          fontWeight: 900,
          fontSize: 80,
          color: '#fff',
          textShadow: '4px 0 #f0f, -4px 0 #0ff',
          opacity: f % 10 < 6 ? 1 : 0.4,
        }}
      >
        {label}
      </div>
    </AbsoluteFill>
  );
};

/**
 * Barrido de transicion: una franja de colores de Loria cruza la pantalla.
 * Se pone al inicio de una escena (en: true) o al final (en: false).
 */
export const Swipe: React.FC<{at: number; dur?: number; colors?: string[]; dir?: 1 | -1}> = ({
  at,
  dur = 0.4,
  colors = [C.yellow, C.orange, C.green],
  dir = 1,
}) => {
  const t = useT();
  if (t < at || t > at + dur) return null;
  const p = (t - at) / dur;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      {colors.map((c, i) => {
        const x = interpolate(p, [0, 1], [-2600 + i * 180, 2600 + i * 180]) * dir;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              top: -400,
              left: 0,
              width: 900,
              height: 1900,
              background: c,
              borderLeft: `14px solid ${C.outline}`,
              borderRight: `14px solid ${C.outline}`,
              transform: `translateX(${x}px) rotate(18deg)`,
              filter: 'blur(2px)',
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/** Fogonazo blanco de un instante. */
export const Flash: React.FC<{at: number; dur?: number; color?: string}> = ({at, dur = 0.25, color = '#fff'}) => {
  const t = useT();
  if (t < at || t > at + dur) return null;
  return <AbsoluteFill style={{background: color, opacity: tw(t, [at, at + dur], [0.95, 0])}} />;
};

/** Lineas de velocidad (estilo manga) desde el centro. */
export const SpeedLines: React.FC<{opacity?: number; color?: string}> = ({opacity = 1, color = '#fff'}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{opacity}}>
      <svg width="1920" height="1080" viewBox="-960 -540 1920 1080">
        {new Array(48).fill(0).map((_, i) => {
          const a = (i / 48) * Math.PI * 2 + (f % 3) * 0.02;
          const r0 = 380 + ((i * 37 + f * 13) % 160);
          return (
            <path
              key={i}
              d={`M${Math.cos(a) * r0} ${Math.sin(a) * r0} L${Math.cos(a - 0.018) * 1400} ${Math.sin(a - 0.018) * 1400} L${Math.cos(a + 0.018) * 1400} ${Math.sin(a + 0.018) * 1400} Z`}
              fill={color}
            />
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

/** Rotulo pequeno en una esquina (ej. "Dramatizacion"). */
export const CornerTag: React.FC<{text: string; at?: number}> = ({text, at = 0}) => {
  const t = useT();
  if (t < at) return null;
  return (
    <div
      style={{
        position: 'absolute',
        right: 90,
        top: 60,
        fontFamily: TITLE,
        fontSize: 30,
        color: '#fff',
        background: 'rgba(42,9,4,0.7)',
        borderRadius: 12,
        padding: '8px 18px 2px',
        letterSpacing: 1,
      }}
    >
      {text}
    </div>
  );
};

/** Cartel de cine mudo (fondo negro, marco decorado, letra clasica). */
export const SilentCard: React.FC<{from: number; to: number; text: React.ReactNode}> = ({from, to, text}) => {
  const t = useT();
  if (t < from || t > to) return null;
  const o = Math.min(tw(t, [from, from + 0.1], [0, 1]), tw(t, [to - 0.12, to], [1, 0]));
  return (
    <AbsoluteFill style={{background: '#0B0B0B', opacity: o, justifyContent: 'center', alignItems: 'center'}}>
      <div style={{position: 'absolute', inset: 60, border: '6px solid #E9E2D0', outline: '2px solid #E9E2D0', outlineOffset: -22, borderRadius: 20}} />
      {[[90, 90], [1830, 90], [90, 990], [1830, 990]].map(([x, y], i) => (
        <div key={i} style={{position: 'absolute', left: x - 22, top: y - 22, width: 44, height: 44, transform: 'rotate(45deg)', border: '5px solid #E9E2D0'}} />
      ))}
      <div style={{fontFamily: 'Georgia, "Times New Roman", serif', fontStyle: 'italic', fontSize: 96, color: '#F2EDE0', textAlign: 'center', lineHeight: 1.25, padding: '0 200px'}}>{text}</div>
      <Noise opacity={0.25} />
    </AbsoluteFill>
  );
};
