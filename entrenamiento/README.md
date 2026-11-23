# Entrenamiento del evaluador de pronunciación

| Archivo | Qué es |
|---|---|
| `entrenar_evaluador.py` | Entrena el evaluador que usa el bot hoy y lo compara con las versiones anteriores. |
| `resultados_etapa8.json` | Todos los números del entrenamiento que produjo el modelo actual (Colab, GPU T4). |

El primer evaluador (versión 1) se entrenó con un cuaderno de Colab que ya no está en el proyecto; queda en el historial de git. Este script lo vuelve a entrenar como línea de comparación, con el mismo protocolo.

## Cómo volver a entrenarlo

Necesita, además de lo del bot: `pip install pyarrow scipy huggingface_hub soundfile`. No están en `requirements.txt` porque el bot no los usa.

- **En Colab (con GPU, unos 20 minutos):**
  1. Sube `entrenar_evaluador.py` y `tutor/rasgos_pronunciacion.py`, los dos a `/content`.
  2. Ejecuta `!python entrenar_evaluador.py`.
  3. Descarga `/content/evaluador_pronunciacion.pt` y `/content/resultados_etapa8.json` antes de cerrar Colab, porque al reiniciarse borra los archivos.
- **En el computador:** `python entrenamiento/entrenar_evaluador.py`. Sin GPU tarda varias horas, casi todas en pasar los 5.000 audios por wav2vec2.

Después, el `.pt` va en `datos/` y el `.json` en esta carpeta. El `.pt` trae adentro su normalización y sus variantes; no hace falta ningún otro archivo.

## Datos y protocolo

