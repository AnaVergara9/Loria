import time
import random
import logging
from collections import defaultdict, deque

from google.genai import types

from llm import cliente, MODELO_TEXTO, corregir
from db import obtener_usuario, registrar_error, guardar_ejercicio
from pronunciacion import EJERCICIOS_PRONUNCIACION, evaluar_audio

MAX_PASOS = 5  # tope de vueltas del ciclo, evita bucles infinitos

# Memoria de corto plazo: últimos turnos por usuario (solo texto). Se pierde al reiniciar.
historial = defaultdict(lambda: deque(maxlen=8))


# ---------------------------------------------------------------- herramientas
DECLARACIONES = [
    types.FunctionDeclaration(
        name="corregir_gramatica",
        description=(
            "Corrige la gramática de una frase del estudiante en inglés o francés, con ediciones "
            "mínimas y una explicación corta por cada una. También guarda los errores en su perfil. "
            "Úsala siempre que el estudiante escriba o diga una frase para practicar."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "texto": types.Schema(type=types.Type.STRING, description="La frase del estudiante, tal cual."),
            },
            required=["texto"],
        ),
    ),
    types.FunctionDeclaration(
        name="consultar_perfil",
        description=(
            "Devuelve el perfil del estudiante, sus errores frecuentes recientes y si tiene un "
            "ejercicio de pronunciación activo."
        ),
    ),
    types.FunctionDeclaration(
        name="generar_ejercicio",
        description=(
            "Propone una frase en inglés para practicar pronunciación y deja el ejercicio activo. "
            "Úsala cuando el estudiante quiera practicar pronunciación. Solo hay ejercicios en inglés."
        ),
    ),
    types.FunctionDeclaration(
        name="evaluar_pronunciacion",
        description=(
            "Evalúa la nota de voz del estudiante contra el ejercicio activo y devuelve un puntaje "
            "de la frase y los sonidos más débiles. Solo úsala si el mensaje indica que el estudiante "
            "envió audio para un ejercicio activo."
        ),
    ),
]


def ejecutar(nombre: str, args: dict, ctx: dict) -> dict:
    """Ejecuta una herramienta. Siempre devuelve un dict; si algo falla, devuelve {'error': ...}."""
    uid = ctx["user_id"]
    try:
        if nombre == "corregir_gramatica":
            usuario = obtener_usuario(uid)
            r = corregir(args.get("texto", ""), usuario["perfil"], usuario["errores_frecuentes"])
            for e in r.get("ediciones", []):
                registrar_error(uid, f"{e['original']} -> {e['correccion']}")
            return r

        if nombre == "consultar_perfil":
            u = obtener_usuario(uid)
            return {
                "perfil": u["perfil"],
                "errores_frecuentes": u["errores_frecuentes"] or "ninguno todavía",
                "ejercicio_activo": u["frase_objetivo"],
            }

        if nombre == "generar_ejercicio":
            ej = random.choice(EJERCICIOS_PRONUNCIACION)
            guardar_ejercicio(uid, ej["frase"], ej["fonemas"])
            return {"frase": ej["frase"]}

        if nombre == "evaluar_pronunciacion":
            u = obtener_usuario(uid)
            if not ctx.get("ruta_audio"):
                return {"error": "Este mensaje no trae audio."}
            if not u["fonemas_objetivo"]:
                return {"error": "No hay un ejercicio activo. Primero hay que proponer uno."}
            res = evaluar_audio(ctx["ruta_audio"], u["fonemas_objetivo"])
            guardar_ejercicio(uid, None, None)  # cierra el ejercicio
            return {"frase": u["frase_objetivo"], **res}

        return {"error": f"Herramienta desconocida: {nombre}"}
    except Exception as e:
        logging.exception("Error en herramienta %s", nombre)
        return {"error": str(e)}


