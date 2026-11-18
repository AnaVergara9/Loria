import React from 'react';
import {Img, staticFile, useCurrentFrame} from 'remotion';
import {C} from '../theme';
import {BODY, TITLE} from '../fonts';

export const BOT = '@loriaabot';

/** Codigo QR (lleva a t.me/loriaabot) con el usuario del bot debajo. */
export const QRBox: React.FC<{size?: number; blink?: boolean}> = ({size = 300, blink = false}) => {
  const f = useCurrentFrame();
  const on = !blink || f % 20 < 14;
  return (
    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14}}>
      <div style={{background: '#fff', border: `9px solid ${C.outline}`, borderRadius: 28, padding: 14, boxShadow: `0 12px 0 ${C.outline}`}}>
        <Img src={staticFile('qr-loriaabot.png')} style={{width: size, height: size, display: 'block'}} />
      </div>
      <div
        style={{
          fontFamily: TITLE,
          fontSize: size * 0.2,
          color: on ? C.yellow : '#fff',
          WebkitTextStroke: `${size / 50}px ${C.outline}`,
          paintOrder: 'stroke fill',
          background: '#4F8FCB',
          border: `8px solid ${C.outline}`,
          borderRadius: 999,
          padding: `${size * 0.04}px ${size * 0.1}px 0`,
        }}
      >
        {BOT}
      </div>
      <div style={{fontFamily: BODY, fontWeight: 800, fontSize: size * 0.12, color: '#fff', textShadow: `0 3px 0 ${C.outline}`}}>Búscala en Telegram</div>
    </div>
  );
};
