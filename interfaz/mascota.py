"""Mascota del modo niños: crece con el nivel REAL de inglés del niño (escala MCER).

    A1 huevo -> A2 pollito -> B1 loro -> B2 loro con gafas -> C1 loro con gorra

- La mascota sigue el nivel más alto alcanzado ("nivel_max"): si el nivel baja para repasar
  cosas más fáciles, la mascota NO se encoge (sería desmotivador para un niño).
- Las estrellas son los aciertos desde la última revisión de nivel. No son puntos inventados:
  muestran cuánto falta para que Loria revise si la mascota crece (ver progreso.py).
"""
from tutor.progreso import NIVELES, FRASES_UBICACION, MIN_DESDE_CAMBIO

ETAPAS = {
    "A1": ("🥚", "Huevito"),
    "A2": ("🐣", "Pollito"),
    "B1": ("🦜", "Lorito"),
    "B2": ("🦜👓", "Loro con gafas"),
    "C1": ("🦜🧢", "Loro con gorra"),
}


def etapa(nivel: str) -> tuple:
    return ETAPAS.get(nivel, ETAPAS["A1"])


def estrellas(info: dict) -> tuple:
    """(llenas, total) según el progreso de inglés (resultado de progreso.resumen)."""
    if not info["ubicado"]:
        return min(info["desde_cambio"], FRASES_UBICACION), FRASES_UBICACION
    return min(info["correctas_desde_cambio"], MIN_DESDE_CAMBIO), MIN_DESDE_CAMBIO


def tarjeta(info: dict) -> str:
    """Pantalla "Mi mascota" a partir del progreso de inglés."""
    emoji, nombre = etapa(info["nivel_max"])
    llenas, total = estrellas(info)
    barra = "⭐" * llenas + "☆" * (total - llenas)
    lineas = [f"{emoji}  Tu mascota: {nombre}", "", barra]
    if not info["ubicado"]:
        faltan = total - llenas
        lineas.append(f"Juega {faltan} {'vez' if faltan == 1 else 'veces'} más para que tu huevito "
                      "sepa cuánto inglés sabes.")
    elif info["nivel"] < info["nivel_max"]:   # está repasando cosas más fáciles (su nivel bajó)
        lineas.append("Estamos repasando cosas más fáciles 💪 Cada acierto te da una estrella ⭐. "
                      "¡Sigue así y volverás a los retos difíciles!")
    elif info["nivel_max"] == NIVELES[-1]:
        lineas.append("¡Tu loro ya es un sabio del inglés! 🎓 Sigue jugando para no olvidar.")
    else:
        sig_emoji, sig_nombre = etapa(NIVELES[NIVELES.index(info["nivel_max"]) + 1])
        if llenas < total:
            lineas.append(f"Cada acierto te da una estrella ⭐. Con {total} estrellas, Loria mira si tu "
                          f"mascota ya puede ser {sig_nombre} {sig_emoji}.")
        else:
            lineas.append(f"¡Ya tienes todas las estrellas! Sigue acertando y tu mascota será {sig_nombre} {sig_emoji}.")
    if "pronunciacion" in info:
        lineas.append(f"\n🎤 Retos de voz: {info['pronunciacion']['ejercicios']}")
    return "\n".join(lineas)


def mensaje_cambio(nivel_max_antes: str, nivel_max_despues: str, nivel_antes: str, nivel_despues: str) -> str | None:
    """Mensaje para el niño cuando su nivel cambió en este turno (o None si no cambió nada)."""
    if nivel_max_despues > nivel_max_antes:          # creció la mascota
        e1, n1 = etapa(nivel_max_antes)
        e2, n2 = etapa(nivel_max_despues)
        return f"🎉🎉 ¡WOW! Tu {n1} {e1} se convirtió en {n2} {e2}!\n¡Estás aprendiendo muchísimo inglés! 🌟"
    if nivel_despues < nivel_antes:                   # bajó el nivel: repasar sin quitarle la mascota
        e, n = etapa(nivel_max_despues)
        return f"💪 Vamos a repasar cosas un poquito más fáciles. ¡Tu {n} {e} sigue contigo!"
    return None
