"""Adaptador de Gemini: traduce entre el formato neutro de llm.py y la librería google-genai.

Formato neutro de los mensajes (el mismo para Gemini y Groq):
    {"rol": "usuario",     "texto": "..."}
    {"rol": "asistente",   "texto": "...", "llamadas": [{"id", "nombre", "args"}]}
    {"rol": "herramienta", "id": "...", "nombre": "...", "resultado": {...}}
"""
import os

from google import genai
from google.genai import types

NOMBRE = "gemini"

# Razonamiento bajo: el tutor no necesita pensar a fondo y así responde mucho más rápido.
PENSAR_POCO = types.ThinkingConfig(thinking_level="low")

_cliente = None


def disponible() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def _cli():
    global _cliente
    if _cliente is None:
        _cliente = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _cliente


def _http(timeout: float):
    # Tiempo máximo de espera de ESTA llamada (la librería lo pide en milisegundos).
    return types.HttpOptions(timeout=int(timeout * 1000))


def generar_json(modelo, instruccion, texto, esquema, temperatura, timeout) -> str:
    """Pide una respuesta que cumpla el esquema JSON. Devuelve el texto JSON."""
    config = types.GenerateContentConfig(
        system_instruction=instruccion,
        response_mime_type="application/json",
        response_json_schema=esquema,
        temperature=temperatura,
        thinking_config=PENSAR_POCO,
        http_options=_http(timeout),
    )
    r = _cli().models.generate_content(model=modelo, contents=texto, config=config)
    return r.text or ""


def paso(modelo, sistema, mensajes, herramientas, timeout) -> dict:
    """Una sola llamada al modelo. Devuelve un mensaje neutro del asistente."""
    config = types.GenerateContentConfig(
        system_instruction=sistema,
        tools=[types.Tool(function_declarations=[
            types.FunctionDeclaration(
                name=h["nombre"], description=h["descripcion"], parameters_json_schema=h["parametros"]
            ) for h in herramientas
        ])] if herramientas else None,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        thinking_config=PENSAR_POCO,
        http_options=_http(timeout),
    )
    r = _cli().models.generate_content(model=modelo, contents=_a_gemini(mensajes), config=config)
    if not r.candidates or r.candidates[0].content is None:
        raise ValueError("Gemini devolvió una respuesta vacía")
    if str(r.candidates[0].finish_reason).endswith("MAX_TOKENS"):
        raise ValueError("respuesta cortada a la mitad (límite de longitud)")  # que responda otro modelo

    contenido = r.candidates[0].content
    llamadas = [
        {"id": fc.id or f"llamada_{i}", "nombre": fc.name, "args": dict(fc.args or {})}
        for i, fc in enumerate(r.function_calls or [])
    ]
    texto = "".join(p.text for p in (contenido.parts or []) if p.text and not p.thought)
    # "_nativo" guarda el contenido original: Gemini 3 exige recibir de vuelta sus
    # "firmas de razonamiento" cuando se le devuelve el resultado de una herramienta.
    return {"rol": "asistente", "texto": texto.strip(), "llamadas": llamadas, "_nativo": (NOMBRE, contenido)}


def _a_gemini(mensajes: list) -> list:
    """Convierte la conversación neutra al formato de Gemini."""
    salida = []
    for m in mensajes:
        if m["rol"] == "usuario":
            salida.append(types.Content(role="user", parts=[types.Part(text=m["texto"])]))
        elif m["rol"] == "asistente":
            nativo = m.get("_nativo")
            if nativo and nativo[0] == NOMBRE:
                salida.append(nativo[1])
            else:
                salida.append(types.Content(role="model", parts=[types.Part(text=m["texto"] or "...")]))
        elif m["rol"] == "herramienta":
            parte = types.Part.from_function_response(name=m["nombre"], response={"resultado": m["resultado"]})
            anterior = salida[-1] if salida else None
            # Varias respuestas de herramientas seguidas van juntas en un mismo mensaje.
            if anterior is not None and anterior.role == "user" and anterior.parts and anterior.parts[0].function_response:
                anterior.parts.append(parte)
            else:
                salida.append(types.Content(role="user", parts=[parte]))
    return salida
