"""Agente ReAct de Loria: el modelo de lenguaje decide qué herramienta MCP usar en cada turno.

Ciclo:  PENSAR (el modelo lee el mensaje y la lista de herramientas)
        -> ACTUAR (si elige una herramienta, el bot se la pide al servidor MCP)
        -> OBSERVAR (el resultado vuelve al modelo)
        -> ... hasta que el modelo responde con texto.
"""
import re
import json
import time
import logging
from collections import defaultdict, deque

from modelos_lenguaje import llm
from agente.cliente_mcp import cliente as mcp

log = logging.getLogger("agente")

MAX_PASOS = 5  # tope de vueltas del ciclo, evita bucles infinitos

# Memoria de corto plazo: últimos turnos por usuario (solo texto, formato neutro). Se pierde al reiniciar.
historial = defaultdict(lambda: deque(maxlen=8))


# ---------------------------------------------------------------- herramientas (vía MCP)
def ejecutar(nombre: str, args: dict, ctx: dict) -> tuple:
    """Pide la herramienta al servidor MCP, con caché por turno. Devuelve (resultado, venía_de_caché).

    Si un modelo falla a mitad de un turno y se reintenta con otro, las herramientas que ya
    se ejecutaron NO se repiten (así no se duplican errores guardados ni se cambia el ejercicio).
    """
    clave = (nombre, json.dumps(args, sort_keys=True, default=str))
    cache = ctx.setdefault("cache", {})
    if clave in cache:
        return cache[clave], True

    # Con un ejercicio de texto activo, la respuesta se revisa con revisar_respuesta. Si el modelo
    # también la "corrige", se guardaría dos veces en el progreso: el bot no lo permite.
    if nombre == "corregir_gramatica" and ctx.get("hay_ejercicio_texto"):
        log.info("HERRAMIENTA | corregir_gramatica bloqueada: hay un ejercicio de texto activo")
        return {"error": "Hay un ejercicio de texto activo: usa revisar_respuesta con la respuesta del estudiante, "
                         "o cancelar_ejercicio si cambió de tema."}, False

    restante = max(5.0, ctx["limite"] - time.time())
    contexto = {
        "user_id": ctx["user_id"],
        "ruta_audio": ctx.get("ruta_audio"),
        "transcripcion": ctx.get("transcripcion"),
        "tiempo_max": restante - 2,                 # la herramienta debe terminar antes que el turno
        "evitar_modelos": llm.modelos_en_pausa(),   # lo que el bot ya sabe que está caído
    }
    resultado = mcp.llamar(nombre, args, contexto, espera_max=restante)
    if "error" not in resultado:
        cache[clave] = resultado
        if nombre in ("evaluar_pronunciacion", "revisar_respuesta"):
            ctx["evaluado"] = True  # el ejercicio se cierra al final del turno, si todo salió bien
        if nombre in GENERADORES:
            ctx["ejercicio_nuevo"] = (nombre, resultado)  # el bot lo mostrará tal cual, no el modelo
            ctx["hay_ejercicio_texto"] = nombre == "generar_ejercicio_texto"
        if nombre == "cancelar_ejercicio":
            ctx["hay_ejercicio_texto"] = False
            ctx.pop("ejercicio_nuevo", None)
    return resultado, False


# ---------------------------------------------------------------- ejercicios: los muestra el código, no el modelo
GENERADORES = ("generar_ejercicio_texto", "generar_ejercicio_pronunciacion")
ESPACIO = re.compile(r"_{2,}")  # "___": señal de un ejercicio de completar escrito en la respuesta


