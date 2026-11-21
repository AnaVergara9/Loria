"""Modelos de lenguaje con cadena de respaldo: Gemini principal -> Gemini de respaldo -> Groq.

Cada intento tiene un tiempo máximo de espera. Si un modelo falla, se pasa al siguiente y se
anota en la consola por qué falló. Un modelo que acaba de fallar queda "en pausa" un rato,
para no hacer esperar al usuario con un modelo que sabemos que está caído.
"""
import os
import re
import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as EsperaAgotada

from dotenv import load_dotenv

load_dotenv()

from modelos_lenguaje import llm_gemini, llm_groq

log = logging.getLogger("modelos")

PROVEEDORES = {"gemini": llm_gemini, "groq": llm_groq}

TIEMPO_POR_INTENTO = float(os.getenv("LLM_TIEMPO_POR_INTENTO", "12"))  # segundos por llamada
TIEMPO_POR_TURNO = float(os.getenv("LLM_TIEMPO_POR_TURNO", "60"))      # segundos para todo un mensaje
PAUSA_SI_FALLA = 60          # segundos que un modelo saturado o caído queda fuera de la cadena
PAUSA_SI_CONFIGURACION = 600  # clave inválida o modelo inexistente: no tiene sentido reintentar pronto

# Para la sustentación: LLM_SIMULAR_FALLO=gemini hace que todos los Gemini "fallen" y se vea el paso a Groq.
SIMULAR_FALLO = {p.strip() for p in os.getenv("LLM_SIMULAR_FALLO", "").split(",") if p.strip()}


def _lista(variable: str, defecto: str) -> list:
    return [m.strip() for m in os.getenv(variable, defecto).split(",") if m.strip()]


# La cadena, en orden. Verifica los nombres en https://aistudio.google.com/docs/models
# y https://console.groq.com/docs/models (revisados el 20/11/2026).
CADENA = (
    [("gemini", m) for m in _lista("GEMINI_MODELOS", "gemini-3.5-flash,gemini-3.7-flash,gemini-3.8-flash")]
    + [("groq", m) for m in _lista("GROQ_MODELOS", "openai/gpt-oss-120b,qwen/qwen3.8-27b,openai/gpt-oss-20b")]
)
_sin_clave = sorted({p for p, _ in CADENA if not PROVEEDORES[p].disponible()})
CADENA = [(p, m) for p, m in CADENA if PROVEEDORES[p].disponible()]

_pausa_hasta: dict = {}  # (proveedor, modelo) -> instante en que vuelve a estar disponible


class TodosFallaron(Exception):
    """Ningún modelo de la cadena pudo responder."""

    def __init__(self, fallos: list):
        self.fallos = fallos
        super().__init__("Ningún modelo respondió: " + "; ".join(fallos))


class FalloSimulado(Exception):
    pass


class TurnoSinTiempo(TimeoutError):
    """Se acabó el tiempo total del mensaje (no el de un intento)."""


NOMBRES_ERROR_RED = ("ConnectError", "ReadError", "WriteError", "RemoteProtocolError",
                     "NetworkError", "ConnectionError", "APIConnectionError")


def es_error_de_red(e: Exception) -> bool:
    """True si el error es de conexión (cortes, DNS), de cualquier librería."""
    return any(n in type(e).__name__ for n in NOMBRES_ERROR_RED)


def es_tiempo_agotado(e: Exception) -> bool:
    return isinstance(e, TimeoutError) or "Timeout" in type(e).__name__ or "TimedOut" in type(e).__name__


def describir_cadena() -> str:
    return " -> ".join(f"{p}/{m}" for p, m in CADENA) or "(vacía)"


