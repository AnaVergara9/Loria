"""
Diagnóstico de Gemini. Uso: python diagnostico_gemini.py   (tarda unos 2-4 minutos si hay fallos)

Prueba 1: el MISMO modelo 4 veces seguidas.
   - falla la primera y luego responde  -> calentamiento de la conexión
   - falla de forma intermitente        -> inestabilidad del servicio
Prueba 2: dos rondas con los modelos en orden aleatorio.
   - falla siempre el mismo modelo      -> problema de ese modelo
   - fallan los primeros de cada ronda  -> calentamiento / conexión
"""
import time
import random
from google.genai import types
from llm import MODELOS, llamar, PENSAR_POCO

cfg = types.GenerateContentConfig(thinking_config=PENSAR_POCO)


def intento(modelo):
    t = time.time()
    try:
        llamar(modelo, "Say hello in five words.", cfg, reintentos=0)
        return f"OK     {time.time() - t:4.1f}s"
    except Exception as e:
        return f"FALLO  {time.time() - t:4.1f}s  {getattr(e, 'code', type(e).__name__)}"


principal = MODELOS[0]
print(f"\nPrueba 1: {principal} cuatro veces seguidas")
for i in range(4):
    print(f"  intento {i + 1}: {intento(principal)}")

print("\nPrueba 2: dos rondas en orden aleatorio")
for ronda in range(2):
    for m in random.sample(MODELOS, len(MODELOS)):
        print(f"  ronda {ronda + 1}  {m:18}  {intento(m)}")