def formatear_ejercicio(nombre: str, ej: dict, perfil: str = "adulto") -> str:
    """Texto del ejercicio copiado del resultado de la herramienta. Así lo que ve el estudiante es
    exactamente lo que el bot va a revisar (el modelo de lenguaje podría cambiarlo o inventarlo)."""
    nino = perfil == "nino"
    if nombre == "generar_ejercicio_pronunciacion":
        if nino:
            return (f"🎤 ¡Reto de voz! Lee en voz alta:\n\n👉 {ej['frase']}\n\n"
                    "Mantén apretado el micrófono 🎙 y dilo. ¡Tú puedes! 💪")
        return f"🎙 Lee en voz alta esta frase:\n\n👉 {ej['frase']}\n\nEnvíame una nota de voz leyéndola."
    if nino:   # frases cortas y sin nivel MCER (al niño no le dice nada "A1")
        titulo = {"elegir": "🎮 ¡Elige la respuesta correcta!", "completar": "🎮 ¡Completa la frase!",
                  "traducir": "🎮 ¿Cómo se dice en inglés?"}[ej["tipo"]]
        texto = f"{titulo}\n\n👉 {ej['enunciado']}"
        if ej.get("pista"):
            texto += f"\n\n💡 Pista: {ej['pista']}"
        return texto + ("\n\nToca tu respuesta 👇" if ej["tipo"] == "elegir" else "\n\nEscríbeme tu respuesta ✏️")
    bandera = "🇬🇧" if ej["idioma"] == "inglés" else "🇫🇷"
    if ej["tipo"] == "elegir":
        texto = f"{bandera} Elige la respuesta (nivel {ej['nivel']}):\n\n👉 {ej['enunciado']}"
    elif ej["tipo"] == "completar":
        texto = f"{bandera} ✏️ Completa la frase (nivel {ej['nivel']}):\n\n👉 {ej['enunciado']}"
    else:
        texto = f"{bandera} 🔁 Traduce al {ej['idioma']} (nivel {ej['nivel']}):\n\n👉 {ej['enunciado']}"
    if ej.get("pista"):
        texto += f"\n\n💡 Pista: {ej['pista']}"
    return texto + "\n\nEscríbeme tu respuesta."


def _limpiar_ejercicios_del_modelo(texto: str, ej_nuevo: tuple | None) -> tuple:
    """Quita del texto del modelo las líneas que parecen un ejercicio (con "___" o con el enunciado
    del ejercicio nuevo). Devuelve (texto_limpio, había_un_ejercicio_inventado)."""
    repetidos = []
    if ej_nuevo:
        repetidos = [ej_nuevo[1].get("enunciado") or ej_nuevo[1].get("frase") or ""]
    lineas, inventado = [], False
    for linea in texto.splitlines():
        if ESPACIO.search(linea):
            inventado = True
            continue
        if any(r and r.lower() in linea.lower() for r in repetidos):
            continue
        lineas.append(linea)
    return "\n".join(lineas).strip(), inventado


# ---------------------------------------------------------------- instrucciones
def describir_niveles(resumen: dict) -> str:
    """Convierte el resultado de consultar_nivel en una línea para las instrucciones del modelo."""
    partes = []
    for idioma, info in resumen.items():
        if not isinstance(info, dict):
            continue
        estado = "" if info.get("ubicado") else " (todavía calculando su nivel)"
        partes.append(f"{idioma} {info.get('nivel', 'A1')}{estado}")
    return "; ".join(partes) or "desconocido"


def describir_ejercicio(perfil_mcp: dict) -> str:
    """Convierte el ejercicio activo (de consultar_perfil) en una línea para las instrucciones."""
    ej = perfil_mcp.get("ejercicio_texto")
    if ej:
        que = {"completar": "completar el espacio ___ de",
               "elegir": f"elegir entre {ej.get('opciones')} para",
               "traducir": f"traducir al {ej['idioma']}"}.get(ej["tipo"], "responder")
        return f'de texto: {que} "{ej["enunciado"]}" ({ej["idioma"]}, nivel {ej["nivel"]}).'
    if perfil_mcp.get("ejercicio_pronunciacion"):
        return f'de pronunciación: leer en voz alta "{perfil_mcp["ejercicio_pronunciacion"]}".'
    return "ninguno."


