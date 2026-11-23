"""Características acústicas de cada fonema esperado, a partir de la salida de wav2vec2.

Lo usan IGUAL el bot (tutor/pronunciacion.py) y el entrenamiento (entrenamiento/entrenar_evaluador.py):
si se cambia algo aquí, hay que volver a entrenar la red. Solo usa numpy.

Entrada común: log_probs, una matriz [T, V] con el logaritmo de la probabilidad de cada símbolo
(V = 392 fonemas y símbolos especiales) en cada instante (T = un instante cada 20 ms).

Dos versiones:
- v1 (la original): 4 valores por fonema calculados sobre TODO el audio. Un fonema que aparece dos
  veces en la frase recibe los mismos valores las dos veces.
- v2 (Etapa 8): una ALINEACIÓN FORZADA decide en qué instantes se dijo cada fonema esperado; luego
  cada fonema se mide solo en su propio tramo y se compara con lo que el modelo reconoció.

Variantes: wav2vec2 se entrenó con muchos idiomas y escribe varios sonidos del inglés con otros
símbolos ("uː" en vez de "u", "ɐ" en vez de "ə"...). En v2 cada fonema esperado acepta sus variantes
(VARIANTES, sacadas SOLO del conjunto de entrenamiento: ver entrenamiento/entrenar_evaluador.py).
"""
import numpy as np

NOMBRES_V1 = ["max", "media", "desv", "gop_global"]
NOMBRES_V2 = ["lpp", "gop", "max_tramo", "duracion", "coincide", "cambiado", "omitido"]
_NEG = -1e30

# Fonema esperado -> otros símbolos de wav2vec2 que cuentan como el mismo sonido.
# Se llena con la lista que imprime el entrenamiento (paso "variantes").
VARIANTES = {}


# ----------------------------------------------------------------------------- preparación
def ids_aceptados(fonemas: list, vocab: dict, variantes: dict | None = None) -> list:
    """Para cada fonema esperado (IPA), los ids de los símbolos que lo representan."""
    variantes = VARIANTES if variantes is None else variantes
    salida = []
    for f in fonemas:
        simbolos = [f] + list(variantes.get(f, []))
        if f == "ɡ":
            simbolos.append("g")
        ids = sorted({vocab[s] for s in simbolos if s in vocab})
        salida.append(ids or [vocab.get("<unk>", 3)])
    return salida


def _logsumexp(x: np.ndarray, eje: int) -> np.ndarray:
    m = x.max(axis=eje, keepdims=True)
    return (m + np.log(np.exp(x - m).sum(axis=eje, keepdims=True))).squeeze(eje)


# ----------------------------------------------------------------------------- v1
def rasgos_v1(log_probs: np.ndarray, tokens: list) -> np.ndarray:
    """Las 4 características originales (sobre todo el audio). tokens: un id por fonema. [N, 4]"""
    mejor_por_instante = float(np.mean(np.max(log_probs, axis=-1)))
    filas = []
    for t in tokens:
        p = log_probs[:, t]
        filas.append([np.max(p), np.mean(p), np.std(p), np.max(p) - mejor_por_instante])
    return np.array(filas, dtype=np.float32).reshape(len(tokens), 4)


