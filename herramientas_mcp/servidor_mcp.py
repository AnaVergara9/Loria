"""Servidor MCP de Loria: expone las capacidades del tutor como herramientas.

Corre como un programa aparte. El bot lo lanza solo al arrancar y le habla por stdin/stdout
(transporte "stdio" de MCP), así que no hace falta ejecutarlo a mano.

Parámetros de contexto: user_id, ruta_audio, tiempo_max y evitar_modelos los llena el cliente
(el bot), NUNCA el modelo de lenguaje. El cliente los oculta de la lista que ve el modelo, así el
modelo no puede pedir datos de otro usuario ni leer otro archivo.

Para probarlo solo:  python scripts/probar_mcp.py
"""
import sys
import time
import asyncio
import logging
from typing import Annotated, Literal

from pydantic import Field

# stdout es el canal del protocolo MCP: nada más puede escribir ahí. Los registros van a stderr,
# que el bot muestra en su misma consola.
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="[servidor MCP] %(levelname)s %(message)s")
for _nombre in ("httpx", "huggingface_hub", "mcp", "google_genai"):
    logging.getLogger(_nombre).setLevel(logging.WARNING)
log = logging.getLogger("servidor_mcp")

from mcp.server.mcpserver import MCPServer

from modelos_lenguaje import llm
from tutor import progreso, ejercicios
from tutor.db import (init_db, obtener_usuario, registrar_error, guardar_ejercicio, obtener_progreso,
                guardar_ejercicio_texto, obtener_ejercicio_texto)
from tutor.pronunciacion import evaluar_audio

init_db()

mcp = MCPServer(
    "loria",
    instructions="Herramientas del tutor de idiomas Loria: corrección, perfil, nivel, ejercicios y pronunciación.",
)

UsuarioId = Annotated[int, Field(description="Id de Telegram del estudiante (lo llena el bot).")]
TiempoMax = Annotated[float, Field(description="Segundos disponibles (lo llena el bot).")]
EvitarModelos = Annotated[list[str] | None, Field(description="Modelos caídos (lo llena el bot).")]


async def _en_hilo(nombre: str, funcion, *args) -> dict:
    """Ejecuta el trabajo pesado en un hilo, para atender a varios estudiantes a la vez.
    Nunca lanza excepciones hacia el modelo: si algo falla devuelve {"error": ...}."""
    log.info("ejecutando %s", nombre)
    try:
        return await asyncio.to_thread(funcion, *args)
    except Exception as e:
        log.exception("Error en la herramienta %s", nombre)
        return {"error": str(e)}


def _anotar_cambio(user_id: int, resultado: dict, cambio: dict | None):
    if cambio:
        log.info("NIVEL | usuario %s, %s: %s -> %s (%s)", user_id, cambio["idioma"], cambio["de"],
                 cambio["a"], cambio["motivo"])
        resultado["cambio_nivel"] = cambio


# ---------------------------------------------------------------- corrección y perfil
@mcp.tool()
async def corregir_gramatica(
    texto: Annotated[str, Field(description="La frase del estudiante, tal cual la escribió o dijo.")],
    user_id: UsuarioId,
    tiempo_max: TiempoMax = 30,
    evitar_modelos: EvitarModelos = None,
) -> dict:
    """Corrige la gramática de una frase del estudiante en inglés o francés, con ediciones mínimas
    y una explicación corta en español por cada una. Guarda los errores y la frase en su progreso,
    y si su nivel cambia lo indica en "cambio_nivel".
    Úsala siempre que el estudiante escriba o diga una frase para practicar."""
    def trabajo():
        # Los modelos que el bot acaba de ver caídos se saltan también aquí, para no esperar dos veces.
        llm.pausar(evitar_modelos or [])
        u = obtener_usuario(user_id)
        r = llm.corregir(texto, u["perfil"], u["errores_frecuentes"], time.time() + tiempo_max,
                         niveles=progreso.niveles(user_id))
        if "error" in r:
            return r
        for e in r.get("ediciones", []):
            registrar_error(user_id, f"{e['original']} -> {e['correccion']}")
        _anotar_cambio(user_id, r, progreso.registrar_frase(user_id, r))  # guarda el intento y revisa el nivel
        return r
    return await _en_hilo("corregir_gramatica", trabajo)


@mcp.tool()
async def consultar_perfil(user_id: UsuarioId) -> dict:
    """Devuelve el perfil del estudiante (niño o adulto), el idioma que practica, sus errores frecuentes y el
    ejercicio activo, si tiene uno (de pronunciación o de texto). Úsala si necesitas recordar en
    qué se equivoca o qué ejercicio está haciendo."""
    def trabajo():
        u = obtener_usuario(user_id)
        ej = obtener_ejercicio_texto(user_id)
        return {
            "perfil": u["perfil"],
            "idioma_preferido": u.get("idioma") or "inglés",
            "errores_frecuentes": u["errores_frecuentes"] or "ninguno todavía",
            "ejercicio_pronunciacion": u["frase_objetivo"],
            "ejercicio_texto": ejercicios.publico(ej) if ej else None,
        }
    return await _en_hilo("consultar_perfil", trabajo)