def _segundos_de_espera(texto: str) -> float | None:
    """Lee el "Please retry in 4h55m35s" que manda Gemini en los errores 429."""
    m = re.search(r"retry in (?:(\d+)h)?(?:(\d+)m)?(?:([\d.]+)s)?", texto)
    if not m or not any(m.groups()):
        return None
    h, mi, s = (float(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


def _motivo(e: Exception) -> tuple:
    """Traduce un error a (explicación corta, segundos de pausa)."""
    if isinstance(e, FalloSimulado):
        return "fallo simulado (LLM_SIMULAR_FALLO)", 0
    if isinstance(e, TurnoSinTiempo):
        return f"se acabó el tiempo total del mensaje ({TIEMPO_POR_TURNO:.0f} s)", 0
    if es_tiempo_agotado(e):
        return f"no respondió en {TIEMPO_POR_INTENTO:.0f} s", PAUSA_SI_FALLA
    codigo = getattr(e, "code", None) or getattr(e, "status_code", None)
    if codigo == 429:
        texto = str(e)
        espera = _segundos_de_espera(texto)
        try:  # Groq manda los segundos exactos en el encabezado "retry-after"
            espera = espera or float(e.response.headers.get("retry-after"))
        except (AttributeError, TypeError, ValueError):
            pass
        if "per day" in texto or "PerDay" in texto:
            # Cuota DIARIA gratuita agotada: no sirve reintentar en un minuto, se pausa hasta que se reinicie.
            pausa = espera or 3600
            return f"cuota diaria gratuita agotada (429), vuelve en {pausa / 3600:.1f} h", pausa
        pausa = min(max(espera or PAUSA_SI_FALLA, 5), 3600)
        return f"saturado o límite por minuto alcanzado (429), vuelve en {pausa:.0f} s", pausa
    if isinstance(codigo, int) and codigo >= 500:
        return f"error del servidor ({codigo})", PAUSA_SI_FALLA
    if codigo in (401, 403):
        return f"clave inválida o sin permiso ({codigo})", PAUSA_SI_CONFIGURACION
    if codigo == 404:
        return "el modelo no existe o cambió de nombre (404)", PAUSA_SI_CONFIGURACION
    if codigo == 400:
        return f"petición rechazada (400): {str(e)[:120]}", 0
    if es_error_de_red(e):
        return "sin conexión a internet", 0  # el problema es nuestro, no del modelo: no se pausa
    if isinstance(e, (json.JSONDecodeError, ValueError, KeyError)):
        return f"respuesta inválida: {str(e)[:120]}", 0
    return f"error inesperado {type(e).__name__}: {str(e)[:120]}", 0


def modelos_en_pausa() -> list:
    """Etiquetas "proveedor/modelo" de los modelos que fallaron hace poco."""
    ahora = time.time()
    return [f"{p}/{m}" for (p, m), hasta in _pausa_hasta.items() if hasta > ahora]


def pausar(etiquetas: list, segundos: float = PAUSA_SI_FALLA):
    """Pone en pausa modelos que otro proceso (el bot) ya vio caídos."""
    for etiqueta in etiquetas:
        p, _, m = etiqueta.partition("/")
        if (p, m) in CADENA:
            _pausa_hasta[(p, m)] = max(_pausa_hasta.get((p, m), 0), time.time() + segundos)


def _eslabones() -> list:
    ahora = time.time()
    libres = [e for e in CADENA if _pausa_hasta.get(e, 0) <= ahora]
    return libres or list(CADENA)  # si todos están en pausa, se intentan igual antes que rendirse


def tiempo_para(limite: float) -> float:
    """Tiempo de espera para la próxima llamada: el máximo por intento, sin pasarse del límite del turno."""
    restante = limite - time.time()
    if restante < 2:
        raise TurnoSinTiempo("Se agotó el tiempo del turno.")
    return min(TIEMPO_POR_INTENTO, restante)


# Las librerías aplican su tiempo máximo por fase (conectar, leer...), no al total: en las pruebas
# una llamada con límite de 12 s tardó 19 s. Por eso cada llamada corre en un hilo aparte y,
# si no termina a tiempo, se deja de esperarla y se pasa al siguiente modelo.
_hilos = ThreadPoolExecutor(max_workers=16, thread_name_prefix="modelo")


def llamar_con_tope(funcion, *args, segundos: float):
    """Ejecuta funcion(*args, segundos) y garantiza que nunca se espera más de `segundos`."""
    futuro = _hilos.submit(funcion, *args, segundos)
    try:
        return futuro.result(timeout=segundos + 1)  # +1 s para que la librería alcance a cortar sola
    except EsperaAgotada:
        raise TimeoutError(f"no respondió en {segundos:.0f} s") from None


def con_respaldo(tarea: str, operacion, limite: float | None = None):
    """Ejecuta operacion(proveedor, modelo, limite) en cada eslabón hasta que uno funcione.

    Devuelve (resultado, "proveedor/modelo", lista_de_fallos). Si todos fallan lanza TodosFallaron.
    """
    if not CADENA:
        raise TodosFallaron(["no hay ningún modelo configurado (revisa las claves en .env)"])
    limite = limite or time.time() + TIEMPO_POR_TURNO
    fallos = []
    for nombre_prov, modelo in _eslabones():
        etiqueta = f"{nombre_prov}/{modelo}"
        if limite - time.time() < 2:
            fallos.append(f"{etiqueta}: no se intentó, se acabó el tiempo del turno")
            break
        t0 = time.time()
        try:
            if nombre_prov in SIMULAR_FALLO:
                raise FalloSimulado()
            resultado = operacion(PROVEEDORES[nombre_prov], modelo, limite)
        except Exception as e:
            motivo, pausa = _motivo(e)
            if motivo.startswith("error inesperado"):
                log.exception("MODELO | %s: %s falló con un error inesperado", tarea, etiqueta)
            log.warning("MODELO | %s: %s FALLÓ en %.1f s -> %s%s", tarea, etiqueta, time.time() - t0, motivo,
                        f" (en pausa {pausa} s)" if pausa else "")
            fallos.append(f"{etiqueta}: {motivo}")
            if pausa:
                _pausa_hasta[(nombre_prov, modelo)] = time.time() + pausa
            continue
        log.info("MODELO | %s: respondió %s en %.1f s%s", tarea, etiqueta, time.time() - t0,
                 f" (antes fallaron {len(fallos)})" if fallos else "")
        return resultado, etiqueta, fallos
    log.error("MODELO | %s: TODOS los modelos fallaron", tarea)
    raise TodosFallaron(fallos)


def generar_json(tarea, instruccion, texto, esquema, temperatura=0.2, limite=None) -> tuple:
    """Pide una respuesta JSON con el esquema dado, con respaldo. Devuelve (dict, modelo)."""
    def operacion(prov, modelo, lim):
        crudo = llamar_con_tope(prov.generar_json, modelo, instruccion, texto, esquema, temperatura,
                                segundos=tiempo_para(lim))
        datos = json.loads(crudo)
        faltan = [k for k in esquema.get("required", []) if k not in datos]
        if faltan:
            raise ValueError(f"al JSON le faltan las claves {faltan}")
        return datos

    datos, modelo, _ = con_respaldo(tarea, operacion, limite)
    return datos, modelo


# ---------------------------------------------------------------- corrección gramatical
ESQUEMA_EDICIONES = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "original": {"type": "string"},
            "correccion": {"type": "string"},
            "tipo": {"type": "string", "enum": ["gramática", "vocabulario", "ortografía", "puntuación"]},
            "explicacion": {"type": "string"},
        },
        "required": ["original", "correccion", "tipo", "explicacion"],
        "additionalProperties": False,
    },
}

