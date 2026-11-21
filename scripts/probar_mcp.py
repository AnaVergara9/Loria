"""Prueba el servidor MCP sin Telegram: lo lanza, lista sus herramientas y llama algunas.

Uso:  python scripts/probar_mcp.py            (usa un usuario de prueba, id 1, y lo borra al final)
"""
import json
import logging
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # para importar los módulos del proyecto

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
for _n in ("httpx", "google_genai", "mcp"):
    logging.getLogger(_n).setLevel(logging.WARNING)

from agente.cliente_mcp import cliente
from tutor.db import eliminar_usuario

USUARIO_PRUEBA = 1
ctx = {"user_id": USUARIO_PRUEBA}

print("\nLanzando el servidor MCP (la primera vez tarda por wav2vec2)...")
cliente.iniciar()

print("\n== 1. Lo que el servidor declara (incluye los parámetros de contexto) ==")
for h in cliente.herramientas:
    print(f"- {h.name}: {json.dumps(h.input_schema.get('properties', {}), ensure_ascii=False)[:150]}")

print("\n== 2. Lo que ve el modelo de lenguaje (sin user_id ni ruta_audio) ==")
for h in cliente.herramientas_para_modelo():
    print(f"- {h['nombre']}({', '.join(h['parametros']['properties'])})")

print("\n== 3. Llamadas de prueba ==")
print("generar_ejercicio_pronunciacion ->", cliente.llamar("generar_ejercicio_pronunciacion", {}, ctx))
print("consultar_perfil   ->", cliente.llamar("consultar_perfil", {}, ctx))
ej = cliente.llamar("generar_ejercicio_texto", {"idioma": "inglés"}, ctx)
print("generar_ejercicio_texto ->", ej)
print("revisar_respuesta (vacía = se rinde, no gasta el modelo) ->",
      cliente.llamar("revisar_respuesta", {"respuesta": ""}, ctx))
print("corregir_gramatica ->", cliente.llamar("corregir_gramatica", {"texto": "She don't like apples."},
                                              {**ctx, "tiempo_max": 40}))
print("cancelar_ejercicio ->", cliente.llamar("cancelar_ejercicio", {}, ctx))
print("modelo intenta user_id ajeno ->",
      cliente.llamar("consultar_perfil", {"user_id": 999}, ctx), "(debe ser el perfil del usuario 1)")

eliminar_usuario(USUARIO_PRUEBA)
cliente.cerrar()
print("\nListo.")
