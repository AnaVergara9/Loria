"""Banco de ejercicios de Loria: cuál proponer a cada estudiante y cómo revisar su respuesta.

Las frases están en datos/ejercicios.json (se pueden agregar sin tocar código):
- "pronunciacion": frases en inglés para leer en voz alta, con sus fonemas (scripts/generar_fonemas.py).
- "texto": ejercicios de inglés y francés para responder por escrito:
    * "completar": una frase con un espacio ___ y las respuestas aceptadas.
    * "traducir": una frase en español y algunas traducciones de referencia.
    * "elegir": una pregunta con 3 opciones que se tocan como botones (solo modo niños).

Cada ejercicio tiene un perfil ("adulto" o "nino") y un nivel MCER. Los niños solo tienen inglés.
"""
import os
import re
import json
import random
import unicodedata

from tutor.progreso import NIVELES

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # carpeta del proyecto
ARCHIVO = os.path.join(RAIZ, "datos", "ejercicios.json")

with open(ARCHIVO, encoding="utf-8") as _f:
    _datos = json.load(_f)
PRONUNCIACION = _datos["pronunciacion"]
TEXTO = _datos["texto"]
for _n, _ej in enumerate(PRONUNCIACION):
    _ej["id"] = f"p{_n}"
for _n, _ej in enumerate(TEXTO):
    _ej["id"] = f"t{_n}"


def _i(nivel: str) -> int:
    return NIVELES.index(nivel) if nivel in NIVELES else 0


# ---------------------------------------------------------------- elegir
def _candidatos(lista: list, nivel: str) -> list:
    """Ejercicios de su nivel o uno más fácil (los de su nivel son los que lo hacen subir).
    Si no hay (por ejemplo, un niño en B2), cualquiera hasta su nivel, y si no, todos."""
    i = _i(nivel)
    cerca = [ej for ej in lista if i - 1 <= _i(ej["nivel"]) <= i]
    return cerca or [ej for ej in lista if _i(ej["nivel"]) <= i] or lista


# Rotación: se recorren todos los candidatos en orden aleatorio antes de repetir,
# y nunca el mismo dos veces seguidas. Se guarda en memoria (se reinicia con el bot).
_bolsas: dict = {}
_ultimo: dict = {}


def _rotar(clave: tuple, candidatos: list) -> dict:
    ids = {ej["id"]: ej for ej in candidatos}
    bolsa = [i for i in _bolsas.get(clave, []) if i in ids]
    if not bolsa:
        bolsa = list(ids)
        random.shuffle(bolsa)
        if len(bolsa) > 1 and bolsa[-1] == _ultimo.get(clave):
            bolsa[0], bolsa[-1] = bolsa[-1], bolsa[0]
    elegido = bolsa.pop()
    _bolsas[clave] = bolsa
    _ultimo[clave] = elegido
    return ids[elegido]


def elegir_pronunciacion(user_id: int, perfil: str, nivel: str) -> dict:
    lista = [ej for ej in PRONUNCIACION if ej["perfil"] == perfil] or PRONUNCIACION
    return _rotar((user_id, "pronunciacion"), _candidatos(lista, nivel))


def elegir_texto(user_id: int, idioma: str, perfil: str, nivel: str) -> dict | None:
    """None si no hay ejercicios para ese idioma y perfil (los niños solo tienen inglés)."""
    lista = [ej for ej in TEXTO if ej["idioma"] == idioma and ej["perfil"] == perfil]
    if not lista:
        return None
    return _rotar((user_id, "texto", idioma), _candidatos(lista, nivel))


# ---------------------------------------------------------------- revisar
def normalizar(texto: str, tildes: bool = True) -> str:
    """Para comparar respuestas: minúsculas, sin puntuación ni espacios de más (y opcionalmente sin tildes)."""
    t = texto.lower().replace("’", "'").replace("‘", "'")
    t = re.sub(r"\([^)]*\)", " ", t)          # quita pistas entre paréntesis, como "(café)"
    t = re.sub(r"[^\w' ]", " ", t)            # quita puntuación, emojis y otros símbolos
    t = " ".join(t.split())
    if not tildes:
        t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    return t


