"""Llena los fonemas de las frases de pronunciación de ejercicios.json.

Para agregar una frase nueva: escríbela en ejercicios.json SIN "fonemas" y ejecuta
    python scripts/generar_fonemas.py
El script busca cada palabra en el diccionario de pronunciación CMU (inglés americano, público)
y la convierte a los símbolos IPA que usa el evaluador. Las frases que ya tienen fonemas no se tocan
(con  python scripts/generar_fonemas.py --todas  se vuelven a calcular todas).

El diccionario (cmudict.dict, unos 3,5 MB) se descarga solo la primera vez y no se sube a GitHub.
"""
import os
import re
import sys
import json
import urllib.request

CARPETA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos")
ARCHIVO = os.path.join(CARPETA, "ejercicios.json")
DICCIONARIO = os.path.join(CARPETA, "cmudict.dict")
URL_DICCIONARIO = "https://raw.githubusercontent.com/cmusphinx/cmudict/master/cmudict.dict"

# ARPAbet (CMU) -> IPA, con los mismos símbolos que las frases originales del evaluador.
# El modelo wav2vec2 no tiene "ɝ", así que la R vocálica es siempre "ɚ".
ARPABET_A_IPA = {
    "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ", "EH": "ɛ", "ER": "ɚ",
    "EY": "eɪ", "IH": "ɪ", "IY": "i", "OW": "oʊ", "OY": "ɔɪ", "UH": "ʊ", "UW": "u",
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "F": "f", "G": "ɡ", "HH": "h", "JH": "dʒ", "K": "k",
    "L": "l", "M": "m", "N": "n", "NG": "ŋ", "P": "p", "R": "ɹ", "S": "s", "SH": "ʃ", "T": "t",
    "TH": "θ", "V": "v", "W": "w", "Y": "j", "Z": "z", "ZH": "ʒ",
}


# Palabras que se escriben igual pero suenan distinto ("I read" hoy / ayer): se fija la que usan las frases.
PREFERIDAS = {
    "read": "R IY1 D",    # presente (el diccionario pone primero el pasado, "red")
    "live": "L IH1 V",    # verbo vivir
    "close": "K L OW1 Z", # verbo cerrar
}


def cargar_diccionario() -> dict:
    if not os.path.exists(DICCIONARIO):
        print("Descargando el diccionario CMU (solo la primera vez)...")
        urllib.request.urlretrieve(URL_DICCIONARIO, DICCIONARIO)
    dic = {}
    with open(DICCIONARIO, encoding="utf-8") as f:
        for linea in f:
            partes = linea.split("#")[0].split()
            if not partes or "(" in partes[0]:   # "word(2)" es una variante: se usa la primera
                continue
            dic[partes[0]] = partes[1:]
    dic.update({palabra: f.split() for palabra, f in PREFERIDAS.items()})
    return dic


def a_ipa(fonema_cmu: str) -> str:
    base, acento = fonema_cmu.rstrip("012"), fonema_cmu[len(fonema_cmu.rstrip("012")):]
    if base == "AH" and acento == "0":
        return "ə"   # vocal débil (schwa), como en "the" o "today"
    return ARPABET_A_IPA[base]


def fonemas_de(frase: str, dic: dict) -> tuple:
    """Devuelve (fonemas, palabras_que_no_están_en_el_diccionario)."""
    palabras = re.findall(r"[a-z']+", frase.lower().replace("’", "'"))
    salida, faltan = [], []
    for p in palabras:
        p = p.strip("'")
        if p not in dic:
            faltan.append(p)
            continue
        salida.extend(a_ipa(f) for f in dic[p])
    return " ".join(salida), faltan


def guardar(datos: dict):
    """Una entrada por línea, para que el archivo se pueda leer y editar a mano."""
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        f.write("{\n")
        for n, (seccion, lista) in enumerate(datos.items()):
            f.write(f'  "{seccion}": [\n')
            f.write(",\n".join("    " + json.dumps(e, ensure_ascii=False) for e in lista))
            f.write("\n  ]" + (",\n" if n < len(datos) - 1 else "\n"))
        f.write("}\n")


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # la consola de Windows no muestra IPA sin esto
    with open(ARCHIVO, encoding="utf-8") as f:
        datos = json.load(f)
    dic = cargar_diccionario()
    nuevas, problemas = 0, 0
    todas = "--todas" in sys.argv
    for ej in datos["pronunciacion"]:
        if ej.get("fonemas") and not todas:
            continue
        fonemas, faltan = fonemas_de(ej["frase"], dic)
        if faltan:
            problemas += 1
            print(f'  ✗ "{ej["frase"]}": no están en el diccionario {faltan}. Cambia esas palabras.')
            continue
        ej["fonemas"] = fonemas
        nuevas += 1
        print(f'  ✓ {ej["frase"]}  ->  {fonemas}')
    guardar(datos)
    print(f"\n{nuevas} frases nuevas con fonemas, {problemas} con problemas.")
    sys.exit(1 if problemas else 0)


if __name__ == "__main__":
    main()
