import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
cliente = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

INSTRUCCION = """Eres un tutor de idiomas para hispanohablantes.
El estudiante escribe en inglés o en francés. Detecta el idioma.
Corrige únicamente lo que es incorrecto, sin cambiar el estilo ni reescribir la frase.
Responde solo con JSON con estas claves:
- idioma: "inglés" o "francés"
- corregida: la frase corregida (igual a la original si no hay errores)
- ediciones: lista de máximo 3 objetos con "original", "correccion" y "explicacion"
La explicacion va en español, con palabras sencillas y en una sola frase.
Si no hay errores, ediciones es una lista vacía."""

def corregir(texto: str) -> dict:
    respuesta = cliente.models.generate_content(
        model="gemini-2.5-flash",
        contents=texto,
        config=types.GenerateContentConfig(
            system_instruction=INSTRUCCION,
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    return json.loads(respuesta.text)