- **Datos.** Se usa [speechocean762](https://huggingface.co/datasets/mispeech/speechocean762): 5.000 frases en inglés leídas por hablantes no nativos, 2.500 para entrenar y 2.500 para la prueba. Expertos calificaron cada fonema de 0 a 2 y cada frase de 0 a 10.
- **Fonemas.** El dataset los trae en ARPAbet. Se pasan a los símbolos IPA de wav2vec2 con la misma tabla `ARPA2IPA` que usa `scripts/generar_fonemas.py` para las frases del bot.
- **Protocolo.** Es el mismo del cuaderno original, para que la comparación sea justa:
  - semilla 0;
  - 250 frases de entrenamiento apartadas como validación;
  - 30 épocas con Adam (lr 1e-3, weight decay 1e-4);
  - pérdida: MSE de los fonemas + 0,5 × MSE de la frase;
  - se guarda la época con mejor Pearson por fonema **en validación**;
  - la versión ganadora también se elige por validación;
  - el conjunto de prueba se mide una sola vez, al final.
- **Red.** Una BiLSTM de 2 capas que recibe el fonema (como embedding) más sus características acústicas. Da un puntaje por fonema (0 a 2) y uno por frase (0 a 10).

## Qué cambió: características por tramo (v2)

**El problema de la versión 1.** wav2vec2 dice qué tan probable es cada fonema en cada instante del audio (cada 20 ms). La versión 1 resumía esas probabilidades sobre **todo el audio** con cuatro valores: máximo, media, desviación y un GOP global. Si un fonema aparece dos veces en la frase, las dos veces recibe los mismos números, y la red no puede saber cuál se dijo mal.

**La solución, en `tutor/rasgos_pronunciacion.py`:**

1. **Alineación forzada CTC.** Ya se sabe qué fonemas debían decirse y en qué orden. Con el algoritmo de Viterbi se busca el reparto más probable de los instantes del audio entre esos fonemas. El resultado es el tramo de audio de cada fonema.
2. **Siete características medidas en el tramo de cada fonema:**

   | Característica | Qué mide |
   |---|---|
   | `lpp` | Probabilidad promedio del fonema esperado en su tramo. |
   | `gop` | Cuánto pierde el fonema esperado frente al mejor competidor en cada instante (0 si gana). |
   | `max_tramo` | Su mejor instante. |
   | `duracion` | Cuánto duró el tramo (en escala logarítmica). |
   | `coincide`, `cambiado`, `omitido` | Resultado de comparar con lo que wav2vec2 reconoce libremente, sin saber la frase. Se alinean las dos secuencias, como en una distancia de edición. |

3. **Variantes de notación.** wav2vec2 escribe algunos sonidos correctos con otro símbolo: por ejemplo `iː` en lugar de `i`, o `ɐ` en lugar de `ə`. Si no se tuviera en cuenta, un sonido bien dicho parecería un error. Las variantes se aprenden de los datos de entrenamiento:
   - un símbolo cuenta como variante si es el más probable en al menos el 10 % de los fonemas que los expertos calificaron como bien dichos, con al menos 20 casos;
   - **nunca puede ser otro fonema del inglés.** Por eso `z` no se acepta como `ð` aunque salga en el 22 % de los casos: decir "zis" en lugar de "this" es justo el error que queremos detectar.

   Variantes encontradas: `i→iː`, `u→uː`, `ʊ→uː`, `ɑ→ɑːɹ, ɑː`, `ɔ→ɔːɹ, ɔː`, `ə→ɐ`, `ɚ→ɜː`, `ʌ→ɑː`, `h→x`.

## Resultados (conjunto de prueba, 2.500 frases)

Medida principal: la correlación de Pearson con los puntajes de los expertos. La columna "2 peores = error" dice qué tan seguido los 2 fonemas peor calificados de cada frase son errores reales según los expertos. Elegirlos al azar acierta el 20,4 %.

| Versión | Pearson fonema | Pearson frase | 2 peores = error |
|---|---|---|---|
| Solo identidad (sin audio, línea base) | 0,068 | 0,162 | 26,3 % |
| v1 (primer evaluador, reproducido) | 0,356 | 0,616 | 42,8 % |
| v2 (por tramo) | 0,592 | 0,650 | 49,3 % |
| **v1 + v2 (elegida por validación, la usa el bot)** | **0,593** | **0,676** | **51,3 %** |
| Referencia GOPT (Gong et al., 2022) | ~0,61 | ~0,74 | — |

- **El protocolo se reprodujo bien.** La versión 1 entrenada con este script da 0,356 y 0,616; el primer evaluador daba 0,353 y 0,609.
- **El Pearson por fonema subió de 0,356 a 0,593**, casi el de GOPT, un modelo publicado más grande. Sin red, una sola característica ya mide más que toda la versión 1: `lpp` sola da 0,472.
- **Los 2 sonidos que el bot señala son errores reales el 51 % de las veces**, frente al 43 % de antes y al 20 % de elegirlos al azar.
- **El puntaje de la frase mejoró menos** (de 0,616 a 0,676) y sigue por debajo de GOPT (0,74). GOPT usa características de fluidez y entonación que aquí no se calculan.
- **Repetibilidad.** El mismo script en un computador sin GPU dio casi lo mismo: 0,597 por fonema y 0,642 por frase. Las diferencias son pequeñas y vienen de cómo la GPU redondea los cálculos.
- **Qué se oyó.** El bot dice el símbolo más fuerte en el tramo del fonema. Es una pista útil para explicar el error, pero no un diagnóstico perfecto: en voz con acento, wav2vec2 a veces escribe símbolos de otros idiomas.

## Límites honestos

- Los expertos de speechocean762 calificaron a hablantes de chino mandarín, no a hispanohablantes. Los errores típicos de los hispanohablantes, como "estation" o "zis", sí aparecen, pero con otra frecuencia.
- El evaluador compara contra la pronunciación del diccionario CMU, que es inglés americano. Un acento británico correcto puede salir un poco más bajo.
- **Prueba con voces sintéticas de Windows en "Where is the bus station?":**
  - La voz en inglés saca 8,8 y no marca nada.
  - La voz en español leyendo inglés saca 7,7 y marca la `ʃ` de "station" (sonó como una `s`) y la `s` de "bus" (sonó como una `l`).
  - Una frase mal escrita a propósito ("Where is de bus estation?") con la voz en inglés sacó 8,7. Esa voz la pronuncia casi como la frase correcta, así que no sirve como prueba de errores. Para eso hace falta grabar voces reales.
