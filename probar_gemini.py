"""Mide qué modelo de Gemini responde y cuánto tarda. Uso: python probar_gemini.py"""
import time
from google.genai import types
from llm import MODELOS, llamar, PENSAR_POCO

cfg = types.GenerateContentConfig(thinking_config=PENSAR_POCO)
for m in MODELOS:
    t = time.time()
    try:
        r = llamar(m, "Say hello in five words.", cfg, reintentos=0)
        print(f"{m}: OK en {time.time()-t:.1f}s -> {r.text.strip()[:60]}")
    except Exception as e:
        print(f"{m}: FALLO en {time.time()-t:.1f}s -> {getattr(e, 'code', type(e).__name__)} {str(e)[:90]}")
