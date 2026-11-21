"""Prueba cada modelo de la cadena de respaldo por separado y luego la cadena completa.

Uso:  python scripts/probar_modelos.py
Para ver el paso a Groq sin esperar a que Gemini falle de verdad:
      $env:LLM_SIMULAR_FALLO="gemini"; python scripts/probar_modelos.py; Remove-Item Env:LLM_SIMULAR_FALLO
"""
import os
import sys
import json
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # para importar los módulos del proyecto

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
for _n in ("httpx", "google_genai", "groq"):
    logging.getLogger(_n).setLevel(logging.WARNING)

from modelos_lenguaje import llm

FRASE = "Yesterday I go to the cinema with my friends."
HERRAMIENTA = [{
    "nombre": "corregir_gramatica",
    "descripcion": "Corrige la gramática de una frase del estudiante.",
    "parametros": {"type": "object", "properties": {"texto": {"type": "string"}}, "required": ["texto"]},
}]

print(f"\nCadena: {llm.describir_cadena()}")
if llm.SIMULAR_FALLO:
    print(f"(simulando fallo de: {', '.join(sorted(llm.SIMULAR_FALLO))})")

print("\n== 1. Cada modelo por separado: JSON y elección de herramienta ==")
for nombre_prov, modelo in llm.CADENA:
    prov = llm.PROVEEDORES[nombre_prov]
    for prueba in ("json", "herramienta"):
        t = time.time()
        try:
            if prueba == "json":
                crudo = llm.llamar_con_tope(prov.generar_json, modelo, "Corrige la frase.", FRASE,
                                           llm.ESQUEMA_CORRECCION, 0.2, segundos=llm.TIEMPO_POR_INTENTO)
                salida = json.loads(crudo)["corregida"]
            else:
                r = llm.llamar_con_tope(prov.paso, modelo, "Usa la herramienta para corregir lo que escriba el estudiante.",
                                        [{"rol": "usuario", "texto": FRASE}], HERRAMIENTA,
                                        segundos=llm.TIEMPO_POR_INTENTO)
                salida = [l["nombre"] for l in r["llamadas"]] or "no eligió herramienta"
            print(f"  OK     {nombre_prov}/{modelo:24} {prueba:11} {time.time() - t:4.1f}s -> {salida}")
        except Exception as e:
            print(f"  FALLO  {nombre_prov}/{modelo:24} {prueba:11} {time.time() - t:4.1f}s -> {llm._motivo(e)[0]}")

print("\n== 2. Cadena completa (lo que hace el bot) ==")
print(" ", llm.corregir(FRASE))