def construir_instruccion(perfil: str, niveles: str = "desconocido", ejercicio: str = "ninguno.",
                          idioma: str = "inglés") -> str:
    tono = (
        """Hablas con un NIÑO de 7 a 11 años que practica inglés. Reglas para niños:
- Máximo 4 líneas cortas, con palabras muy simples y 1 o 2 emojis.
- Empieza siempre con un elogio o ánimo. Nunca digas "mal" ni "incorrecto": di "¡Casi!" y muestra cómo se dice.
- Solo inglés: si escribe en francés, dile con cariño que aquí jugamos en inglés.
- No menciones niveles como "A1" o "B2": habla de su mascota y sus estrellas.
- Si habla de temas que no son para su edad o se siente triste, responde con cariño, sin entrar en el tema,
  y sugiérele hablar con un adulto de confianza; luego vuelve a la práctica."""
        if perfil == "nino"
        else "Hablas con un estudiante adulto: sé claro, respetuoso, directo y motivador."
    )
    return f"""Eres Loria 🦜, un tutor de idiomas por Telegram para hispanohablantes que practican inglés y francés. {tono}

Idioma que el estudiante eligió practicar: {idioma}. Conversa y propón ejercicios en ese idioma, salvo que
él escriba en el otro idioma o pida explícitamente el otro.
Ejercicio activo ahora: {ejercicio}

Tienes herramientas. En cada turno decide cuál usar:
- Si hay un ejercicio de texto activo y el mensaje es su respuesta: llama a revisar_respuesta con el mensaje tal cual
  (NO a corregir_gramatica). Si dice que no sabe o pide la solución, llama a revisar_respuesta con respuesta vacía.
- Si el estudiante escribe o dice una frase en inglés o francés: llama primero a corregir_gramatica con esa frase.
- Si pide un ejercicio, otro ejercicio, practicar escribiendo o que lo pongas a prueba (por ejemplo "dame un ejercicio",
  "otro", "uno de francés", o "sí" cuando le ofreciste otro): llama a generar_ejercicio_texto con ese idioma, o con el
  último que practicó. Los niños solo tienen ejercicios de inglés.
- NUNCA inventes ejercicios ni frases para leer o completar: solo existen los que devuelven las herramientas, porque
  el bot revisa la respuesta contra el ejercicio guardado. Si escribes uno tú, el estudiante será evaluado mal.
- Si quiere practicar pronunciación: llama a generar_ejercicio_pronunciacion. Solo hay pronunciación en inglés;
  en francés ofrécele un ejercicio de texto.
- Si el mensaje dice que envió una nota de voz para el ejercicio activo: llama a evaluar_pronunciacion.
- Si ya no quiere hacer el ejercicio activo o quiere hablar de otra cosa: llama a cancelar_ejercicio.
- Si necesitas recordar sus errores: llama a consultar_perfil.
- Si pregunta por su nivel o su progreso: llama a consultar_nivel y resúmelo en pocas líneas.
- Si pide explícitamente cambiar su nivel (por ejemplo "ponme en B2"): llama a cambiar_nivel. Nunca lo cambies por tu cuenta.
- Para saludos o dudas generales no hace falta herramienta.

Nivel actual del estudiante (escala MCER): {niveles}.
Cuando le hables en el idioma que practica, usa vocabulario y estructuras de su nivel: A1-A2 frases muy cortas
y palabras comunes; B1 frases cotidianas con conectores simples; B2-C1 lenguaje natural y variado.
Si el resultado de corregir_gramatica o de revisar_respuesta trae "cambio_nivel": si es "inicial" o "sube", felicítalo y dile su nuevo
nivel; si es "baja", díselo con tacto y ánimo (así practica a su ritmo).

Cómo responder al final (texto plano, sin Markdown, máximo 8 líneas):
- Después de corregir_gramatica: muestra la frase corregida y como máximo 3 ediciones con su explicación breve en español. No inventes correcciones que la herramienta no dio. Si no hubo errores, felicítalo. Luego responde al contenido de lo que dijo con 1 o 2 frases en el idioma que practica y haz una pregunta corta para seguir la conversación.
- Después de generar_ejercicio_texto o generar_ejercicio_pronunciacion: NO escribas el ejercicio ni la frase; el bot
  los muestra automáticamente debajo de tu mensaje, copiados de la herramienta. Escribe solo una frase corta de ánimo
  en español (por ejemplo "¡Vamos con este!"). Nunca des la respuesta.
- Después de revisar_respuesta: dile si acertó. Si no, muestra la respuesta esperada (o "corregida" si se parece más
  a lo que escribió) y explica el error en una frase. Si hay otras respuestas válidas, puedes mencionar una.
  Termina preguntándole si quiere otro ejercicio, sin escribirlo tú.
- Después de evaluar_pronunciacion: comenta cómo le fue sin mostrar números ni símbolos fonéticos; si hay
  "palabras_no_entendidas", dile cuáles palabras no se le entendieron para que las repase; explica máximo 2 sonidos con ejemplos cotidianos (por ejemplo, la 'th' de 'think' se hace sacando un poquito la punta de la lengua entre los dientes); si no hay sonidos débiles, felicítalo. Termina preguntándole si quiere otra frase, sin escribirla tú.
- Si una herramienta devuelve un error, explícalo con sencillez y sugiere qué hacer.
Nunca afirmes un puntaje ni una corrección que no vengan de una herramienta."""