ESQUEMA_CORRECCION = {
    "type": "object",
    "properties": {
        "idioma": {"type": "string", "enum": ["inglés", "francés", "otro"]},
        "corregida": {"type": "string"},
        "ediciones": ESQUEMA_EDICIONES,
        # Nivel MCER que demuestra la frase (vocabulario y estructuras usadas), no el del estudiante.
        "nivel_frase": {"type": "string", "enum": ["A1", "A2", "B1", "B2", "C1"]},
    },
    "required": ["idioma", "corregida", "ediciones", "nivel_frase"],
    "additionalProperties": False,
}

# Cómo explicar según el nivel del estudiante.
EXPLICAR_SEGUN_NIVEL = {
    "A1": "Explica con palabras muy simples, sin términos gramaticales (no digas 'pretérito' ni 'auxiliar').",
    "A2": "Explica con palabras simples; como mucho nombra el tiempo verbal (pasado, presente).",
    "B1": "Puedes nombrar la regla gramatical de forma sencilla.",
    "B2": "Puedes usar términos gramaticales y mencionar la regla con precisión.",
    "C1": "Usa términos gramaticales precisos; puedes mencionar matices de registro si el error es de vocabulario.",
}


def corregir(texto: str, perfil: str = "adulto", errores_previos: str = "", limite: float | None = None,
             niveles: dict | None = None) -> dict:
    """Corrección gramatical con ediciones mínimas. El modelo detecta el idioma (inglés o francés).

    `niveles` es {"inglés": "B1", "francés": "A2"}: las explicaciones se adaptan al nivel del idioma detectado.
    """
    tono = (
        "Hablas con un niño de 7 a 11 años: sé muy amable, usa emojis, ejemplos divertidos y palabras súper simples."
        if perfil == "nino"
        else "Hablas con un estudiante adulto: sé claro, respetuoso, directo y motivador."
    )
    contexto_errores = (
        f"\nErrores frecuentes previos del estudiante (priorízalos si reaparecen): {errores_previos}"
        if errores_previos else ""
    )
    niveles = niveles or {}
    guia_nivel = "\n".join(
        f"- Si el texto está en {idioma} (nivel del estudiante: {nivel}): {EXPLICAR_SEGUN_NIVEL.get(nivel[:2], EXPLICAR_SEGUN_NIVEL['A1'])}"
        for idioma, nivel in niveles.items()
    )
    instruccion = f"""Eres Loria, un tutor de idiomas para hispanohablantes. {tono}
El estudiante practica inglés o francés. Detecta en cuál de los dos está escrito el texto.
Corrige únicamente lo que es incorrecto en ese idioma, sin cambiar el estilo ni reescribir la frase.{contexto_errores}
Responde solo con JSON con estas claves:
- idioma: "inglés", "francés" u "otro"
- corregida: la frase corregida (igual a la original si no hay errores)
- ediciones: lista de máximo 3 objetos con "original", "correccion", "tipo" y "explicacion"
  - tipo: "gramática" (conjugación, concordancia, orden, tiempos), "vocabulario" (palabra equivocada o inexistente),
    "ortografía" (letras, tildes, mayúsculas) o "puntuación"
- nivel_frase: el nivel MCER (A1, A2, B1, B2 o C1) que demuestra la frase por su vocabulario y estructuras,
  sin importar los errores. Ejemplos: "I like dogs" es A1; "If I had known, I would have come" es B2.
La explicacion va en español, en una sola frase corta y fácil de entender.
{guia_nivel}
Si no hay errores, ediciones es una lista vacía.
Si el texto no está en inglés ni en francés, idioma es "otro", ediciones es una lista vacía y nivel_frase es "A1"."""

    try:
        datos, _ = generar_json("corregir", instruccion, texto, ESQUEMA_CORRECCION, 0.2, limite)
        datos["ediciones"] = datos["ediciones"][:3]
        return datos
    except (TodosFallaron, TimeoutError):
        return {"error": "El servicio de corrección no está disponible en este momento."}


