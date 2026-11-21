"""Nivel y progreso del estudiante, por idioma, en la escala del MCER (A1 a C1).

Reglas (pensadas para que un solo mensaje nunca cambie el nivel):

1. Ubicación inicial: con las primeras 5 frases de un idioma se calcula el nivel de partida,
   según el nivel de las frases que escribió bien.
2. Después, el nivel se revisa con las últimas 10 frases, y solo si hay al menos 8 frases
   desde el último cambio:
     - SUBE si al menos el 80 % son correctas Y al menos la mitad son frases correctas de su nivel
       o más (escribir bien "I like dogs" no demuestra un B2).
     - BAJA si el 40 % o menos son correctas.
     - Si no, se mantiene.
3. Una frase es "correcta" si no tiene errores importantes (gramática o vocabulario). Los errores
   leves (ortografía, puntuación) se cuentan en las estadísticas pero no la vuelven incorrecta.
4. Los ejercicios de texto (completar y traducir) cuentan igual que las frases, con el nivel del
   ejercicio: así resolver bien ejercicios de su nivel también lo hace subir.
5. La pronunciación (solo inglés) se guarda en el progreso, pero no mueve el nivel MCER: el
   evaluador mide sonidos, no dominio del idioma.
"""
from collections import Counter

from tutor import db

NIVELES = ["A1", "A2", "B1", "B2", "C1"]
IDIOMAS = ["inglés", "francés"]

FRASES_UBICACION = 5   # frases para calcular el nivel inicial
VENTANA = 10           # frases recientes que se miran
MIN_DESDE_CAMBIO = 8   # frases necesarias desde el último cambio antes de volver a cambiar
UMBRAL_SUBE = 0.8
UMBRAL_BAJA = 0.4
MIN_DE_SU_NIVEL = 0.5

ERRORES_IMPORTANTES = {"gramática", "vocabulario"}
ERRORES_LEVES = {"ortografía", "puntuación"}
CUENTAN_PARA_NIVEL = ("frase", "ejercicio")   # la pronunciación no


def _i(nivel: str) -> int:
    return NIVELES.index(nivel) if nivel in NIVELES else 0