# ---------------------------------------------------------------- ejercicios de texto
@mcp.tool()
async def generar_ejercicio_texto(
    user_id: UsuarioId,
    idioma: Annotated[Literal["inglés", "francés"], Field(description="Idioma que quiere practicar.")],
) -> dict:
    """Propone un ejercicio escrito de su nivel: completar una frase o traducirla del español.
    Lo deja como ejercicio activo hasta que responda. Úsala cuando pida un ejercicio, practicar
    escribiendo o que lo pongan a prueba. No incluye la respuesta: nunca la inventes."""
    def trabajo():
        u = obtener_usuario(user_id)
        nivel = obtener_progreso(user_id, idioma)["nivel"]
        ej = ejercicios.elegir_texto(user_id, idioma, u["perfil"], nivel)
        if ej is None:
            return {"error": f"Por ahora no hay ejercicios de {idioma} para este perfil. "
                             "Los ejercicios para niños son solo de inglés."}
        guardar_ejercicio_texto(user_id, ej)
        log.info("EJERCICIO | usuario %s: %s de %s, nivel %s (%s)", user_id, ej["tipo"], idioma, ej["nivel"], ej["id"])
        return ejercicios.publico(ej)
    return await _en_hilo("generar_ejercicio_texto", trabajo)


@mcp.tool()
async def revisar_respuesta(
    user_id: UsuarioId,
    respuesta: Annotated[str, Field(description="La respuesta del estudiante, tal cual la escribió. "
                                                "Vacía si se rinde o pide la solución.")],
    tiempo_max: TiempoMax = 30,
    evitar_modelos: EvitarModelos = None,
) -> dict:
    """Revisa la respuesta del estudiante al ejercicio de texto activo, la guarda en su progreso
    y devuelve si es correcta, la respuesta esperada y las correcciones. Si su nivel cambia lo
    indica en "cambio_nivel". Úsala cuando haya un ejercicio de texto activo y el mensaje sea
    su respuesta."""
    def trabajo():
        ej = obtener_ejercicio_texto(user_id)
        if not ej:
            return {"error": "No hay un ejercicio de texto activo. Primero hay que proponer uno."}
        # 1) Reglas fijas: respuestas aceptadas (sin gastar el modelo de lenguaje).
        r = ejercicios.revisar_fija(ej, respuesta)
        revisado_por = "reglas"
        if r is None:
            # 2) Traducción distinta de las de referencia: puede estar bien, la juzga el modelo de lenguaje.
            llm.pausar(evitar_modelos or [])
            u = obtener_usuario(user_id)
            juicio = llm.revisar_traduccion(ej["enunciado"], ej["respuestas"], respuesta, ej["idioma"],
                                            u["perfil"], ej["nivel"], time.time() + tiempo_max)
            if "error" in juicio:
                return juicio
            tipos = [e["tipo"] for e in juicio["ediciones"]]
            correcta = juicio["correcta"] and not any(t in progreso.ERRORES_IMPORTANTES for t in tipos)
            r = {"correcta": correcta, "tipos": tipos, "corregida": juicio["corregida"],
                 "ediciones": juicio["ediciones"]}
            revisado_por = "modelo de lenguaje"

        for e in r["ediciones"]:
            registrar_error(user_id, f"{e['original']} -> {e['correccion']}")
        cambio = progreso.registrar_ejercicio(user_id, ej["idioma"], ej["nivel"], r["correcta"], r["tipos"])
        log.info("EJERCICIO | usuario %s: %s %s (revisado por %s)", user_id, ej["id"],
                 "correcta" if r["correcta"] else "incorrecta", revisado_por)
        salida = {
            **ejercicios.publico(ej),
            "respuesta_estudiante": respuesta,
            "correcta": r["correcta"],
            "respuesta_esperada": ej["respuestas"][0],
            "corregida": r["corregida"],
            "ediciones": r["ediciones"],
        }
        if len(ej["respuestas"]) > 1:
            salida["otras_validas"] = ej["respuestas"][1:]
        _anotar_cambio(user_id, salida, cambio)
        return salida
    return await _en_hilo("revisar_respuesta", trabajo)