ESQUEMA_REVISION = {
    "type": "object",
    "properties": {
        "correcta": {"type": "boolean"},
        "corregida": {"type": "string"},
        "ediciones": ESQUEMA_EDICIONES,
    },
    "required": ["correcta", "corregida", "ediciones"],
    "additionalProperties": False,
}


def revisar_traduccion(original: str, referencias: list, respuesta: str, idioma: str, perfil: str = "adulto",
                       nivel: str = "A1", limite: float | None = None) -> dict:
    """Juzga una traducción del estudiante (del español al inglés o francés).

    Las referencias son ejemplos: hay muchas traducciones válidas, por eso no basta comparar textos.
    """
    tono = ("Hablas con un niño de 7 a 11 años: usa palabras súper simples y ánimo."
            if perfil == "nino" else "Hablas con un estudiante adulto: sé claro y respetuoso.")
    instruccion = f"""Eres Loria, un tutor de idiomas para hispanohablantes. {tono}
El estudiante debía traducir al {idioma} esta frase en español: "{original}"
Traducciones de referencia (son ejemplos, hay otras válidas): {" | ".join(referencias)}
El mensaje del usuario es la traducción del estudiante. Responde solo con JSON:
- correcta: true si transmite el mismo significado y no tiene errores de gramática ni de vocabulario.
  Acepta sinónimos, contracciones y otras estructuras correctas. Los errores de ortografía, tildes,
  mayúsculas o puntuación NO la vuelven incorrecta (pero inclúyelos en ediciones).
  Si está en otro idioma, está vacía o cambia el significado, correcta es false.
- corregida: la traducción del estudiante con cambios mínimos para que quede correcta (si el significado
  está muy lejos, la referencia más parecida).
- ediciones: máximo 3 objetos con "original", "correccion", "tipo" (gramática, vocabulario, ortografía o
  puntuación) y "explicacion" (en español, una frase corta). Lista vacía si no hay nada que corregir.
{EXPLICAR_SEGUN_NIVEL.get(nivel, EXPLICAR_SEGUN_NIVEL["A1"])}"""
    try:
        datos, _ = generar_json("revisar", instruccion, respuesta, ESQUEMA_REVISION, 0.1, limite)
        datos["ediciones"] = datos["ediciones"][:3]
        return datos
    except (TodosFallaron, TimeoutError):
        return {"error": "El servicio de revisión no está disponible en este momento."}


if CADENA:
    log.info("Cadena de respaldo: %s", describir_cadena())
if _sin_clave:
    log.warning("Sin clave en .env para: %s (esos modelos no se usarán)", ", ".join(_sin_clave))
