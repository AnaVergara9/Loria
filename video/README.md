# Video promocional de Loria (Remotion)

Video animado de **3:00 exactos**, en **1920x1080 a 30 cuadros por segundo**, hecho con código.
Remotion es como un editor de video donde cada escena es un archivo: cambias el archivo y el video cambia.

---

## 1. Lo que necesitas instalar (una sola vez)

1. **Node.js** versión 18 o más nueva: descárgalo de https://nodejs.org (botón "LTS") e instálalo como cualquier programa.
2. Abre una terminal **dentro de la carpeta `video`** (en Windows: abre la carpeta, escribe `cmd` en la barra de direcciones y presiona Enter).
3. Instala las piezas del proyecto:

```bash
npm install
```

Esto crea la carpeta `node_modules` (es grande, no la subas a ningún lado).

## 2. Ver el video mientras trabajas

```bash
npm run studio
```

Se abre el navegador con el **Remotion Studio**:
- A la izquierda eliges **LoriaPromo** (el video completo) o una escena suelta en la carpeta **Escenas** (E00, E01...).
- La barra de abajo es la línea de tiempo: dale play o arrastra para moverte.
- Si cambias un archivo y lo guardas, el Studio se actualiza solo.

## 3. Exportar a MP4

```bash
npm run render
```

El video queda en `video/out/loria-promo.mp4`. Tarda varios minutos (depende de tu computador).

Para exportar solo una escena (por ejemplo la E05):

```bash
npx remotion render E05 out/escena-05.mp4
```

## 4. Agregar las voces

1. Graben las frases de `GUION_VOCES.md` (están numeradas por escena, con duración y cómo decirlas).
2. Guarden cada audio en `public/voces/` con el **nombre exacto** del archivo. Ejemplo: `e05_03.mp3`. También sirven `.wav` y `.m4a`.
3. Listo: el video las pone solas en el momento justo. Las que falten se quedan solo con subtítulo.

Los **subtítulos** siempre aparecen (así el video se entiende sin sonido). Si cambian una frase al grabarla,
cambien también el texto en `src/dialogue.json` para que el subtítulo coincida.

## 5. Agregar la música

Pongan **un** archivo de música libre de derechos (mp3, wav o m4a) dentro de `public/music/`.
Suena de fondo en todo el video, bajita. Si quieren cambiar el volumen, en `src/Video.tsx` cambien
`<Music />` por `<Music volume={0.3} />` (0 = nada, 1 = máximo).

Sitios con música libre de derechos: YouTube Audio Library, Pixabay Music o Free Music Archive (revisen que la licencia permita usarla).

## 6. Efectos de sonido

Están en `public/sfx/` (pop, whoosh, buzzer, ding, rayón de disco, sirena, rebobinado, aplausos...).
Los creó el programa `tools/make_sfx.py`. Si consiguen uno mejor, **reemplacen el archivo con el mismo nombre**.

---

## Qué hace cada archivo

| Archivo | Para qué sirve |
|---|---|
| `package.json` | La lista de piezas que instala `npm install` y los atajos `npm run studio` / `npm run render`. |
| `remotion.config.ts` | Ajustes de exportación (formato de imagen, sobrescribir el video). |
| `src/index.ts` | El punto de arranque: le dice a Remotion dónde están los videos. |
| `src/Root.tsx` | "Registra" los videos que ves en el Studio: el completo, cada escena y las pruebas. |
| `src/Video.tsx` | Arma el video completo poniendo las escenas una detrás de otra, y pone la música. |
| `src/timeline.ts` | **El orden y la duración de cada escena.** Si alargas una, acorta otra para que el total siga siendo 180 segundos. |
| `src/dialogue.json` | **Todos los diálogos**: quién habla, qué dice, cuándo empieza y cuánto dura. De aquí salen los subtítulos, las voces, el movimiento de la boca y `GUION_VOCES.md`. |
| `src/theme.ts` | Los colores de Loria. Cambias uno aquí y cambia en todo el video. |
| `src/fonts.ts` | Carga las letras guardadas en `public/fonts`. |
| `src/characters/Loria.tsx` | **Loria como títere por piezas**: abre el pico, parpadea, aletea, gira la cabeza, y se pone gafas, audífonos o gorra. El libro es opcional y su texto se puede cambiar. |
| `src/characters/Person.tsx` | Los personajes humanos (Camila, el jefe, el mesero, Andrés, doña Marta, el niño...). Al final del archivo está el "elenco" con la ropa y el pelo de cada uno. |
| `src/components/core.tsx` | Herramientas que usan todas las escenas: subtítulos, voces, efectos de sonido, cámara (zoom), textos que entran de golpe, sellos, confeti y destellos. |
| `src/components/effects.tsx` | Efectos de televisión: blanco y negro con rayas, estática, rebobinado, barridos, líneas de velocidad y el rótulo "Dramatización". |
| `src/components/Studio.tsx` | El estudio de teletienda (rayos, bombillos, focos), el mostrador, el logo LORIA y el lema. |
| `src/components/Sets.tsx` | Los escenarios: oficina, café en París, aeropuerto, videollamada, bus, cocina, cuarto, cama y las ondas de sonido. |
| `src/components/Phone.tsx` | El celular con el chat de Telegram: mensajes con error tachado, corrección en verde y notas de voz. |
| `src/components/EndCard.tsx` | El código QR (lleva a t.me/loriaabot) y el usuario **@loriaabot**. |
| `src/scenes/E00_Gancho.tsx` ... `E14_Final.tsx` | **Una escena por archivo.** Puedes cambiar una sin tocar las demás. Arriba de cada archivo hay un comentario con lo que pasa en la escena. |
| `src/scenes/index.ts` | Conecta cada escena (E00, E01...) con su archivo. |
| `public/` | Archivos que usa el video: letras, efectos de sonido, QR, y las carpetas `voces/` y `music/` para sus audios. |
| `tools/make_sfx.py` | Vuelve a crear los efectos de sonido. |
| `tools/voice_list.py` | Vuelve a crear `GUION_VOCES.md` si cambian los diálogos. |
| `tools/stills.mjs` / `tools/sheet.py` | Sacan imágenes de prueba de varias escenas a la vez (para revisar sin ver todo el video). |
| `GUION_VOCES.md` | La lista numerada de frases para grabar. |

