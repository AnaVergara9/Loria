import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
cliente = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELO_TEXTO = "gemini-3.8-flash"


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

    try:
        respuesta = cliente.models.generate_content(
            model=MODELO_TEXTO,
            contents=texto,
            config=types.GenerateContentConfig(
                system_instruction=instruccion,
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        return json.loads(respuesta.text)
    except Exception as e:
        print(f"Error en corregir: {e}")
        return {"idioma": "otro", "corregida": texto, "ediciones": []}
