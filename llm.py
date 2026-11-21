import os
import json
import time
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

load_dotenv()
cliente = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(timeout=20000),  # 20 s por llamada (milisegundos)
)

# gemini-3.5-flash es el principal (versión estable; en la prueba del 20/11 respondió en 2 s,
# mientras 3.7 y 3.8 daban 504). El primero es el principal; si está saturado se prueba el siguiente.
# Verifica en https://ai.google.dev/gemini-api/docs/models que estos nombres sigan vigentes
# y que tu clave gratuita pueda usarlos.
MODELOS = os.getenv("GEMINI_MODELOS", "gemini-3.5-flash,gemini-3.7-flash,gemini-3.8-flash").split(",")

# Razonamiento bajo: el tutor no necesita pensar a fondo y así responde mucho más rápido.
# Requiere google-genai >= 1.51 (pip install -U google-genai).
PENSAR_POCO = types.ThinkingConfig(thinking_level="low")
MODELO_TEXTO = MODELOS[0]

CODIGOS_REINTENTO = {429, 500, 502, 503, 504}  # saturación o fallo temporal del servidor


NOMBRES_ERROR_RED = ("Timeout", "ConnectError", "ReadError", "WriteError",
                     "RemoteProtocolError", "NetworkError", "TimedOut", "ConnectionError")


def es_error_de_red(e: Exception) -> bool:
    """True si el error es de conexión (cortes, DNS, tiempo de lectura agotado), de cualquier librería."""
    return any(n in type(e).__name__ for n in NOMBRES_ERROR_RED)


def llamar(modelo, contents, config, reintentos=1, limite=None):
    """Llama a un modelo y reintenta con espera corta si el servidor está saturado.

    `limite` es un instante (time.time()) después del cual ya no se intenta nada más.
    """
    for i in range(reintentos + 1):
        if limite is not None and time.time() >= limite:
            raise TimeoutError("Se agotó el tiempo máximo para responder.")
        try:
            return cliente.models.generate_content(model=modelo, contents=contents, config=config)
        except Exception as e:
            transitorio = (
                isinstance(e, errors.APIError) and getattr(e, "code", None) in CODIGOS_REINTENTO
            ) or es_error_de_red(e)
            if transitorio and i < reintentos:
                logging.warning("Gemini %s falló (%s); reintento %s/%s", modelo,
                                getattr(e, "code", type(e).__name__), i + 1, reintentos)
                time.sleep(2 * (i + 1))
                continue
            raise


def corregir(texto: str, perfil: str = "adulto", errores_previos: str = "") -> dict:
    """Corrección gramatical con ediciones mínimas. El LLM detecta el idioma (inglés o francés)."""
    tono = (
        "Hablas con un niño de 7 a 11 años: sé muy amable, usa emojis, ejemplos divertidos y palabras súper simples."
        if perfil == "nino"
        else "Hablas con un estudiante adulto: sé claro, respetuoso, directo y motivador."
    )
    contexto_errores = (
        f"\nErrores frecuentes previos del estudiante (priorízalos si reaparecen): {errores_previos}"
        if errores_previos else ""
    )

    instruccion = f"""Eres Loria, un tutor de idiomas para hispanohablantes. {tono}
El estudiante practica inglés o francés. Detecta en cuál de los dos está escrito el texto.
Corrige únicamente lo que es incorrecto en ese idioma, sin cambiar el estilo ni reescribir la frase.{contexto_errores}
Responde solo con JSON con estas claves en este orden exacto:
- idioma: "inglés", "francés" u "otro"
- corregida: la frase corregida (igual a la original si no hay errores)
- ediciones: lista de máximo 3 objetos con "original", "correccion" y "explicacion"
La explicacion va en español, en una sola frase corta y fácil de entender.
Si no hay errores, ediciones es una lista vacía.
Si el texto no está en inglés ni en francés, idioma es "otro" y ediciones es una lista vacía."""

    config = types.GenerateContentConfig(
        system_instruction=instruccion,
        response_mime_type="application/json",
        temperature=0.2,
        thinking_config=PENSAR_POCO,
    )
    limite = time.time() + 25  # presupuesto de tiempo para toda la corrección
    for modelo in MODELOS:
        try:
            respuesta = llamar(modelo, texto, config, limite=limite)
            return json.loads(respuesta.text)
        except TimeoutError:
            logging.warning("corregir: se agotó el tiempo")
            break
        except Exception as e:
            if isinstance(e, errors.APIError) or es_error_de_red(e):
                logging.warning("corregir: %s falló (%s), probando el siguiente modelo", modelo,
                                getattr(e, "code", type(e).__name__))
                continue
            logging.exception("corregir: respuesta inválida")  # p. ej. JSON mal formado
            break
    return {"error": "El servicio de corrección no está disponible en este momento."}
