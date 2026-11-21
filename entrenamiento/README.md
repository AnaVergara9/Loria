# Entrenamiento del evaluador de pronunciación

`evaluador_pronunciacion_colab.py` es el cuaderno de Google Colab (exportado como .py) con el que se entrenó el evaluador que usa el bot. Produce los dos archivos que carga `pronunciacion.py`, `evaluador_pronunciacion.pt` y `normalizacion.npz`, que siempre van juntos.

**Cómo volver a entrenarlo.** En Colab, sube el archivo (Archivo → Subir cuaderno, o copia las celdas), elige un entorno con GPU, quita el `#` de la línea `!pip install` y ejecuta todo. Al final, descarga **los dos** archivos y reemplázalos en la carpeta del proyecto.

## Qué hace

1. **Datos.** Usa [speechocean762](https://huggingface.co/datasets/mispeech/speechocean762): 5.000 frases en inglés leídas por hablantes no nativos (2.500 de entrenamiento y 2.500 de prueba). Expertos calificaron cada fonema de 0 a 2 y cada frase de 0 a 10.
2. **Fonemas esperados.** El dataset trae los fonemas en ARPAbet. Se pasan a los símbolos IPA del modelo wav2vec2 con la tabla `ARPA2IPA`, que es la misma que usa `generar_fonemas.py` para las frases del bot. Por eso las frases del banco tienen los mismos símbolos con los que se entrenó la red.
3. **Características acústicas.** Se pasa el audio por `facebook/wav2vec2-lv-60-espeak-cv-ft`, que da la probabilidad de cada fonema en cada instante. Por cada fonema esperado se calculan cuatro valores: probabilidad máxima, media, desviación y un "GOP aproximado" (su máximo menos el promedio del mejor fonema en cada instante).
4. **Red.** Es una BiLSTM de 2 capas que recibe el fonema (como embedding) más esas 4 características. Tiene dos salidas: el puntaje de cada fonema (0 a 2) y el de la frase (0 a 10).
5. **Entrenamiento.** El cuaderno tiene dos bloques; el que vale es el segundo:
   - El primer bloque es una versión inicial: 15 épocas, sin normalizar.
   - El segundo es el que produce los archivos que usa el bot:
     - Normaliza las características.
     - Separa 250 frases de entrenamiento como validación.
     - Entrena 30 épocas con Adam (lr 1e-3, weight decay 1e-4) y pérdida MSE de los fonemas + 0,5 × la de la frase.
     - Guarda la época con mejor Pearson por fonema en validación.
     - Mide el conjunto de prueba **una sola vez**, al final.
6. **Métricas.**
   - Correlación de Pearson con los puntajes de los expertos en el conjunto de prueba. Resultado: **0,609 por frase y 0,353 por fonema**. La referencia del modelo GOPT es 0,740 y 0,610.
   - Qué tan seguido los 2 fonemas peor calificados son errores reales, comparado con elegirlos al azar.
   - Opcional, para el informe: con `SOLO_IDENTIDAD = True`, la red solo ve qué fonema es, sin audio. Sirve como línea base para medir cuánto aportan las características acústicas.

## Por qué el puntaje por fonema es débil

Las cuatro características se calculan sobre **todo el audio**, no sobre el pedazo donde se dijo cada fonema. Por eso un fonema que aparece dos veces en la frase recibe los mismos valores las dos veces, y la red no puede saber cuál de los dos se pronunció mal. La mejora planeada es calcular el GOP de cada fonema en su propio segmento, con alineación forzada CTC.