# ----------------------------------------------------------------------------- alineación
def alinear(lp_fonemas: np.ndarray, lp_blanco: np.ndarray, repetido: np.ndarray) -> list:
    """Alineación forzada CTC (algoritmo de Viterbi).

    lp_fonemas [T, N]: log-probabilidad de cada fonema esperado en cada instante.
    lp_blanco  [T]:    log-probabilidad del "blanco" (silencio o transición).
    repetido   [N]:    True si el fonema k es igual al anterior (entonces debe haber un blanco entre ellos).

    Busca el camino más probable que recorre los fonemas EN ORDEN y devuelve, para cada uno, la
    lista de instantes que le tocaron (al menos uno). Si el audio es demasiado corto para todos
    los fonemas, los reparte en partes iguales.
    """
    T, N = lp_fonemas.shape
    if N == 0:
        return []
    # Estados: blanco, fonema 1, blanco, fonema 2, ..., fonema N, blanco  (2N + 1 estados)
    S = 2 * N + 1
    lp = np.empty((T, S))
    lp[:, 0::2] = lp_blanco[:, None]
    lp[:, 1::2] = lp_fonemas
    salto = np.zeros(S, dtype=bool)                          # saltarse el blanco entre dos fonemas
    salto[3::2] = ~repetido[1:]

    puntaje = np.full(S, _NEG)
    puntaje[0], puntaje[1] = lp[0, 0], lp[0, 1]
    desde = np.zeros((T, S), dtype=np.int8)                  # 0 = se queda, 1 = avanza 1, 2 = avanza 2
    for t in range(1, T):
        avanzar1 = np.concatenate(([_NEG], puntaje[:-1]))
        avanzar2 = np.concatenate(([_NEG, _NEG], puntaje[:-2]))
        avanzar2[~salto] = _NEG
        opciones = np.stack([puntaje, avanzar1, avanzar2])
        mejor = opciones.argmax(axis=0)
        puntaje = opciones[mejor, np.arange(S)] + lp[t]
        desde[t] = mejor

    fin = S - 1 if puntaje[S - 1] >= puntaje[S - 2] else S - 2
    if puntaje[fin] < _NEG / 2:                              # no hay camino posible: reparto uniforme
        bordes = np.linspace(0, T, N + 1).astype(int)
        return [list(range(min(bordes[k], T - 1), max(bordes[k + 1], bordes[k] + 1))) for k in range(N)]

    tramos = [[] for _ in range(N)]
    s = fin
    for t in range(T - 1, -1, -1):
        if s % 2 == 1:
            tramos[s // 2].append(t)
        s -= desde[t, s]
    return [sorted(tr) for tr in tramos]


# ----------------------------------------------------------------------------- reconocimiento libre
def reconocer(log_probs: np.ndarray, blanco: int, especiales: set) -> list:
    """Lo que el modelo "oyó" sin saber la frase: el símbolo más probable en cada instante,
    sin repeticiones seguidas ni blancos (decodificación voraz de CTC)."""
    salida, anterior = [], None
    for m in log_probs.argmax(axis=-1):
        m = int(m)
        if m != anterior and m != blanco and m not in especiales:
            salida.append(m)
        anterior = m
    return salida


def comparar(aceptados: list, reconocidos: list) -> list:
    """Para cada fonema esperado: "ok", "cambiado" (se oyó otro en su lugar) u "omitido" (no se oyó).

    Distancia de edición (Levenshtein): un fonema reconocido "coincide" con el esperado si es uno
    de sus símbolos aceptados; cambiar, omitir o agregar un fonema cuesta 1.
    """
    N, M = len(aceptados), len(reconocidos)
    d = np.zeros((N + 1, M + 1), dtype=int)
    d[:, 0] = np.arange(N + 1)
    d[0, :] = np.arange(M + 1)
    for i in range(1, N + 1):
        for j in range(1, M + 1):
            igual = reconocidos[j - 1] in aceptados[i - 1]
            d[i, j] = min(d[i - 1, j - 1] + (0 if igual else 1), d[i - 1, j] + 1, d[i, j - 1] + 1)
    estado, i, j = ["ok"] * N, N, M
    while i > 0:                                              # se recorre el camino hacia atrás
        igual = j > 0 and reconocidos[j - 1] in aceptados[i - 1]
        if j > 0 and d[i, j] == d[i - 1, j - 1] + (0 if igual else 1):
            estado[i - 1] = "ok" if igual else "cambiado"
            i, j = i - 1, j - 1
        elif d[i, j] == d[i - 1, j] + 1:
            estado[i - 1] = "omitido"
            i -= 1
        else:
            j -= 1
    return estado


# ----------------------------------------------------------------------------- v2
def analizar(log_probs: np.ndarray, aceptados: list, blanco: int, especiales: set) -> dict:
    """Características v2 y, para mostrarle al estudiante, qué sonido se oyó en cada fonema.

    aceptados: para cada fonema esperado, la lista de ids que lo representan (ids_aceptados).
    Por cada fonema esperado, en SU tramo de la alineación:
      lpp        promedio del log de la probabilidad del fonema esperado (sumando sus variantes)
      gop        "Goodness of Pronunciation": lpp menos el log del mejor fonema competidor
                 (0 si el esperado era el más probable; muy negativo si sonaba a otro)
      max_tramo  la probabilidad más alta que alcanzó el fonema esperado en su tramo
      duracion   log del número de instantes del tramo
      coincide   1 si el fonema que más sonó en el tramo es uno de los aceptados
      cambiado / omitido   comparación con el reconocimiento libre (ver comparar)
    """
    T, N = log_probs.shape[0], len(aceptados)
    lp_fon = np.stack([_logsumexp(log_probs[:, ids], 1) for ids in aceptados], axis=1) if N else np.zeros((T, 0))
    repetido = np.array([k > 0 and aceptados[k] == aceptados[k - 1] for k in range(N)], dtype=bool)
    tramos = alinear(lp_fon, log_probs[:, blanco], repetido)

    solo_fonemas = np.ones(log_probs.shape[1], dtype=bool)
    solo_fonemas[list(especiales | {blanco})] = False         # competidores: solo fonemas reales
    estado = comparar(aceptados, reconocer(log_probs, blanco, especiales))

    filas, oidos = [], []
    for k, (ids, tramo) in enumerate(zip(aceptados, tramos)):
        seg = lp_fon[tramo, k]
        otros = solo_fonemas.copy()
        otros[ids] = False
        mejor_otro = log_probs[tramo][:, otros].max(axis=1)
        masa = np.where(solo_fonemas, np.exp(log_probs[tramo]), 0).sum(axis=0)
        oido = int(masa.argmax())                              # el fonema que más sonó en el tramo
        filas.append([seg.mean(), np.minimum(seg - mejor_otro, 0).mean(), seg.max(),
                      np.log(len(tramo)), float(oido in ids),
                      float(estado[k] == "cambiado"), float(estado[k] == "omitido")])
        oidos.append(oido)
    return {"rasgos": np.array(filas, dtype=np.float32).reshape(N, len(NOMBRES_V2)),
            "oidos": oidos, "estado": estado, "tramos": tramos}


def rasgos(version: str, log_probs: np.ndarray, fonemas: list, vocab: dict,
           variantes: dict | None = None) -> np.ndarray:
    """Matriz [N, k] de características según la versión del modelo: "v1", "v2" o "v1+v2"."""
    blanco, especiales = especiales_de(vocab)
    partes = []
    if "v1" in version:
        partes.append(rasgos_v1(log_probs, [ids[0] for ids in ids_aceptados(fonemas, vocab, {})]))
    if "v2" in version:
        partes.append(analizar(log_probs, ids_aceptados(fonemas, vocab, variantes), blanco, especiales)["rasgos"])
    return np.concatenate(partes, axis=1)


def especiales_de(vocab: dict) -> tuple:
    """(id del blanco, ids de los símbolos que no son fonemas)."""
    return vocab["<pad>"], {vocab[t] for t in ("<s>", "</s>", "<unk>") if t in vocab}