# ---------------------------------------------------------------- verificador: ¿es una frase para practicar?
# Palabras muy frecuentes de cada idioma. Se cuentan las del mensaje y gana el idioma con más
# (las que comparten dos idiomas, como "la" o "de", están en ambas listas y se compensan).
# Es una regla simple a propósito (sin gastar el modelo de lenguaje); solo decide si se le insiste al modelo.
_PALABRAS = {
    "español": set("""de la que el en y los se del las por un para con no una su al es lo como más pero sus le ya
        este sí porque esta cuando muy sin sobre también me hasta hay donde quien desde todo nos uno les ni
        eso esto qué yo otro él ella mi mis tú te tu tus quiero cómo cuál dame puedes hola gracias ejercicio
        nivel mejor quisiera ayuda estoy está estás soy eres tengo hacer practicar""".split()),
    "inglés": set("""the a an is are i you to and of in it my we he she they have has had was were do does did
        like with for this that on at be not can will would me your am our their there what how why when
        where went go going yesterday today because very much some""".split()),
    "francés": set("""le la les de des du un une je tu il elle nous vous ils elles est suis sont et à au aux avec pour
        bonjour merci oui comment allez voudrais
        dans ce cette mon ma mes pas ne qui j'ai c'est je suis avons ont était hier aujourd'hui très mais
        aussi ton ta tes son sa ses leur""".split()),
}


def idioma_de_la_frase(texto: str) -> str | None:
    """"inglés" o "francés" si el mensaje parece una frase en ese idioma (3 palabras o más); si no, None."""
    palabras = [p.strip(".,;:!?¡¿\"'()").lower() for p in texto.replace("’", "'").replace("-", " ").split()]
    palabras = [p for p in palabras if p]
    if len(palabras) < 3:
        return None   # "hello", "ok", "sí": no hace falta insistir
    puntos = {idioma: sum(p in lista for p in palabras) for idioma, lista in _PALABRAS.items()}
    mejor = max(puntos, key=puntos.get)
    if mejor == "español" or puntos[mejor] == 0 or puntos[mejor] <= puntos["español"]:
        return None
    return mejor


# ---------------------------------------------------------------- ciclo ReAct
def _ciclo(prov, modelo, sistema, mensajes, herramientas, ctx, traza, limite) -> str:
    """Un ciclo ReAct completo con UN modelo.

    Si el modelo falla a mitad de camino, la excepción sube a llm.con_respaldo, que repite el
    ciclo desde cero con el siguiente modelo de la cadena (no se mezclan modelos en un ciclo).
    """
    etiqueta = f"{prov.NOMBRE}/{modelo}"
    for paso in range(1, MAX_PASOS + 1):
        resp = llm.llamar_con_tope(prov.paso, modelo, sistema, mensajes, herramientas,
                                   segundos=llm.tiempo_para(limite))
        mensajes.append(resp)

        if not resp["llamadas"]:  # el modelo ya tiene lo necesario: responde
            if not resp["texto"]:
                raise ValueError("el modelo terminó sin texto")
            # VERIFICADOR: el estudiante escribió una frase en inglés o francés y el modelo respondió
            # sin usar ninguna herramienta (sin corregirla). Se le pide UNA vez que use la herramienta.
            if ctx.get("idioma_frase") and not ctx.get("elegidas") and not ctx.get("insistido"):
                ctx["insistido"] = True
                log.warning("VERIFICADOR | %s respondió sin herramientas a una frase en %s; se le pide usarlas",
                            etiqueta, ctx["idioma_frase"])
                traza.append(f"🔁 Verificador: {etiqueta} no usó herramientas con una frase en {ctx['idioma_frase']}")
                mensajes.append({"rol": "usuario", "texto": (
                    f"[Aviso del sistema: el mensaje anterior del estudiante parece una frase en {ctx['idioma_frase']}. "
                    "No respondas sin herramientas: si es una frase para practicar, llama a corregir_gramatica; "
                    "si es un pedido (ejercicio, nivel, etc.), usa la herramienta que corresponde. "
                    "Luego responde al estudiante como indican las instrucciones.]")})
                continue
            log.info("HERRAMIENTA | paso %s: %s responde sin herramienta", paso, etiqueta)
            return resp["texto"]

        for ll in resp["llamadas"]:  # ACTUAR -> OBSERVAR
            log.info("HERRAMIENTA | paso %s: %s eligió %s(%s)", paso, etiqueta, ll["nombre"],
                     json.dumps(ll["args"], ensure_ascii=False))
            t0 = time.time()
            resultado, de_cache = ejecutar(ll["nombre"], ll["args"], ctx)
            ctx.setdefault("elegidas", []).append(ll["nombre"])
            linea = (f"Paso {paso}: {ll['nombre']}({ll['args']}) -> {str(resultado)[:150]} "
                     + ("(ya hecha, no se repite)" if de_cache else f"[{time.time() - t0:.1f}s]"))
            traza.append(linea)
            log.info("HERRAMIENTA | resultado: %s", str(resultado)[:200])
            mensajes.append({"rol": "herramienta", "id": ll["id"], "nombre": ll["nombre"], "resultado": resultado})

    return "Me enredé un poco con tu mensaje, ¿puedes intentarlo de nuevo?"


