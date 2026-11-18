import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Loria} from '../characters/Loria';
import {blinkAt, BODY, Cam, Confetti, Pos, Scene, Sfx, SlamText, Sparkle, talkAmount, TITLE, tw, useT} from '../components/core';
import {StudioBG} from '../components/Studio';
import {C} from '../theme';

// E11 (2:08-2:22) Tres botones gigantes al ritmo. Con cada uno, Loria cambia de accesorio:
// Conversar -> audifonos, Ejercicios -> gorra (y escucha la pronunciacion), Corregir -> gafas. "¡Tu eliges!"
const PRESS = [0.8, 4.2, 7.6];
const FINAL = 11.0;

const BUTTONS = [
  {icon: '💬', label: 'CONVERSAR', color: '#4F8FCB'},
  {icon: '🏋️', label: 'EJERCICIOS', color: C.orange},
  {icon: '✅', label: 'CORREGIR', color: C.green},
];

export const E11_Botones: React.FC = () => {
  const t = useT();
  const active = t >= PRESS[2] ? 2 : t >= PRESS[1] ? 1 : t >= PRESS[0] ? 0 : -1;
  const final = t >= FINAL;
  const bounce = Math.abs(Math.sin(t * Math.PI * 2)) * 18; // al ritmo (2 golpes por segundo)
  return (
    <Scene id="E11">
      <StudioBG />
      <Cam zoom={1 + (active >= 0 ? Math.max(0, 0.06 - (t - PRESS[active]) * 0.12) : 0)}>
        {/* botones */}
        <div style={{position: 'absolute', left: 110, top: 120, display: 'flex', flexDirection: 'column', gap: 44}}>
          {BUTTONS.map((b, i) => {
            const k = t - PRESS[i];
            const pressed = k >= 0 && k < 0.18;
            const on = final || active === i;
            const appear = Math.min(1, Math.max(0, (t - i * 0.12) / 0.25));
            return (
              <div key={i} style={{transform: `translateX(${(1 - appear) * -900}px) scale(${on ? 1.06 : 0.96})`, opacity: on || active < i ? 1 : 0.6}}>
                <div
                  style={{
                    width: 760,
                    height: 190,
                    borderRadius: 60,
                    background: b.color,
                    border: `10px solid ${C.outline}`,
                    boxShadow: pressed ? `0 4px 0 ${C.outline}` : `0 22px 0 ${C.outline}`,
                    transform: `translateY(${pressed ? 18 : 0}px)`,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 30,
                    padding: '0 50px',
                    filter: on ? 'brightness(1.12)' : 'none',
                  }}
                >
                  <span style={{fontSize: 110}}>{b.icon}</span>
                  <span style={{fontFamily: TITLE, fontSize: 92, color: '#fff', WebkitTextStroke: `6px ${C.outline}`, paintOrder: 'stroke fill', paddingTop: 16}}>{b.label}</span>
                </div>
              </div>
            );
          })}
        </div>
        <Pos x={1400} y={1150 - (final ? bounce : 0)}>
          <Loria
            width={600}
            headphones={active === 0 || final}
            cap={active === 1 || final}
            glasses={active === 2 || final}
            beakOpen={talkAmount(t, 'E11', 'LORIA')}
            blink={blinkAt(t)}
            wingR={-20 + Math.sin(t * Math.PI * 4) * 12}
            wingL={final ? -60 : -10}
            headTilt={Math.sin(t * Math.PI * 2) * 5}
            lookX={-0.6}
          />
        </Pos>
        {/* tarjetica de pronunciacion en Ejercicios */}
        {active === 1 && (
          <div style={{position: 'absolute', left: 1080, top: 90, transform: `scale(${Math.min(1, (t - PRESS[1] - 0.3) / 0.2)}) rotate(-4deg)`, background: C.cream, border: `7px solid ${C.outline}`, borderRadius: 26, padding: '16px 28px', fontFamily: BODY, fontWeight: 800, fontSize: 46, color: C.outline, boxShadow: `0 8px 0 ${C.outline}`}}>
            🔊 Escucha cómo se pronuncia
          </div>
        )}
      </Cam>
      {PRESS.map((p, i) => (
        <Sparkle key={i} at={p + 0.1} x={1450} y={330} size={120} />
      ))}
      <SlamText at={FINAL + 0.1} size={150} color={C.yellow} y={-390} x={340} rot={-6}>
        ¡TÚ ELIGES!
      </SlamText>
      <Confetti at={FINAL + 0.1} count={100} />
      {PRESS.map((p, i) => (
        <React.Fragment key={i}>
          <Sfx name="click" at={p} />
          <Sfx name="pop" at={p + 0.1} />
          <Sfx name="sparkle" at={p + 0.12} volume={0.5} />
        </React.Fragment>
      ))}
      <Sfx name="stamp" at={FINAL + 0.1} />
      <Sfx name="fanfare" at={FINAL + 0.2} volume={0.5} />
    </Scene>
  );
};