# ---------------------------------------------------------------- decisión (función pura, se puede probar sola)
def decidir(nivel: str, ubicado: bool, frases: list) -> tuple:
    """Decide el nivel a partir de las frases desde el último cambio (de la más vieja a la más nueva).

    Cada frase es un dict con "correcto" (0/1) y "nivel_frase". Devuelve (nivel, ubicado, motivo);
    motivo es None si no hubo cambio.
    """
    if not ubicado:
        if len(frases) < FRASES_UBICACION:
            return nivel, False, None
        correctas = [f for f in frases if f["correcto"]]
        if not correctas:
            nuevo = "A1"
        else:
            niveles = sorted(_i(f["nivel_frase"]) for f in correctas)
            nuevo_i = niveles[len(niveles) // 2]                      # la mediana
            if len(correctas) / len(frases) < 0.6:
                nuevo_i = max(0, nuevo_i - 1)                         # muchos errores: un nivel menos
            nuevo = NIVELES[nuevo_i]
        return nuevo, True, f"nivel inicial calculado con tus primeras {len(frases)} frases y ejercicios"

    if len(frases) < MIN_DESDE_CAMBIO:
        return nivel, True, None

    recientes = frases[-VENTANA:]
    pct = sum(f["correcto"] for f in recientes) / len(recientes)
    # Solo cuentan como evidencia las frases CORRECTAS de su nivel o más (una frase difícil mal escrita no demuestra nada).
    de_su_nivel = sum(f["correcto"] and _i(f["nivel_frase"]) >= _i(nivel) for f in recientes) / len(recientes)

    if pct >= UMBRAL_SUBE and de_su_nivel >= MIN_DE_SU_NIVEL and _i(nivel) < len(NIVELES) - 1:
        return NIVELES[_i(nivel) + 1], True, f"{pct:.0%} de frases correctas y usando frases de tu nivel"
    if pct <= UMBRAL_BAJA and _i(nivel) > 0:
        return NIVELES[_i(nivel) - 1], True, f"solo {pct:.0%} de frases correctas últimamente"
    return nivel, True, None


# ---------------------------------------------------------------- registro
def registrar_frase(user_id: int, correccion: dict) -> dict | None:
    """Guarda una frase corregida y revisa el nivel. Devuelve el cambio de nivel, si lo hubo."""
    idioma = correccion.get("idioma")
    if idioma not in IDIOMAS:
        return None  # texto en español u otro idioma: no cuenta como práctica
    tipos = [e.get("tipo", "gramática") for e in correccion.get("ediciones", [])]
    return _registrar(user_id, idioma, "frase", tipos, correccion.get("nivel_frase", "A1"))


def registrar_ejercicio(user_id: int, idioma: str, nivel: str, correcto: bool, tipos: list) -> dict | None:
    """Guarda la respuesta a un ejercicio de texto (con el nivel del ejercicio) y revisa el nivel."""
    if correcto:
        tipos = [t for t in tipos if t in ERRORES_LEVES]           # correcto: solo pueden quedar errores leves
    elif not any(t in ERRORES_IMPORTANTES for t in tipos):
        tipos = tipos + ["gramática"]                              # incorrecto: al menos un error importante
    return _registrar(user_id, idioma, "ejercicio", tipos, nivel)


def _registrar(user_id: int, idioma: str, tipo: str, tipos: list, nivel_frase: str) -> dict | None:
    importantes = sum(t in ERRORES_IMPORTANTES for t in tipos)
    db.registrar_intento(
        user_id, idioma, tipo,
        correcto=int(importantes == 0),
        errores_importantes=importantes,
        errores_leves=len(tipos) - importantes,
        tipos_error=",".join(tipos),
        nivel_frase=nivel_frase,
    )

    p = db.obtener_progreso(user_id, idioma)
    frases = db.intentos(user_id, idioma, CUENTAN_PARA_NIVEL, desde_id=p["ultimo_cambio_id"])
    nuevo, ubicado, motivo = decidir(p["nivel"], bool(p["ubicado"]), frases)
    if motivo is None:
        return None

    db.guardar_progreso(user_id, idioma, nuevo, ubicado, ultimo_cambio_id=frases[-1]["id"])
    direccion = "inicial" if not p["ubicado"] else ("sube" if _i(nuevo) > _i(p["nivel"]) else "baja")
    return {"idioma": idioma, "de": p["nivel"], "a": nuevo, "tipo": direccion, "motivo": motivo}


def registrar_pronunciacion(user_id: int, puntaje: float):
    db.registrar_intento(user_id, "inglés", "pronunciacion", correcto=int(puntaje >= 7), puntaje=puntaje)


def cambiar_nivel(user_id: int, idioma: str, nivel: str) -> dict:
    """Cambio manual (solo si el estudiante lo pide). Reinicia la cuenta de frases desde aquí."""
    if idioma not in IDIOMAS or nivel not in NIVELES:
        return {"error": f"Idioma o nivel inválido. Idiomas: {IDIOMAS}. Niveles: {NIVELES}."}
    ultimo = db.intentos(user_id, idioma, CUENTAN_PARA_NIVEL)
    db.guardar_progreso(user_id, idioma, nivel, True, ultimo_cambio_id=ultimo[-1]["id"] if ultimo else 0)
    return {"idioma": idioma, "nivel": nivel}


# ---------------------------------------------------------------- consulta
def niveles(user_id: int) -> dict:
    """{"inglés": "B1 (calculando, 2/5 frases)", ...} para las instrucciones del modelo."""
    salida = {}
    for idioma in IDIOMAS:
        p = db.obtener_progreso(user_id, idioma)
        if p["ubicado"]:
            salida[idioma] = p["nivel"]
        else:
            n = len(db.intentos(user_id, idioma, CUENTAN_PARA_NIVEL))
            salida[idioma] = f"{p['nivel']} (todavía calculando su nivel, {n}/{FRASES_UBICACION} frases)"
    return salida


def resumen(user_id: int) -> dict:
    """Todo lo que el estudiante necesita ver de su progreso, por idioma."""
    salida = {}
    for idioma in IDIOMAS:
        p = db.obtener_progreso(user_id, idioma)
        todas = db.intentos(user_id, idioma, CUENTAN_PARA_NIVEL)   # frases y ejercicios de texto
        desde = [f for f in todas if f["id"] > p["ultimo_cambio_id"]]
        recientes = todas[-VENTANA:]
        tipos = Counter(t for f in todas for t in f["tipos_error"].split(",") if t)
        ejercicios = [f for f in todas if f["tipo"] == "ejercicio"]
        info = {
            "nivel": p["nivel"],
            "nivel_max": p.get("nivel_max") or p["nivel"],
            "ubicado": bool(p["ubicado"]),
            "desde_cambio": len(desde),                                  # para las estrellas del modo niños
            "correctas_desde_cambio": sum(f["correcto"] for f in desde),
            "practicas_totales": len(todas),
            "frases_totales": len(todas) - len(ejercicios),
            "ejercicios_totales": len(ejercicios),
            "ejercicios_correctos": sum(f["correcto"] for f in ejercicios),
            "correctas_recientes": sum(f["correcto"] for f in recientes),
            "frases_recientes": len(recientes),
            "errores_por_tipo": dict(tipos.most_common()),
        }
        if not p["ubicado"]:
            faltan = FRASES_UBICACION - len(todas)
            info["siguiente_paso"] = (f"Escribe {faltan} frase{'s' if faltan > 1 else ''} más (o resuelve ejercicios) "
                                      "para calcular tu nivel.")
        elif p["nivel"] == NIVELES[-1]:
            info["siguiente_paso"] = "Estás en el nivel más alto. ¡Sigue practicando para mantenerlo!"
        else:
            faltan = max(0, MIN_DESDE_CAMBIO - len(desde))
            info["siguiente_paso"] = (
                f"Para subir a {NIVELES[_i(p['nivel']) + 1]}: al menos {UMBRAL_SUBE:.0%} de aciertos en "
                f"tus últimas {VENTANA} frases y ejercicios, usando frases de tu nivel"
                + (f" (falta{'n' if faltan > 1 else ''} {faltan} frase{'s' if faltan > 1 else ''} "
                   f"para la próxima revisión)." if faltan else ".")
            )
        if idioma == "inglés":
            pron = db.intentos(user_id, idioma, "pronunciacion")
            if pron:
                ult = pron[-VENTANA:]
                info["pronunciacion"] = {
                    "ejercicios": len(pron),
                    "promedio_reciente": round(sum(x["puntaje"] for x in ult) / len(ult), 1),
                }
        salida[idioma] = info
    return salida