def responder(user_id: int, mensaje: str, perfil: str = "adulto", ruta_audio: str | None = None,
              transcripcion: str | None = None):
    """Devuelve (texto_de_respuesta, traza, herramientas_usadas). La traza es la lista de acciones y
    observaciones; las herramientas usadas le sirven al bot para elegir los botones de seguimiento.

    Lanza llm.TodosFallaron si ningún modelo de la cadena pudo responder.
    """
    limite = time.time() + llm.TIEMPO_POR_TURNO  # presupuesto de tiempo para todo el turno
    ctx = {"user_id": user_id, "ruta_audio": ruta_audio, "transcripcion": transcripcion, "limite": limite}
    msg_usuario = {"rol": "usuario", "texto": mensaje}
    base = list(historial[user_id]) + [msg_usuario]
    # El nivel lo consulta el bot (no el modelo) para adaptar las instrucciones de este turno.
    resumen = mcp.llamar("consultar_nivel", {}, {"user_id": user_id}, espera_max=10)
    niveles = describir_niveles(resumen) if "error" not in resumen else "desconocido"
    datos = mcp.llamar("consultar_perfil", {}, {"user_id": user_id}, espera_max=10)
    ejercicio = describir_ejercicio(datos) if "error" not in datos else "ninguno."
    ctx["hay_ejercicio_texto"] = bool(datos.get("ejercicio_texto"))
    idioma = datos.get("idioma_preferido") or "inglés"
    # Para el verificador: ¿el mensaje es una frase en inglés o francés? (no aplica a respuestas de
    # ejercicios ni a los avisos entre corchetes que manda el bot, como el de la nota de voz)
    if not ctx["hay_ejercicio_texto"] and not mensaje.startswith("["):
        ctx["idioma_frase"] = idioma_de_la_frase(mensaje)
    log.info("CONTEXTO | usuario %s: nivel %s; ejercicio activo %s (lo consulta el bot, no lo elige el modelo)",
             user_id, niveles, ejercicio)
    sistema = construir_instruccion(perfil, niveles, ejercicio, idioma)
    herramientas = mcp.herramientas_para_modelo()  # el modelo elige entre lo que ofrece el servidor MCP
    traza = []

    def operacion(prov, modelo, lim):
        ctx["elegidas"] = []      # cada modelo empieza el turno desde cero
        ctx["insistido"] = False  # y el verificador puede volver a insistirle una vez
        return _ciclo(prov, modelo, sistema, list(base), herramientas, ctx, traza, lim)

    try:
        texto, modelo, fallos = llm.con_respaldo("agente", operacion, limite)
    except llm.TodosFallaron as e:
        traza.extend(f"⚠️ {f}" for f in e.fallos)
        raise

    texto = texto.replace("**", "")  # algunos modelos usan negritas Markdown aunque se les pide texto plano
    log.info("TURNO | usuario %s | respondió %s | herramientas: %s", user_id, modelo,
             " -> ".join(ctx.get("elegidas", [])) or "ninguna")
    traza.extend(f"⚠️ {f}" for f in fallos)
    traza.append(f"✅ Respondió: {modelo}")

    # El ejercicio que ve el estudiante lo escribe el código, copiado de la herramienta.
    nuevo = ctx.get("ejercicio_nuevo")
    texto, inventado = _limpiar_ejercicios_del_modelo(texto, nuevo)
    if inventado and not nuevo:
        # El modelo escribió un ejercicio de completar sin pedirlo al banco: se cambia por uno real.
        idioma = "francés" if "franc" in mensaje.lower() else idioma
        log.warning("EJERCICIO | %s inventó un ejercicio; el bot lo cambia por uno del banco (%s)", modelo, idioma)
        r = mcp.llamar("generar_ejercicio_texto", {"idioma": idioma}, {"user_id": user_id})
        if "error" not in r:
            nuevo = ("generar_ejercicio_texto", r)
            ctx["evaluado"] = False  # el ejercicio nuevo no se debe cerrar
        traza.append("⚠️ El modelo escribió un ejercicio propio; el bot lo cambió por uno del banco")
    if nuevo:
        texto = (texto + "\n\n" if texto else "") + formatear_ejercicio(nuevo[0], nuevo[1], perfil)

    historial[user_id].append(msg_usuario)
    historial[user_id].append({"rol": "asistente", "texto": texto})
    if ctx.get("evaluado") and not nuevo:
        mcp.llamar("cancelar_ejercicio", {}, {"user_id": user_id})  # el ejercicio quedó evaluado y respondido
    return texto, traza, ctx.get("elegidas", [])
