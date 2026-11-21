"""Botones de Telegram (teclados en línea) de Loria. Este archivo solo arma los botones;
lo que hace cada uno está en bot.py (función botones).

Cada botón lleva un "callback_data" corto que Telegram le devuelve al bot cuando se toca,
con la forma "grupo:acción", por ejemplo "menu:progreso" o "ej:otro_texto".

Modo niños (nino=True): un botón por fila, así ocupan todo el ancho y son más fáciles de tocar.
"""
import random

from telegram import InlineKeyboardButton as Boton, InlineKeyboardMarkup as Teclado

BANDERA = {"inglés": "🇬🇧", "francés": "🇫🇷"}


def _armar(botones: list, nino: bool, por_fila: int = 2) -> Teclado:
    """Adultos: de a 2 por fila. Niños: uno por fila (botones grandes)."""
    n = 1 if nino else por_fila
    return Teclado([botones[i:i + n] for i in range(0, len(botones), n)])


def perfil() -> Teclado:
    return Teclado([[Boton("🧒 Soy Niño / Niña", callback_data="perfil:nino"),
                     Boton("🧑 Soy Adulto", callback_data="perfil:adulto")]])


def menu_principal(idioma: str, nino: bool = False) -> Teclado:
    if nino:  # solo inglés, sin "Corregir un texto" ni "Cambiar idioma"
        return _armar([
            Boton("💬 Hablar con Loria", callback_data="menu:conversar"),
            Boton("🎮 Juego de palabras", callback_data="ej:texto"),
            Boton("🎤 Reto de voz", callback_data="ej:pron"),
            Boton("🥚 Mi mascota", callback_data="menu:progreso"),
            Boton("🗑 Borrar mis datos", callback_data="menu:borrar"),
        ], nino=True)
    return Teclado([
        [Boton("💬 Conversar", callback_data="menu:conversar"),
         Boton("🎯 Ejercicios", callback_data="menu:ejercicios")],
        [Boton("📝 Corregir un texto", callback_data="menu:corregir"),
         Boton("📈 Mi progreso", callback_data="menu:progreso")],
        [Boton(f"🌐 Cambiar idioma ({BANDERA.get(idioma, '')})", callback_data="menu:idioma"),
         Boton("🗑 Borrar mis datos", callback_data="menu:borrar")],
    ])


def _menu() -> Boton:
    return Boton("🏠 Menú", callback_data="menu:inicio")


def menu_ejercicios(idioma: str) -> Teclado:
    filas = [[Boton("✏️ Escribir (completar o traducir)", callback_data="ej:texto")]]
    if idioma == "inglés":
        filas.append([Boton("🎙 Pronunciación (nota de voz)", callback_data="ej:pron")])
    filas.append([_menu()])
    return Teclado(filas)


def idiomas() -> Teclado:
    return Teclado([[Boton("🇬🇧 Inglés", callback_data="idioma:inglés"),
                     Boton("🇫🇷 Francés", callback_data="idioma:francés")],
                    [_menu()]])


def confirmar_borrado() -> Teclado:
    return Teclado([[Boton("✅ Sí, borrar todo", callback_data="borrar:si"),
                     Boton("↩️ No, cancelar", callback_data="borrar:no")]])


# ---------------------------------------------------------------- seguimiento (debajo de cada respuesta)
def opciones(ej: dict) -> list:
    """Botones de respuesta de un ejercicio "elegir", en desorden. El callback lleva la posición
    de la opción en el banco (así el botón funciona aunque el orden mostrado cambie)."""
    botones = [Boton(op, callback_data=f"ej:elige:{ej['id']}:{i}") for i, op in enumerate(ej["opciones"])]
    random.shuffle(botones)
    return botones


def durante_ejercicio_texto(ej: dict, nino: bool = False) -> Teclado:
    # El id evita que "No sé" de un ejercicio viejo muestre la respuesta del ejercicio actual.
    otros = [Boton("🤔 No sé, ver respuesta" if nino else "💡 No sé, ver respuesta",
                   callback_data=f"ej:nose:{ej['id']}"),
             Boton("⏭ Otro", callback_data="ej:otro_texto"),
             Boton("❌ Salir del juego" if nino else "❌ Salir del ejercicio", callback_data="ej:salir")]
    if ej.get("opciones"):
        return Teclado([[b] for b in opciones(ej)] + [[b] for b in otros[1:]])
    return _armar(otros, nino)


def durante_pronunciacion(nino: bool = False) -> Teclado:
    return _armar([Boton("⏭ Otra frase", callback_data="ej:otro_pron"),
                   Boton("❌ Salir del juego" if nino else "❌ Salir del ejercicio", callback_data="ej:salir")], nino)


def despues_de_ejercicio(tipo: str, nino: bool = False) -> Teclado:
    """tipo: "texto" o "pron"."""
    if nino:
        otro = "🎮 ¡Otro juego!" if tipo == "texto" else "🎤 ¡Otro reto de voz!"
        return _armar([Boton(otro, callback_data=f"ej:otro_{tipo}"),
                       Boton("🥚 Mi mascota", callback_data="menu:progreso"), _menu()], nino=True)
    otro = "➡️ Otro ejercicio" if tipo == "texto" else "➡️ Otra frase"
    return Teclado([[Boton(otro, callback_data=f"ej:otro_{tipo}"),
                     Boton("📈 Mi progreso", callback_data="menu:progreso")],
                    [_menu()]])


def despues_de_conversar(nino: bool = False) -> Teclado:
    if nino:
        return _armar([Boton("🎮 Juego de palabras", callback_data="ej:texto"), _menu()], nino=True)
    return Teclado([[Boton("🎯 Hacer un ejercicio", callback_data="menu:ejercicios"), _menu()]])


def despues_de_corregir() -> Teclado:
    return Teclado([[Boton("💬 Conversar", callback_data="menu:conversar"),
                     Boton("🎯 Ejercicios", callback_data="menu:ejercicios")],
                    [_menu()]])


def despues_de_progreso(nino: bool = False) -> Teclado:
    if nino:
        return _armar([Boton("🎮 Juego de palabras", callback_data="ej:texto"),
                       Boton("🎤 Reto de voz", callback_data="ej:pron"), _menu()], nino=True)
    return despues_de_corregir()


def solo_menu() -> Teclado:
    return Teclado([[_menu()]])
