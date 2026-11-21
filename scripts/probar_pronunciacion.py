"""Revisa el banco de pronunciación y, si se le da un audio, lo evalúa con detalle.

Uso:
    python scripts/probar_pronunciacion.py                    revisa que todos los fonemas existan en el modelo
    python scripts/probar_pronunciacion.py audio.ogg 3        evalúa audio.ogg contra la frase número 3
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # para importar los módulos del proyecto
sys.stdout.reconfigure(encoding="utf-8")  # la consola de Windows no muestra IPA sin esto

from tutor.ejercicios import PRONUNCIACION
from tutor.pronunciacion import vocab, evaluar_audio, UMBRAL_FONEMA

print("\n== Fonemas de los ejercicios que NO están en el vocabulario del modelo ==")
malos = 0
for i, ej in enumerate(PRONUNCIACION, 1):
    if not ej.get("fonemas"):
        print(f'{i}. {ej["frase"]} -> SIN FONEMAS (ejecuta python scripts/generar_fonemas.py)')
        malos += 1
        continue
    faltan = [f for f in ej["fonemas"].split() if f not in vocab]
    malos += bool(faltan)
    print(f'{i:>2}. [{ej["perfil"]:>6} {ej["nivel"]}] {ej["frase"]} -> {faltan or "ok"}')
print(f"\n{len(PRONUNCIACION)} frases, {malos} con problemas.")

if len(sys.argv) > 1:
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    ej = PRONUNCIACION[n - 1]
    print(f'\n== Evaluando "{sys.argv[1]}" contra: {ej["frase"]} ==')
    r = evaluar_audio(sys.argv[1], ej["fonemas"], detalle=True)
    print("Puntaje de la frase (0 a 10):", r["puntaje_frase"])
    print(f"Fonemas marcados como débiles (puntaje < {UMBRAL_FONEMA}):", r["peores_fonemas"] or "ninguno")
    print("\nPuntaje de cada fonema (0 a 2), de peor a mejor:")
    for f, s in sorted(r["detalle"], key=lambda x: x[1]):
        print(f"  {f:>3}  {s:.2f}")
