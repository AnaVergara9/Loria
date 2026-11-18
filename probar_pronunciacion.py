import sys
from pronunciacion import EJERCICIOS_PRONUNCIACION, vocab, evaluar_audio, UMBRAL_FONEMA

print("\n== Fonemas de los ejercicios que NO están en el vocabulario del modelo ==")
for i, ej in enumerate(EJERCICIOS_PRONUNCIACION, 1):
    faltan = [f for f in ej["fonemas"].split() if f not in vocab]
    print(f'{i}. {ej["frase"]} -> {faltan or "ninguno"}')

if len(sys.argv) > 1:
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    ej = EJERCICIOS_PRONUNCIACION[n - 1]
    print(f'\n== Evaluando "{sys.argv[1]}" contra: {ej["frase"]} ==')
    r = evaluar_audio(sys.argv[1], ej["fonemas"], detalle=True)
    print("Puntaje de la frase (0 a 10):", r["puntaje_frase"])
    print(f"Fonemas marcados como débiles (puntaje < {UMBRAL_FONEMA}):", r["peores_fonemas"] or "ninguno")
    print("\nPuntaje de cada fonema (0 a 2), de peor a mejor:")
    for f, s in sorted(r["detalle"], key=lambda x: x[1]):
        print(f"  {f:>3}  {s:.2f}")