# ---------------------------------------------------------------- pronunciación (solo inglés)
@mcp.tool()
async def generar_ejercicio_pronunciacion(user_id: UsuarioId) -> dict:
    """Propone una frase en inglés para leer en voz alta, según su nivel y su perfil, y la deja
    como ejercicio activo. Úsala cuando el estudiante quiera practicar pronunciación.
    Solo hay ejercicios de pronunciación en inglés."""
    def trabajo():
        u = obtener_usuario(user_id)
        nivel = obtener_progreso(user_id, "inglés")["nivel"]
        ej = ejercicios.elegir_pronunciacion(user_id, u["perfil"], nivel)
        guardar_ejercicio(user_id, ej["frase"], ej["fonemas"])
        log.info("EJERCICIO | usuario %s: pronunciación, nivel %s (%s)", user_id, ej["nivel"], ej["id"])
        return {"frase": ej["frase"], "nivel": ej["nivel"]}
    return await _en_hilo("generar_ejercicio_pronunciacion", trabajo)


@mcp.tool()
async def evaluar_pronunciacion(
    user_id: UsuarioId,
    ruta_audio: Annotated[str, Field(description="Ruta de la nota de voz (la llena el bot).")],
    transcripcion: Annotated[str | None, Field(description="Lo que entendió Whisper (lo llena el bot).")] = None,
) -> dict:
    """Evalúa la nota de voz del estudiante contra el ejercicio activo y devuelve un puntaje de la
    frase (0 a 10), los sonidos más débiles y las palabras que no se le entendieron. Úsala solo si
    el mensaje indica que el estudiante envió una nota de voz para un ejercicio activo."""
    def trabajo():
        u = obtener_usuario(user_id)
        if not ruta_audio:
            return {"error": "Este mensaje no trae audio."}
        if not u["fonemas_objetivo"]:
            return {"error": "No hay un ejercicio activo. Primero hay que proponer uno."}
        frase = u["frase_objetivo"]

        # 1) ¿Leyó la frase del ejercicio? (si no, no se califica: el puntaje no tendría sentido)
        c = ejercicios.coincidencia(transcripcion, frase) if transcripcion is not None else None
        if c and c["parecido"] < ejercicios.UMBRAL_PARECIDO:
            log.info("PRONUNCIACIÓN | usuario %s: no es la frase (parecido %.2f): %r", user_id, c["parecido"], transcripcion)
            return {"error": f'La nota de voz no parece ser la frase del ejercicio. Se entendió: "{transcripcion}". '
                             f'Pídele que lea en voz alta exactamente: "{frase}". (No se calificó.)'}

        # 2) Evaluador entrenado (wav2vec2 + BiLSTM) contra los fonemas de la frase.
        res = evaluar_audio(ruta_audio, u["fonemas_objetivo"])
        if c:
            # Si Whisper no reconoció muchas palabras, el puntaje no puede ser alto:
            # tope de 4 (no entendió ninguna) a 10 (entendió todas).
            tope = round(4 + 6 * c["entendidas"], 1)
            res["puntaje_evaluador"] = res["puntaje_frase"]
            res["puntaje_frase"] = min(res["puntaje_frase"], tope)
            res["palabras_no_entendidas"] = c["no_entendidas"]
            log.info("PRONUNCIACIÓN | usuario %s: evaluador %.1f, palabras entendidas %.0f%% -> puntaje %.1f",
                     user_id, res["puntaje_evaluador"], 100 * c["entendidas"], res["puntaje_frase"])
        progreso.registrar_pronunciacion(user_id, res["puntaje_frase"])
        return {"frase": frase, **res}
    return await _en_hilo("evaluar_pronunciacion", trabajo)


# ---------------------------------------------------------------- nivel
@mcp.tool()
async def consultar_nivel(user_id: UsuarioId) -> dict:
    """Devuelve el nivel MCER (A1 a C1) del estudiante en inglés y en francés y su progreso:
    frases y ejercicios correctos recientes, errores por tipo, pronunciación y qué le falta para
    subir. Úsala cuando pregunte por su nivel o su progreso."""
    return await _en_hilo("consultar_nivel", progreso.resumen, user_id)


@mcp.tool()
async def cambiar_nivel(
    user_id: UsuarioId,
    idioma: Annotated[str, Field(description='"inglés" o "francés".')],
    nivel: Annotated[str, Field(description="A1, A2, B1, B2 o C1.")],
) -> dict:
    """Cambia a mano el nivel del estudiante en un idioma. Úsala SOLO si el estudiante pide
    explícitamente cambiar su nivel (por ejemplo "ponme en B2"); nunca por tu cuenta."""
    return await _en_hilo("cambiar_nivel", progreso.cambiar_nivel, user_id, idioma, nivel)


@mcp.tool()
async def cancelar_ejercicio(user_id: UsuarioId) -> dict:
    """Cierra el ejercicio activo (de pronunciación o de texto) y vuelve a la conversación libre.
    Úsala si el estudiante dice que ya no quiere hacer el ejercicio."""
    def trabajo():
        guardar_ejercicio(user_id, None, None)   # borra los dos tipos de ejercicio activo
        return {"ok": True}
    return await _en_hilo("cancelar_ejercicio", trabajo)


if __name__ == "__main__":
    log.info("listo, esperando al bot por stdio")
    mcp.run(transport="stdio")