def _formas_aceptadas(ej: dict) -> list:
    """Respuestas que se aceptan sin preguntarle al modelo de lenguaje."""
    if "___" in ej["enunciado"]:
        # La palabra sola ("went") o la frase completa ("Yesterday I went to the supermarket.")
        formas = list(ej["respuestas"])
        for r in ej["respuestas"]:
            pegada = r.startswith("'")  # contracciones: "I'm", no "I 'm"
            formas.append(ej["enunciado"].replace(" ___" if pegada else "___", r))
        return formas
    return list(ej["respuestas"])


def revisar_fija(ej: dict, respuesta: str) -> dict | None:
    """Revisa sin modelo de lenguaje. Devuelve el resultado, o None si hace falta el modelo
    (una traducción distinta de las de referencia puede estar bien)."""
    esperada = ej["respuestas"][0]
    if not respuesta.strip():
        return {"correcta": False, "tipos": [ej.get("area", "gramática")], "corregida": esperada, "ediciones": []}

    formas = _formas_aceptadas(ej)
    if normalizar(respuesta) in {normalizar(f) for f in formas}:
        return {"correcta": True, "tipos": [], "corregida": respuesta.strip(), "ediciones": []}

    if normalizar(respuesta, tildes=False) in {normalizar(f, tildes=False) for f in formas}:
        # Solo le faltó o le sobró una tilde: está bien, pero se le muestra (cuenta como error leve).
        return {"correcta": True, "tipos": ["ortografía"], "corregida": esperada,
                "ediciones": [{"original": respuesta.strip(), "correccion": esperada, "tipo": "ortografía",
                               "explicacion": "Está bien, solo revisa las tildes."}]}

    if ej["tipo"] in ("completar", "elegir"):   # respuestas cerradas: no hace falta el modelo
        return {"correcta": False, "tipos": [ej.get("area", "gramática")], "corregida": esperada, "ediciones": []}
    return None


def publico(ej: dict) -> dict:
    """Lo que se le muestra al estudiante (y al modelo) ANTES de responder: nunca la respuesta."""
    datos = {"id": ej["id"], "tipo": ej["tipo"], "idioma": ej["idioma"], "nivel": ej["nivel"],
             "enunciado": ej["enunciado"]}
    if ej.get("pista"):
        datos["pista"] = ej["pista"]
    if ej.get("opciones"):
        datos["opciones"] = ej["opciones"]
    return datos


# ---------------------------------------------------------------- ¿la nota de voz es la frase del ejercicio?
_UNIDADES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
             "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_DECENAS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def _numero_en_palabras(n: int) -> str:
    """Whisper a veces escribe "9:30" en vez de "nine thirty": se pasan a palabras (0 a 99)."""
    if n < 20:
        return _UNIDADES[n]
    if n < 100:
        return _DECENAS[n // 10] + ("" if n % 10 == 0 else " " + _UNIDADES[n % 10])
    return str(n)


def _palabras(texto: str) -> list:
    t = re.sub(r"\d+", lambda m: " " + _numero_en_palabras(int(m.group())) + " ", texto)
    t = re.sub(r"[^\w' ]", " ", normalizar(t, tildes=False))
    return t.split()


# Por debajo de este parecido, la nota de voz se considera otra frase y no se califica.
# Medido: frases mal pronunciadas ("I sink de wedder...") dan 0,56 o más; frases distintas o en español, 0,35 o menos.
UMBRAL_PARECIDO = 0.45


def coincidencia(transcripcion: str, frase: str) -> dict:
    """Compara lo que entendió Whisper con la frase del ejercicio, palabra por palabra.

    - parecido: de 0 a 1, qué tanto se parecen letra por letra. Una frase mal pronunciada
      ("I sink de wedder") se sigue pareciendo; una frase distinta o en español, no.
    - entendidas: fracción de palabras de la frase que Whisper sí reconoció.
    - no_entendidas: palabras de la frase que no aparecen en lo que entendió.
    """
    import difflib
    dicho, esperado = _palabras(transcripcion), _palabras(frase)
    parecido = (difflib.SequenceMatcher(None, " ".join(dicho), " ".join(esperado)).ratio()
                if dicho and esperado else 0.0)
    restantes = list(dicho)
    no_entendidas = []
    for p in esperado:
        if p in restantes:
            restantes.remove(p)
        else:
            no_entendidas.append(p)
    entendidas = 1 - len(no_entendidas) / len(esperado) if esperado else 0.0
    return {"parecido": round(parecido, 2), "entendidas": round(entendidas, 2), "no_entendidas": no_entendidas}
