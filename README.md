# Parley (bot Loria 🦜)

Bot de Telegram para practicar inglés y francés por texto y por notas de voz. Proyecto final del curso de Agentes Inteligentes, Universidad de Ibagué.

---

## Requisitos

- Windows con PowerShell.
- Python 3.12 o superior y Git (se comprueban con `python --version` y `git --version`). Probado con Python 3.14.
- Conexión a internet.

## Instalación

**1. Descargar el código.**

```powershell
git clone https://github.com/TU_USUARIO/Parley.git
cd Parley
```

**2. Crear y activar el entorno virtual.**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Debe aparecer `(.venv)` al inicio de la línea. Si Windows bloquea la activación, ejecuta una sola vez lo siguiente y repite el paso.

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**3. Instalar las librerías.**

```powershell
pip install -r requirements.txt
```

## Configuración

Copia `.env.example` como `.env` en la carpeta del proyecto y llena las claves, sin comillas ni espacios alrededor del `=`.

```
TELEGRAM_TOKEN=token_del_bot_del_grupo
GEMINI_API_KEY=tu_clave_de_gemini
GROQ_API_KEY=tu_clave_de_groq
```

- **`TELEGRAM_TOKEN`.** Es el token del bot del grupo. Se pide por mensaje privado a quien lo creó y nunca se sube a GitHub.
- **`GEMINI_API_KEY`.** Cada integrante crea la suya en [aistudio.google.com](https://aistudio.google.com), con **Crear clave de API** y el proyecto gratuito.
- **`GROQ_API_KEY`.** Se crea gratis en [console.groq.com/keys](https://console.groq.com/keys). Es opcional, pero sin ella el bot no tiene respaldo cuando Gemini está saturado.

## Ejecución

```powershell
python bot.py
```

La primera vez tarda más porque descarga los modelos de Whisper (unos 150 MB) y de pronunciación (más de 1 GB). Los avisos sobre "symlinks" y "unauthenticated requests" son normales y no afectan. Cuando la terminal quede quieta sin errores en rojo, el bot está funcionando. Para apagarlo, presiona `Ctrl + C`.

Como el bot es uno solo, **solo una persona puede tenerlo corriendo a la vez**. Si dos lo ejecutan al mismo tiempo con el mismo token, los mensajes se pierden.

## Cómo se usa (menú con botones)

Después de `/start` y de elegir el perfil, todo se maneja con botones. `/menu` vuelve a mostrar el menú en cualquier momento.

| Botón | Qué hace |
|---|---|
| 💬 Conversar | Charla libre en el idioma elegido. Loria corrige cada frase y sigue la conversación (lo decide el agente). |
| 🎯 Ejercicios | ✏️ Escribir (completar o traducir) o 🎙 Pronunciación (solo en inglés). |
| 📝 Corregir un texto | Solo corrección, sin conversación: el bot llama directamente a `corregir_gramatica`. |
| 📈 Mi progreso | Nivel, aciertos, errores más comunes y qué le falta para subir. |
| 🌐 Cambiar idioma | Inglés o francés. Se guarda y decide el idioma de los ejercicios y de la conversación. |
| 🗑 Borrar mis datos | Pide confirmación y borra todo, también la memoria de la conversación. |

Debajo de cada respuesta aparecen botones para seguir. Durante un ejercicio: 💡 No sé, ⏭ Otro y ❌ Salir. Después de un ejercicio: ➡️ Otro ejercicio, 📈 Mi progreso y 🏠 Menú. Al tocar un botón, el mensaje pierde sus botones, para que no queden botones viejos activos. "No sé" de un ejercicio que ya no está activo no muestra la respuesta del ejercicio nuevo.

**Botones y agente.** Los botones son acciones fijas: el bot llama la herramienta MCP directamente, sin preguntarle al modelo de lenguaje, y así no gastan cuota. Lo que el estudiante escribe o dice en "Conversar", y las respuestas a los ejercicios, van al agente ReAct, que decide qué herramienta usar.

Los comandos `/practicar`, `/ejercicio`, `/progreso`, `/cancelar`, `/borrar` y `/traza` siguen funcionando como atajos (útiles para la demo), pero no aparecen en la lista de comandos de Telegram.

## Cadena de respaldo de modelos

Cada mensaje se intenta con los modelos en este orden, y se pasa al siguiente si uno falla o tarda más de 12 segundos:

1. `gemini-3.5-flash` (principal)
2. `gemini-3.7-flash` y `gemini-3.8-flash` (respaldo)
3. `openai/gpt-oss-120b`, `qwen/qwen3.8-27b` y `openai/gpt-oss-20b` en Groq (último respaldo)

Un modelo que falla queda en pausa 60 segundos (10 minutos si la clave es inválida o el modelo no existe, y hasta que se reinicie la cuota si se agotó el límite diario), para no hacer esperar al usuario con un modelo caído. Todo el mensaje tiene como máximo 60 segundos. Si todos fallan, el usuario recibe un mensaje amable pidiéndole que intente en un minuto. El orden y los tiempos se pueden cambiar en `.env` (ver `.env.example`).

En la consola, cada mensaje deja líneas como estas:

```
WARNING MODELO | agente: gemini/gemini-3.5-flash FALLÓ en 0.6 s -> saturado o límite por minuto alcanzado (429) (en pausa 60 s)
INFO    MODELO | agente: respondió groq/openai/gpt-oss-120b en 1.4 s (antes fallaron 1)
```

Con `/traza` en el chat también se ve qué modelo respondió y qué herramientas usó el agente.

**Límites gratuitos (revisados el 20/11/2026).** Gemini permite solo **20 peticiones por día por modelo** en el plan gratuito, y cada mensaje del bot usa de 2 a 4 peticiones. Con tres modelos de Gemini alcanza para unos 15 a 30 mensajes al día; después responde Groq. Groq permite unas 1.000 peticiones al día, pero solo 8.000 tokens por minuto por modelo, y también tiene un **tope de tokens por día**: en las pruebas de desarrollo, `gpt-oss-120b` lo agotó tras muchos mensajes seguidos y quedó en pausa unos minutos (el bot pasa solo al siguiente modelo). Conviene no hacer pruebas largas el día de la demo. Si un proveedor corta una respuesta a la mitad (por límite de longitud), el bot la descarta y responde el siguiente modelo, en vez de mandar media frase. El uso actual se ve en [ai.dev/rate-limit](https://ai.dev/rate-limit) y en [console.groq.com/settings/limits](https://console.groq.com/settings/limits).

**Probar los modelos:**

```powershell
python scripts/probar_modelos.py   # prueba cada modelo de la cadena y luego la cadena completa
```

**Mostrar el paso a Groq en una demo** (simula que Gemini está caído, solo mientras esa terminal esté abierta):

```powershell
$env:LLM_SIMULAR_FALLO="gemini"; python bot.py
```

## Servidor MCP (herramientas del agente)

Las capacidades del tutor (corregir, consultar el perfil, generar y evaluar ejercicios) están en un **servidor MCP** propio, `herramientas_mcp/servidor_mcp.py`, hecho con la librería oficial `mcp`. El bot es el **cliente MCP**: al arrancar lanza el servidor como un proceso aparte, le pide la lista de herramientas y se la muestra al modelo de lenguaje. El modelo decide cuál usar y el bot se la pide al servidor.

```
Telegram -> bot.py -> agente/agente.py --(¿qué herramienta?)--> Gemini / Groq
                         |                              (modelos_lenguaje/: cadena de respaldo)
                         +--(ejecútala)--> agente/cliente_mcp.py ==stdio==> herramientas_mcp/servidor_mcp.py
                                                                                -> tutor/ (db, ejercicios, progreso, pronunciación)
```

No hay que ejecutar el servidor a mano: `python bot.py` lo lanza solo. Herramientas: `corregir_gramatica`, `consultar_perfil`, `consultar_nivel`, `cambiar_nivel`, `generar_ejercicio_texto`, `revisar_respuesta`, `generar_ejercicio_pronunciacion`, `evaluar_pronunciacion` y `cancelar_ejercicio`.

El id del usuario, la ruta del audio y lo que entendió Whisper los pone el bot, nunca el modelo: el cliente los oculta de lo que ve el modelo y los agrega al llamar. Así el modelo no puede pedir los datos de otro usuario.

**Controles sobre el agente.** El modelo de lenguaje decide, pero el código revisa estas decisiones:

- **Verificador.** Si el estudiante escribe una frase en inglés o francés y el modelo responde sin usar ninguna herramienta (por ejemplo "¡Frase perfecta!" sin corregirla), el bot le pide una vez que use la herramienta que corresponde. Para saber si el mensaje es una frase en inglés o francés, el bot cuenta palabras frecuentes de cada idioma, sin gastar el modelo. En la consola aparece `VERIFICADOR | ...`.
- **Los ejercicios los escribe el código**, copiados de la herramienta (ver "Ejercicios").
- **No hay doble registro:** con un ejercicio de texto activo no se puede usar `corregir_gramatica`.

En la consola se ve qué herramienta eligió el modelo en cada turno. Las líneas que empiezan con `[servidor MCP]` vienen del servidor:

```
INFO HERRAMIENTA | paso 1: groq/openai/gpt-oss-120b eligió corregir_gramatica({"texto": "I has two dogs"})
[servidor MCP] INFO ejecutando corregir_gramatica
INFO HERRAMIENTA | paso 2: groq/openai/gpt-oss-120b responde sin herramienta
INFO TURNO | usuario 123 | respondió groq/openai/gpt-oss-120b | herramientas: corregir_gramatica
```

**Probar el servidor MCP sin Telegram:**

```powershell
python scripts/probar_mcp.py      # lanza el servidor, muestra sus herramientas y llama algunas
```

## Nivel y progreso

Cada estudiante tiene un nivel por idioma (inglés y francés por separado) en la escala MCER: A1, A2, B1, B2, C1. Se guarda en `datos/parley.db` y se ve con `/progreso`, o preguntándole al bot "¿cuál es mi nivel?".

Cada frase que el estudiante practica (escrita o en nota de voz) y cada ejercicio de texto que responde se guardan como un intento. Al corregirla, el modelo indica también el **tipo de cada error** (gramática, vocabulario, ortografía o puntuación) y el **nivel que demuestra la frase** (por ejemplo, "I like dogs" es A1 y "If I had known, I would have come" es B2). Las reglas están en `tutor/progreso.py`:

1. **Ubicación inicial:** con las primeras 5 frases de un idioma se calcula el nivel de partida (la mediana del nivel de las frases correctas, un nivel menos si acertó menos del 60 %).
2. **Revisión:** se miran las últimas 10 frases, y solo cuando hay al menos 8 desde el último cambio. Así un solo mensaje nunca cambia el nivel.
   - **Sube** si al menos el 80 % son correctas y al menos la mitad son frases correctas de su nivel o más. Escribir bien frases fáciles no basta para subir.
   - **Baja** si el 40 % o menos son correctas.
3. **Correcta** quiere decir sin errores de gramática ni de vocabulario. Los errores de ortografía y puntuación se muestran en las estadísticas, pero no hacen incorrecta la frase.
4. Los **ejercicios de texto** cuentan igual que las frases, con el nivel del ejercicio. Así, resolver bien ejercicios de su nivel también lo hace subir.
5. La **pronunciación** (solo inglés) se guarda en el progreso con su promedio, pero no mueve el nivel MCER: el evaluador mide sonidos, no dominio del idioma.
6. El estudiante puede pedir que le cambien el nivel ("ponme en B2"). El modelo solo lo hace si se lo piden.

Según el nivel cambian las explicaciones de las correcciones (más simples en A1 y A2, con términos gramaticales en B2 y C1), el vocabulario con que Loria conversa y los ejercicios que propone. Cuando el nivel cambia, Loria lo avisa en la conversación. "Borrar mis datos" elimina también el nivel y el historial de intentos.

## Ejercicios

El banco está en `datos/ejercicios.json` y se puede ampliar sin tocar código. Cada ejercicio tiene un **perfil** (adulto o niño) y un **nivel** (A1 a C1). Loria propone ejercicios del nivel del estudiante o uno más fácil, los recorre todos en orden aleatorio antes de repetir y nunca repite el mismo dos veces seguidas.

| | Adulto inglés | Adulto francés | Niño inglés |
|---|---|---|---|
| Pronunciación (leer en voz alta) | 30 (6 por nivel) | no hay | 18 (A1 a B1) |
| Texto: completar y traducir | 30 (6 por nivel) | 30 (6 por nivel) | 13 (A1 a B1) |
| Texto: elegir con botones | no hay | no hay | 14 (A1 a B1) |

- **Completar** (🎯 Ejercicios → ✏️ Escribir, o "dame un ejercicio"): una frase con un espacio `___`. Se acepta la palabra sola o la frase completa, sin importar mayúsculas ni puntuación. Si solo falla una tilde, cuenta como correcta, pero se le muestra como error de ortografía.
- **Traducir**: una frase en español. Si la respuesta coincide con una de las traducciones de referencia, se revisa sin gastar el modelo de lenguaje. Si es distinta (por ejemplo, "I've got two brothers" en lugar de "I have two brothers"), la juzga el modelo de lenguaje, porque una traducción puede estar bien de muchas formas.
- **Pronunciación** (🎯 Ejercicios → 🎙 Pronunciación): solo en inglés. En francés no hay evaluación de pronunciación porque no existen suficientes corpus públicos para entrenar un evaluador confiable. Los niños solo tienen ejercicios en inglés. Cada nota de voz pasa por tres revisiones:
  1. **¿Leyó la frase del ejercicio?** Whisper transcribe la nota de voz y se compara letra por letra con la frase. Si el parecido es menor que 0,45, no se califica y se le pide leer la frase. Con ese límite, las frases mal pronunciadas ("I sink de wedder is nais") dan 0,56 o más, y las frases distintas o en español dan 0,35 o menos.
  2. **¿Qué tan bien la pronunció?** El evaluador entrenado (wav2vec2 + BiLSTM) da el puntaje. Si Whisper no reconoció varias palabras de la frase, el puntaje tiene un tope: 4 + 6 × (fracción de palabras entendidas). Así, una frase que casi no se entiende no puede sacar 9, y Loria le dice cuáles palabras no se entendieron.
     - **Con acento fuerte, Whisper suele creer que el audio está en español** y escribe otra cosa: con una voz española leyendo "Where is the bus station?" escribió "¿Cuál es de bustesian?". Por eso, si no detecta inglés, el bot transcribe una segunda vez forzando inglés, y las palabras entendidas se cuentan con esa versión. La revisión 1 sigue usando la primera transcripción: forzar inglés siempre no sirve, porque Whisper *traduce* lo que se dice en español ("Hola, ¿dónde queda la estación de buses?" salía como "Hello, where is the bus station?") y lo daría por leído.
  3. **¿Qué sonidos fallaron?** El evaluador ubica en el audio el tramo donde se dijo cada fonema (alineación forzada) y mira qué sonido se oyó ahí. Loria explica hasta 2 sonidos débiles, con su palabra y a qué sonaron: "en *bus*, la *s* sonó como una *l*". Cómo se entrenó y cuánto acierta: [entrenamiento/README.md](entrenamiento/README.md).
- **El ejercicio que ve el estudiante lo escribe el código, no el modelo de lenguaje.** Se copia de lo que devolvió la herramienta, así que siempre es el mismo que se va a revisar. Si el modelo escribe un ejercicio propio (una línea con `___`), el bot lo quita y lo cambia por uno real del banco. Mientras hay un ejercicio de texto activo, el bot no deja usar `corregir_gramatica`, para que la respuesta no se guarde dos veces en el progreso.
- Si el estudiante dice "no sé", Loria le muestra la respuesta (cuenta como no acertada). Con `/cancelar` o "ya no quiero" se cierra el ejercicio.

**Agregar frases de pronunciación.** Escribe la frase en `datos/ejercicios.json` sin `"fonemas"` y ejecuta lo siguiente:

```powershell
python scripts/generar_fonemas.py         # busca cada palabra en el diccionario CMU y escribe sus fonemas
python scripts/probar_pronunciacion.py    # comprueba que todos los fonemas existan en el modelo wav2vec2
```

Los fonemas quedan separados por palabra con " | " (por ejemplo `w ɛ ɹ | ɪ z`), para que el evaluador sepa en qué palabra está cada sonido. El diccionario CMU (inglés americano, público) se descarga solo la primera vez. Si una palabra no está en el diccionario (por ejemplo, un nombre propio), el script avisa para que la cambies.

## Modo niños

Se activa al elegir "🧒 Soy Niño / Niña" en `/start`. Es solo en inglés y la versión de adultos no cambia.

- **Menú con botones grandes**, uno por fila: 💬 Hablar con Loria, 🎮 Juego de palabras, 🎤 Reto de voz, 🥚 Mi mascota y 🗑 Borrar mis datos. No tiene "Corregir un texto" ni "Cambiar idioma": el idioma queda en inglés.
- **Juegos de elegir:** una pregunta con 3 opciones que se tocan como botones, en desorden ("¿Cómo se dice «perro»? [dog] [cat] [bird]"). También hay juegos de completar y traducir, más cortos que los de adultos.
- **Respuestas cortas y con ánimo.** Máximo 4 líneas y siempre empieza con un elogio. Nunca dice "incorrecto", sino "¡Casi!" y cómo se dice. No menciona niveles como "A1". Si el niño habla de temas que no son para su edad o se siente triste, responde con cariño, le sugiere hablar con un adulto de confianza y vuelve a la práctica.
- **Mascota** (`interfaz/mascota.py`). Crece con el nivel real de inglés, calculado con las mismas reglas de `tutor/progreso.py`:

  | Nivel | A1 | A2 | B1 | B2 | C1 |
  |---|---|---|---|---|---|
  | Mascota | 🥚 Huevito | 🐣 Pollito | 🦜 Lorito | 🦜👓 Loro con gafas | 🦜🧢 Loro con gorra |

  - **Nunca se encoge.** Sigue el nivel más alto alcanzado (`nivel_max` en la base de datos). Si el nivel baja para repasar cosas más fáciles, la mascota se queda y Loria le dice "¡Tu Pollito sigue contigo!".
  - **Estrellas ⭐.** Son los aciertos desde la última revisión de nivel, de 8 en 8 (o las primeras 5 prácticas, mientras se calcula el nivel inicial). No son puntos inventados: muestran cuánto falta para que Loria revise si la mascota crece.
  - **Cuando crece,** el bot lo celebra en el chat: "¡WOW! Tu Huevito 🥚 se convirtió en Pollito 🐣!".

**Límite conocido.** El banco de niños llega hasta B1, así que para pasar a B2 y C1 hacen falta frases propias en la conversación, no solo juegos.

## Privacidad (Ley 1581 de 2012)

- **Consentimiento primero.** `/start` muestra el aviso de privacidad, y elegir el perfil es aceptar. Antes de eso no se guarda nada del usuario, ni siquiera una fila vacía en la base de datos. Las filas sin consentimiento que dejaron versiones anteriores se borran al arrancar.
- **Audios.** Se procesan y se borran de inmediato; nunca se guardan.
- **Edad.** No se guarda la edad, solo el modo (niño o adulto).
- **Borrar mis datos.** Pide confirmación y elimina el perfil, el nivel, los intentos y la memoria de la conversación.
- **Datos de otros usuarios.** El modelo de lenguaje no puede pedirlos: el id del usuario lo pone el bot.

## Archivos

El único programa que se ejecuta es `bot.py`; lo demás está agrupado en carpetas por responsabilidad. Cada carpeta de código es un paquete de Python (tiene un `__init__.py` que la describe en una línea).

```
Parley/
├── bot.py               punto de entrada: python bot.py
├── interfaz/            lo que ve el usuario en Telegram
├── agente/              el agente ReAct y el cliente MCP
├── herramientas_mcp/    el servidor MCP con las herramientas del tutor
├── modelos_lenguaje/    cadena de respaldo y proveedores (Gemini, Groq)
├── tutor/               lógica de aprendizaje: ejercicios, nivel, pronunciación, base de datos
├── datos/               archivos que no son código (banco, modelo entrenado, base de datos)
├── scripts/             utilidades que se corren a mano (pruebas y generar fonemas)
└── entrenamiento/       cómo se entrenó el evaluador de pronunciación (script y resultados)
```

| Archivo | Responsabilidad |
|---|---|
| `bot.py` | Telegram: menú, botones, mensajes, notas de voz y transcripción con Whisper. |
| `interfaz/teclados.py` | Los botones de Telegram (solo los arma; lo que hacen está en `bot.py`). |
| `interfaz/mascota.py` | Mascota del modo niños: etapas, estrellas y mensajes cuando crece. |
| `agente/agente.py` | Agente ReAct: instrucciones y ciclo pensar → actuar → observar; pide las herramientas por MCP. |
| `agente/cliente_mcp.py` | Cliente MCP: lanza el servidor y le pide ejecutar herramientas. |
| `herramientas_mcp/servidor_mcp.py` | Servidor MCP: expone las herramientas del tutor. |
| `modelos_lenguaje/llm.py` | Cadena de respaldo, tiempos máximos, registro en consola y corrección gramatical. |
| `modelos_lenguaje/llm_gemini.py`, `llm_groq.py` | Adaptadores: traducen el formato común al de cada proveedor. |
| `tutor/progreso.py` | Reglas de nivel (A1 a C1) y resumen del progreso. |
| `tutor/ejercicios.py` | Banco de ejercicios: cuál proponer a cada estudiante y cómo revisar su respuesta. |
| `tutor/pronunciacion.py` | Evaluador de pronunciación (wav2vec2 + red BiLSTM entrenada): puntajes y sonidos débiles. |
| `tutor/rasgos_pronunciacion.py` | Alineación forzada y características de cada fonema (las usan el bot y el entrenamiento). |
| `tutor/db.py` | Base de datos SQLite: usuarios, nivel por idioma e intentos. |
| `datos/ejercicios.json` | Las frases y ejercicios (se pueden agregar sin tocar código). |
| `datos/evaluador_pronunciacion.pt` | La red entrenada del evaluador (trae adentro su normalización y variantes). || `datos/parley.db`, `datos/audios/`, `datos/cmudict.dict` | Se crean solos al usar el bot; no se suben a GitHub (datos personales y una descarga). |
| `scripts/probar_modelos.py` | Prueba cada modelo de la cadena de respaldo y la cadena completa. |
| `scripts/probar_mcp.py` | Lanza el servidor MCP sin Telegram y llama algunas herramientas. |
| `scripts/probar_pronunciacion.py` | Revisa los fonemas del banco y evalúa un audio de prueba. |
| `scripts/generar_fonemas.py` | Escribe los fonemas de las frases nuevas de pronunciación (diccionario CMU). |
| `entrenamiento/entrenar_evaluador.py` | Entrena el evaluador actual (en Colab o en el computador) y compara versiones. |
| `entrenamiento/resultados_etapa8.json` | Los números de ese entrenamiento (variantes, Pearson, épocas). |
Los scripts se ejecutan desde la carpeta del proyecto, por ejemplo `python scripts/probar_mcp.py`.

## Límites conocidos

- **Cuotas gratuitas.** Gemini da 20 peticiones por día por modelo, y cada mensaje usa de 2 a 4. En la práctica, después de unos 15 a 30 mensajes al día responde Groq. Una ráfaga de mensajes puede saturar también a Groq; a ritmo normal de un usuario no pasó.
- **Fallos de los modelos con herramientas.** `gpt-oss` en Groq a veces escribe mal la llamada a una herramienta. El bot lo reintenta con el siguiente modelo.
- **El nivel lo estima el modelo de lenguaje.** El nivel de cada frase no sale de un examen oficial y puede variar un poco entre modelos. Las reglas para subir o bajar sí son fijas y están en código.
- **Memoria corta.** La memoria de la conversación (últimos 8 mensajes) se pierde al reiniciar el bot. El nivel y el progreso sí quedan guardados.
- **Pronunciación:**
  - es solo en inglés y compara contra el inglés americano del diccionario CMU;
  - se entrenó con hablantes de chino mandarín (speechocean762), no de español;
  - "qué se oyó" es una pista, no un diagnóstico exacto;
  - acierta cerca de la mitad de las veces al señalar los 2 sonidos peores (ver [entrenamiento/README.md](entrenamiento/README.md));
  - con acento fuerte, el parecido que mide Whisper queda cerca del límite de 0,45 (una voz española leyendo bien dio 0,50), así que una lectura con mucho acento podría rechazarse como "no es la frase".
- **Pruebas.** Las pruebas automáticas usan modelos simulados, audios sintéticos de Windows y el servidor MCP real. Las pruebas con personas fueron manuales, de la autora, en Telegram. No hay pruebas con estudiantes reales.
- **Un solo proceso.** Solo una persona puede correr el bot a la vez con el mismo token.

## Problemas comunes

- **`ModuleNotFoundError`.** El entorno no está activo. Activa `.venv` y repite `pip install -r requirements.txt`.
- **`unexpected keyword argument 'metadata_errors'`.** Ejecuta `pip install "av<19"` con el entorno activo y reinicia el bot.
- **`InvalidToken` o `Unauthorized`.** El token del `.env` está mal copiado, o el archivo quedó como `.env.txt`.
- **"clave inválida o sin permiso (401/403)" en la consola.** La clave de ese proveedor está mal copiada, o no se reinició el bot después de guardar el `.env`.
- **"el modelo no existe o cambió de nombre (404)".** Cambió el nombre del modelo. Revisa los nombres vigentes en [aistudio.google.com/docs/models](https://aistudio.google.com/docs/models) o [console.groq.com/docs/models](https://console.groq.com/docs/models) y ajústalos con `GEMINI_MODELOS` o `GROQ_MODELOS` en `.env`.
- **"saturado o límite por minuto alcanzado (429)".** El bot pasa solo al siguiente modelo; si pasa con todos, espera un minuto.
- **"cuota diaria gratuita agotada (429)".** Se gastaron las 20 peticiones diarias de ese modelo de Gemini. El bot lo salta hasta que se reinicie la cuota y usa los demás.
- **"No se pudo iniciar el servidor MCP".** Ejecuta `python -m herramientas_mcp.servidor_mcp` (desde la carpeta del proyecto) para ver el error. Si arranca y se queda quieto, está bien (está esperando al bot); ciérralo con `Ctrl + C`.
- **"Sin clave en .env para: groq" al arrancar.** Falta `GROQ_API_KEY`: el bot funciona, pero sin el último respaldo.