## Las escenas

| # | Tiempo | Escena | Qué pasa |
|---|---|---|---|
| E00 | 0:00–0:03 | Gancho | Loria a color: "¿Hablas inglés? …A ver." Aprieta el control y la tele pasa a blanco y negro. |
| E01 | 0:03–0:10 | La entrevista | "How old are you?" / "I have 20 years!" → congelado, buzzer y sello ¡ERROR! |
| E02 | 0:10–0:20 | Montaje de fallos | Café en París, aeropuerto y videollamada; pantalla partida en tres con X rojas. |
| E03 | 0:20–0:28 | La pregunta | Camila debajo de la mesa; preguntas que entran de golpe; "¿PENA DE HABLAR?" llena la pantalla; estática. |
| E04 | 0:28–0:36 | Llega Loria | Explosión de color, confeti; Loria aterriza en el mostrador; logo que rebota y lema. |
| E05 | 0:36–0:52 | El chiste del loro (1/3) | Loria repite "I have 20 years!", rayón de disco, silencio, gafas y corrección en el chat. |
| E06 | 0:52–1:06 | Escríbele | Celular gigante: una corrección en inglés y una en francés, con contador +1, +2. |
| E07 | 1:06–1:10 | ¡Pero espera! | Luces rojas, sirena, a Loria se le esponjan las plumas. |
| E08 | 1:10–1:38 | Notas de voz | Bus, cocina y pijama; "tree" → "three" (pronunciación); "¡Pizza! ¡Pizza!" (2/3) → "I ate pizza". |
| E09 | 1:38–1:42 | Rebobinado | El video se rebobina y frena: "¿Y para los más pequeños?" |
| E10 | 1:42–2:08 | Modo niños | Estilo crayón en hoja de cuaderno: huevo → pollito → loro → gafas → gorra, con estrellas. |
| E11 | 2:08–2:22 | Los botones | Conversar (audífonos), Ejercicios (gorra), Corregir (gafas): "¡Tú eliges!" |
| E12 | 2:22–2:40 | Testimonios | Andrés, doña Marta y Camila (que consiguió el trabajo), con "Dramatización". |
| E13 | 2:40–2:48 | La oferta | "$99.999" tachado → ¡GRATIS!; QR y @loriaabot. |
| E14 | 2:48–3:00 | Final (3/3) | "I am 20 years old!" / "Loria… tú no tienes 20 años." / "Tengo dos semanas." Logo, lema y QR. |

## Cambios comunes

- **Cambiar un texto en pantalla**: búscalo en el archivo de su escena (`src/scenes/E..`) y cámbialo.
- **Cambiar un diálogo o subtítulo**: en `src/dialogue.json`. Luego `python3 tools/voice_list.py` para actualizar la lista de grabación.
- **Mover cuándo pasa algo dentro de una escena**: los tiempos están en segundos dentro de cada escena (por ejemplo `at={2.3}` = a los 2,3 segundos de esa escena).
- **Cambiar la duración de una escena**: en `src/timeline.ts`, y ajusta otra para que el total siga en 180.