# ---------------------------------------------------------------- instrucciones
def construir_instruccion(perfil: str) -> str:
    tono = (
        "Hablas con un niño de 7 a 11 años: sé muy amable, usa emojis, ejemplos divertidos y palabras simples."
        if perfil == "nino"
        else "Hablas con un estudiante adulto: sé claro, respetuoso, directo y motivador."
    )
    return f"""Eres Loria 🦜, un tutor de idiomas por Telegram para hispanohablantes que practican inglés y francés. {tono}

Tienes herramientas. En cada turno decide cuál usar:
- Si el estudiante escribe o dice una frase en inglés o francés: llama primero a corregir_gramatica con esa frase.
- Si quiere practicar pronunciación: llama a generar_ejercicio. Solo hay ejercicios en inglés.
- Si el mensaje dice que envió una nota de voz para el ejercicio activo: llama a evaluar_pronunciacion.
- Si necesitas recordar sus errores: llama a consultar_perfil.
- Para saludos o dudas generales no hace falta herramienta.

Cómo responder al final (texto plano, sin Markdown, máximo 8 líneas):
- Después de corregir_gramatica: muestra la frase corregida y como máximo 3 ediciones con su explicación breve en español. No inventes correcciones que la herramienta no dio. Si no hubo errores, felicítalo. Luego responde al contenido de lo que dijo con 1 o 2 frases en el idioma que practica y haz una pregunta corta para seguir la conversación.
- Después de generar_ejercicio: presenta la frase y pídele que envíe una nota de voz leyéndola.
- Después de evaluar_pronunciacion: comenta cómo le fue en general sin mostrar números ni símbolos fonéticos. Si la herramienta marca sonidos débiles, preséntalos como una sugerencia prudente ("parece que la 'th' pudo sonar parecida a una 't'") y explica máximo 2 con ejemplos cotidianos (por ejemplo, la 'th' de 'think' se hace sacando un poquito la punta de la lengua entre los dientes). Nunca afirmes con certeza que pronunció mal un sonido. Si no hay sonidos débiles, felicítalo pero sin exagerar.
Nunca afirmes un puntaje ni una corrección que no vengan de una herramienta."""


# ---------------------------------------------------------------- ciclo ReAct
def responder(user_id: int, mensaje: str, perfil: str = "adulto", ruta_audio: str | None = None):
    """Devuelve (texto_de_respuesta, traza). La traza es la lista de acciones y observaciones."""
    ctx = {"user_id": user_id, "ruta_audio": ruta_audio}
    msg_usuario = types.Content(role="user", parts=[types.Part(text=mensaje)])
    contenidos = list(historial[user_id]) + [msg_usuario]

    config = types.GenerateContentConfig(
        system_instruction=construir_instruccion(perfil),
        tools=[types.Tool(function_declarations=DECLARACIONES)],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    traza = []
    for paso in range(1, MAX_PASOS + 1):
        resp = cliente.models.generate_content(model=MODELO_TEXTO, contents=contenidos, config=config)
        if not resp.candidates or resp.candidates[0].content is None:
            return "No pude generar una respuesta, intenta reformular tu mensaje.", traza

        # Se agrega el contenido del modelo tal cual (conserva las firmas de razonamiento de Gemini 3).
        contenidos.append(resp.candidates[0].content)
        llamadas = resp.function_calls or []

        if not llamadas:  # el modelo ya tiene lo necesario: responde
            texto = (resp.text or "").strip()
            historial[user_id].append(msg_usuario)
            historial[user_id].append(types.Content(role="model", parts=[types.Part(text=texto)]))
            return texto, traza

        partes = []
        for fc in llamadas:  # ACTUAR -> OBSERVAR
            args = dict(fc.args or {})
            t0 = time.time()
            resultado = ejecutar(fc.name, args, ctx)
            dt = time.time() - t0
            linea = f"Paso {paso}: {fc.name}({args}) -> {str(resultado)[:150]} [{dt:.1f}s]"
            traza.append(linea)
            logging.info("ReAct | %s", linea)
            partes.append(types.Part.from_function_response(name=fc.name, response={"resultado": resultado}))
        contenidos.append(types.Content(role="user", parts=partes))

    return "Me enredé un poco con tu mensaje, ¿puedes intentarlo de nuevo?", traza
