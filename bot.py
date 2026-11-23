"""Interfaz de Telegram de Loria: menú con botones, mensajes de texto y notas de voz.

Dos caminos:
- Botones (menú, "Otro ejercicio", "No sé"...): el bot llama la herramienta MCP directamente.
  Son acciones fijas que no necesitan que el modelo de lenguaje decida nada.
- Mensajes escritos o de voz en modo "Conversar": van al agente ReAct, que decide qué herramienta usar.
  En modo "Corregir un texto" el bot llama directamente a corregir_gramatica.

Modo niños (perfil "nino"): solo inglés, botones grandes, juegos de elegir y una mascota que crece
con el nivel (mascota.py). Solo se guarda el modo, nunca la edad.
"""
import os
import asyncio
import logging
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from telegram import Update, BotCommand
from telegram.error import NetworkError, BadRequest
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
for _nombre in ("httpx", "httpx2", "huggingface_hub", "telegram.ext.Application", "mcp", "google_genai"):
    logging.getLogger(_nombre).setLevel(logging.WARNING)

from tutor.db import (init_db, obtener_usuario, guardar_perfil, guardar_idioma, eliminar_usuario,
                obtener_ejercicio_texto, obtener_progreso)
from agente.cliente_mcp import cliente as mcp
from agente import agente
from interfaz import mascota, teclados
from modelos_lenguaje.llm import es_error_de_red, modelos_en_pausa, TodosFallaron

# Carpeta temporal de audios, junto a este archivo (cada audio se borra apenas se procesa).
CARPETA_AUDIOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos", "audios")
os.makedirs(CARPETA_AUDIOS, exist_ok=True)
init_db()

modelo_whisper = WhisperModel("base", device="cpu", compute_type="int8")

BANDERA = teclados.BANDERA
SALUDO_CONVERSACION = {
    "inglés": "Let's talk! 😊 How was your day?",
    "francés": "Parlons ! 😊 Comment s'est passée ta journée ?",
}


def transcribir(ruta, idioma=None):
    """Texto de la nota de voz e idioma detectado. idioma=None: Whisper lo detecta solo; "en": se le dice que es inglés."""
    segmentos, info = modelo_whisper.transcribe(ruta, language=idioma)
    texto = " ".join(s.text.strip() for s in segmentos)
    return texto, info.language


def mensaje_error(e: Exception) -> str:
    """Mensaje amable para el usuario según el error. Nunca se deja al usuario sin respuesta."""
    if isinstance(e, TodosFallaron):
        if any("sin conexión" in f for f in e.fallos):
            return "Se está cortando la conexión a internet 🦜 Intenta de nuevo en unos segundos."
        return ("Uy, todos mis cerebros de IA están ocupados en este momento 🦜💤 "
                "Dame un minuto y vuelve a escribirme, ¡aquí te espero!")
    if isinstance(e, TimeoutError):
        return "Estoy tardando más de lo normal en responder 🦜 Intenta de nuevo en un momento."
    if es_error_de_red(e):
        return "Se está cortando la conexión a internet 🦜 Intenta de nuevo en unos segundos."
    codigo = getattr(e, "code", None)
    if codigo in (429, 500, 502, 503, 504):
        return "Mis servidores de IA están muy ocupados en este momento 🦜 Intenta de nuevo en unos segundos."
    return None


# ---------------------------------------------------------------- ayudas
async def decir(update: Update, context: ContextTypes.DEFAULT_TYPE, texto: str, teclado=None):
    """Envía un mensaje al chat (sirve igual para mensajes y para botones)."""
    await context.bot.send_message(update.effective_chat.id, texto or "...", reply_markup=teclado)


async def herramienta(nombre: str, args: dict, user_id: int, **extra) -> dict:
    """Llama una herramienta del servidor MCP sin pasar por el modelo de lenguaje (acciones de botones)."""
    return await asyncio.to_thread(mcp.llamar, nombre, args, {"user_id": user_id, **extra})


async def sin_consentimiento(update: Update, context: ContextTypes.DEFAULT_TYPE, usuario: dict) -> bool:
    """True si el usuario aún no aceptó el tratamiento de datos (Ley 1581)."""
    if not usuario["consentimiento"]:
        await decir(update, context, "Antes de empezar necesito tu autorización. Usa /start 🦜")
        return True
    return False


def es_nino(usuario: dict) -> bool:
    return usuario.get("perfil") == "nino"


def idioma_de(usuario: dict) -> str:
    """Los niños solo practican inglés."""
    return "inglés" if es_nino(usuario) else (usuario.get("idioma") or "inglés")


def modo(context: ContextTypes.DEFAULT_TYPE) -> str:
    """"conversar" (el agente responde) o "corregir" (solo corrección). Se guarda en memoria."""
    return context.user_data.get("modo", "conversar")


def teclado_de_seguimiento(user_id: int, herramientas: list, nino: bool):
    """Botones debajo de la respuesta del agente, según cómo quedó el estudiante después del turno."""
    ej = obtener_ejercicio_texto(user_id)
    if ej:
        return teclados.durante_ejercicio_texto(ej, nino)
    if obtener_usuario(user_id)["frase_objetivo"]:
        return teclados.durante_pronunciacion(nino)
    if "revisar_respuesta" in herramientas:
        return teclados.despues_de_ejercicio("texto", nino)
    if "evaluar_pronunciacion" in herramientas:
        return teclados.despues_de_ejercicio("pron", nino)
    return teclados.despues_de_conversar(nino)


# ---------------------------------------------------------------- mascota (modo niños)
def foto_nivel(user_id: int) -> dict:
    """Nivel de inglés antes de una acción, para saber después si la mascota creció."""
    return obtener_progreso(user_id, "inglés")


async def celebrar(update, context, usuario: dict, antes: dict):
    """Si es un niño y su nivel cambió con la última acción, se lo cuenta con la mascota."""
    if not es_nino(usuario):
        return
    despues = obtener_progreso(usuario["user_id"], "inglés")
    texto = mascota.mensaje_cambio(antes["nivel_max"], despues["nivel_max"], antes["nivel"], despues["nivel"])
    if texto:
        await decir(update, context, texto)


# ---------------------------------------------------------------- formatos
async def enviar_respuesta_agente(update, context, usuario, respuesta, traza, herramientas):
    nino = es_nino(usuario)
    await decir(update, context, respuesta, teclado_de_seguimiento(usuario["user_id"], herramientas, nino))
    if context.user_data.get("traza") and traza:
        await decir(update, context, ("🧠 Traza del agente (ReAct):\n" + "\n".join(traza))[:3500])


def formatear_cambio_nivel(cambio: dict | None) -> str:
    if not cambio:
        return ""
    idioma = cambio["idioma"]
    if cambio["tipo"] == "inicial":
        return f"\n\n📍 Ya calculé tu nivel de {idioma}: {cambio['a']}."
    if cambio["tipo"] == "sube":
        return f"\n\n🎉 ¡Subiste de nivel en {idioma}: {cambio['de']} → {cambio['a']}!"
    return f"\n\n💪 Bajamos tu nivel de {idioma} a {cambio['a']} para que practiques a tu ritmo. ¡Tú puedes!"


def formatear_progreso(resumen: dict) -> str:
    """Texto del progreso para Telegram, a partir de la herramienta MCP consultar_nivel."""
    bloques = []
    for idioma, info in resumen.items():
        bandera = BANDERA.get(idioma, "")
        if info["practicas_totales"] == 0 and "pronunciacion" not in info:
            bloques.append(f"{bandera} {idioma.capitalize()}: todavía no has practicado. "
                           "¡Escríbeme una frase o haz un ejercicio!")
            continue
        nivel = info["nivel"] if info["ubicado"] else f"{info['nivel']} (calculando)"
        lineas = [
            f"{bandera} {idioma.capitalize()}: nivel {nivel}",
            f"   Frases practicadas: {info['frases_totales']}",
        ]
        if info["ejercicios_totales"]:
            n = info["ejercicios_correctos"]
            lineas.append(f"   Ejercicios: {info['ejercicios_totales']} ({n} correcto{'' if n == 1 else 's'})")
        if info["frases_recientes"]:
            lineas.append(f"   Aciertos recientes: {info['correctas_recientes']} de {info['frases_recientes']}")
        if info["errores_por_tipo"]:
            lineas.append("   Errores más comunes: " + ", ".join(
                f"{tipo} ({n})" for tipo, n in list(info["errores_por_tipo"].items())[:3]))
        if "pronunciacion" in info:
            pr = info["pronunciacion"]
            lineas.append(f"   Pronunciación: {pr['ejercicios']} ejercicios, promedio reciente {pr['promedio_reciente']}/10")
        lineas.append(f"   👉 {info['siguiente_paso']}")
        bloques.append("\n".join(lineas))
    return "📈 Tu progreso\n\n" + "\n\n".join(bloques)


def formatear_correccion(r: dict) -> str:
    """Resultado de corregir_gramatica para el modo "Corregir un texto"."""
    if r.get("idioma") == "otro":
        return "Ese texto no parece estar en inglés ni en francés 🤔 Escríbelo en uno de los dos y te lo corrijo."
    if not r["ediciones"]:
        texto = f"✅ ¡Perfecto! No encontré errores en tu {r['idioma']}.\n\n{r['corregida']}"
    else:
        lineas = [f"📝 Así queda corregido:\n\n{r['corregida']}\n"]
        for e in r["ediciones"]:
            lineas.append(f"• {e['original']} → {e['correccion']} ({e['tipo']}): {e['explicacion']}")
        texto = "\n".join(lineas)
    return texto + formatear_cambio_nivel(r.get("cambio_nivel"))


# ---------------------------------------------------------------- acciones (las usan botones y comandos)
async def mostrar_menu(update, context, usuario: dict, texto: str | None = None):
    if es_nino(usuario):
        await decir(update, context, texto or "¿A qué jugamos hoy? 🦜", teclados.menu_principal("inglés", nino=True))
        return
    idioma = idioma_de(usuario)
    await decir(update, context, f"{texto or '¿Qué quieres hacer? 🦜'}\nIdioma: {BANDERA.get(idioma, '')} {idioma}",
                teclados.menu_principal(idioma))


async def proponer_texto(update, context, usuario: dict, idioma: str | None = None):
    user_id = usuario["user_id"]
    idioma = "inglés" if es_nino(usuario) else (idioma or idioma_de(usuario))
    ej = await herramienta("generar_ejercicio_texto", {"idioma": idioma}, user_id)
    if "error" in ej:
        await decir(update, context, ej["error"] if "niños" in ej["error"] else
                    "No pude preparar el ejercicio, intenta de nuevo en un momento.", teclados.solo_menu())
        return
    await decir(update, context, agente.formatear_ejercicio("generar_ejercicio_texto", ej, usuario["perfil"]),
                teclados.durante_ejercicio_texto(ej, es_nino(usuario)))


async def proponer_pronunciacion(update, context, usuario: dict):
    ej = await herramienta("generar_ejercicio_pronunciacion", {}, usuario["user_id"])
    if "error" in ej:
        await decir(update, context, "No pude preparar el ejercicio, intenta de nuevo en un momento.",
                    teclados.solo_menu())
        return
    await decir(update, context, agente.formatear_ejercicio("generar_ejercicio_pronunciacion", ej, usuario["perfil"]),
                teclados.durante_pronunciacion(es_nino(usuario)))


async def responder_boton(update, context, usuario: dict, id_ejercicio: str, respuesta: str):
    """Botón "No sé" (respuesta vacía) o una opción de un juego de elegir. Se revisa con reglas
    fijas (sin modelo de lenguaje) y se guarda en el progreso como cualquier otra respuesta."""
    user_id, nino = usuario["user_id"], es_nino(usuario)
    activo = obtener_ejercicio_texto(user_id)
    if not activo or activo["id"] != id_ejercicio:
        await decir(update, context, "Ese ejercicio ya no está activo.", teclados.despues_de_ejercicio("texto", nino))
        return
    antes = foto_nivel(user_id)
    r = await herramienta("revisar_respuesta", {"respuesta": respuesta}, user_id)
    await herramienta("cancelar_ejercicio", {}, user_id)
    if "error" in r:
        await decir(update, context, "No pude revisar la respuesta, intenta de nuevo.", teclados.solo_menu())
        return
    esperada = r["respuesta_esperada"]
    if r["correcta"]:
        texto = (f"🎉 ¡Muy bien! «{esperada}» es correcto. ¡Ganaste una estrella! ⭐" if nino
                 else f"✅ ¡Correcto! «{esperada}».")
    elif respuesta:   # eligió una opción equivocada
        texto = f"¡Casi! 😊 La respuesta es «{esperada}». ¡La próxima la aciertas!" if nino \
            else f"❌ No es esa. La respuesta es «{esperada}»."
    else:             # "No sé"
        texto = (f"¡No pasa nada! 😊 La respuesta es:\n\n👉 {esperada}" if nino
                 else f"No pasa nada 💪 La respuesta era:\n\n👉 {esperada}")
        if r.get("otras_validas") and not nino:
            texto += f"\n\nTambién vale: {r['otras_validas'][0]}"
    if not nino:
        texto += formatear_cambio_nivel(r.get("cambio_nivel"))
    await decir(update, context, texto, teclados.despues_de_ejercicio("texto", nino))
    await celebrar(update, context, usuario, antes)


async def ver_progreso(update, context, usuario: dict):
    resumen = await herramienta("consultar_nivel", {}, usuario["user_id"])
    if "error" in resumen:
        await decir(update, context, "No pude consultar tu progreso en este momento, intenta de nuevo.",
                    teclados.solo_menu())
        return
    if es_nino(usuario):
        await decir(update, context, mascota.tarjeta(resumen["inglés"]), teclados.despues_de_progreso(nino=True))
    else:
        await decir(update, context, formatear_progreso(resumen), teclados.despues_de_progreso())


async def pedir_confirmacion_borrado(update, context):
    await decir(update, context,
                "🗑 ¿Seguro que quieres borrar tus datos? Se eliminan tu perfil, tu nivel, tu progreso y tu "
                "historial. No se puede deshacer.", teclados.confirmar_borrado())


async def borrar_todo(update, context, user_id: int):
    eliminar_usuario(user_id)
    agente.historial.pop(user_id, None)   # también la memoria de la conversación
    context.user_data.clear()
    await decir(update, context, "🗑 Tus datos y tu historial fueron eliminados. Usa /start cuando quieras volver.")


# ---------------------------------------------------------------- comandos
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy *Loria* 🦜, tu tutor para practicar inglés y francés.\n\n"
        "🔒 *Aviso de privacidad (Ley 1581):* Tus notas de voz se procesan únicamente para darte "
        "retroalimentación y se eliminan inmediatamente después. Puedes borrar tus datos en "
        "cualquier momento desde el menú.\n\n"
        "Al elegir tu perfil aceptas este tratamiento. ¿Quién va a practicar hoy?",
        parse_mode="Markdown",
        reply_markup=teclados.perfil(),
    )


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = obtener_usuario(update.effective_user.id)
    if not await sin_consentimiento(update, context, usuario):
        await mostrar_menu(update, context, usuario)


# Comandos de atajo (siguen funcionando, pero el camino normal son los botones).
async def practicar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = obtener_usuario(update.effective_user.id)
    if not await sin_consentimiento(update, context, usuario):
        await proponer_pronunciacion(update, context, usuario)


async def ejercicio_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/ejercicio usa el idioma elegido; /ejercicio francés o /ejercicio inglés lo cambia solo esta vez."""
    usuario = obtener_usuario(update.effective_user.id)
    if await sin_consentimiento(update, context, usuario):
        return
    pedido = " ".join(context.args).lower()
    idioma = "francés" if pedido.startswith("fr") else "inglés" if pedido.startswith(("in", "en")) else None
    await proponer_texto(update, context, usuario, idioma)


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await herramienta("cancelar_ejercicio", {}, update.effective_user.id)
    await decir(update, context, "Ejercicio cancelado.", teclados.solo_menu())


async def progreso_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = obtener_usuario(update.effective_user.id)
    if not await sin_consentimiento(update, context, usuario):
        await ver_progreso(update, context, usuario)


async def borrar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await pedir_confirmacion_borrado(update, context)


async def traza_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activa o desactiva mostrar la traza del agente (útil para la demo)."""
    activa = not context.user_data.get("traza", False)
    context.user_data["traza"] = activa
    await update.message.reply_text(
        "🧠 Traza del agente ACTIVADA: verás qué herramientas usa Loria en cada turno."
        if activa else "Traza del agente desactivada."
    )


# ---------------------------------------------------------------- botones
async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Atiende todos los botones. callback_data tiene la forma "grupo:acción[:dato...]"."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    partes = query.data.replace("perfil_", "perfil:").split(":")   # "perfil_nino": botones de antes de la etapa 5
    grupo, accion = partes[0], partes[1] if len(partes) > 1 else ""
    logging.info("BOTÓN | usuario %s tocó %s", user_id, query.data)

    # Se quitan los botones del mensaje tocado (su texto queda): así no quedan botones viejos activos.
    try:
        await query.edit_message_reply_markup(None)
    except BadRequest:
        pass

    if grupo == "perfil":
        nino = accion == "nino"
        guardar_perfil(user_id, "nino" if nino else "adulto")
        if nino:
            guardar_idioma(user_id, "inglés")   # el modo niños es solo en inglés
            context.user_data["modo"] = "conversar"
            bienvenida = ("🎉 ¡Hola! Soy Loria, tu loro maestro 🦜\n\n"
                          "Vamos a jugar en inglés. Tienes una mascota: un huevito 🥚\n"
                          "Cada vez que aciertas ganas una estrella ⭐, y cuando aprendes más, "
                          "¡tu mascota crece! 🐣🦜\n\nToca un botón para empezar 👇")
        else:
            bienvenida = "✅ Perfil de adulto configurado. Toca un botón para empezar."
        await mostrar_menu(update, context, obtener_usuario(user_id), bienvenida)
        return

    if grupo == "borrar" and accion == "si":
        await borrar_todo(update, context, user_id)
        return

    usuario = obtener_usuario(user_id)
    if await sin_consentimiento(update, context, usuario):
        return
    nino = es_nino(usuario)
    idioma = idioma_de(usuario)

    if grupo == "menu":
        if accion == "inicio":
            await mostrar_menu(update, context, usuario)
        elif accion == "conversar":
            context.user_data["modo"] = "conversar"
            await herramienta("cancelar_ejercicio", {}, user_id)
            if nino:
                texto = ("💬 ¡Hablemos en inglés! Escríbeme o mándame un audio 🎙\n\n"
                         "Hi! 😊 What is your favorite animal?")
            else:
                texto = (f"💬 Conversemos en {idioma}. Escríbeme o mándame una nota de voz: corrijo tus errores "
                         f"y seguimos hablando.\n\n{SALUDO_CONVERSACION.get(idioma, '')}")
            await decir(update, context, texto, teclados.solo_menu())
        elif accion == "ejercicios":
            extra = "" if idioma == "inglés" else "\n(La pronunciación por ahora solo está en inglés.)"
            await decir(update, context, f"🎯 ¿Qué tipo de ejercicio de {idioma}?{extra}",
                        teclados.menu_ejercicios(idioma))
        elif accion == "corregir" and not nino:
            context.user_data["modo"] = "corregir"
            await herramienta("cancelar_ejercicio", {}, user_id)
            await decir(update, context,
                        "📝 Escríbeme (o dime en una nota de voz) el texto en inglés o francés y te lo corrijo, "
                        "con la explicación de cada error. Para volver a conversar usa el menú.",
                        teclados.solo_menu())
        elif accion == "progreso":
            await ver_progreso(update, context, usuario)
        elif accion == "idioma" and not nino:
            await decir(update, context, "🌐 ¿Qué idioma quieres practicar?", teclados.idiomas())
        elif accion == "borrar":
            await pedir_confirmacion_borrado(update, context)
        else:
            await mostrar_menu(update, context, usuario)

    elif grupo == "idioma" and accion in BANDERA:
        if nino:
            await mostrar_menu(update, context, usuario, "Por ahora jugamos solo en inglés 🇬🇧😊")
            return
        guardar_idioma(user_id, accion)
        usuario["idioma"] = accion
        await mostrar_menu(update, context, usuario, f"✅ Listo, ahora practicamos {accion}.")

    elif grupo == "borrar":   # "no"
        await mostrar_menu(update, context, usuario, "👍 No borré nada.")

    elif grupo == "ej":
        if accion in ("texto", "otro_texto"):
            await proponer_texto(update, context, usuario)
        elif accion in ("pron", "otro_pron"):
            await proponer_pronunciacion(update, context, usuario)
        elif accion == "nose":
            await responder_boton(update, context, usuario, partes[2] if len(partes) > 2 else "", "")
        elif accion == "elige" and len(partes) > 3:
            # "ej:elige:<id del ejercicio>:<posición de la opción>"
            activo = obtener_ejercicio_texto(user_id)
            opciones = (activo or {}).get("opciones") or []
            pos = int(partes[3]) if partes[3].isdigit() else -1
            texto = opciones[pos] if 0 <= pos < len(opciones) else ""
            await responder_boton(update, context, usuario, partes[2], texto or "(opción inválida)")
        elif accion == "salir":
            await herramienta("cancelar_ejercicio", {}, user_id)
            await mostrar_menu(update, context, usuario,
                               "¡Listo! ¿A qué jugamos ahora? 🦜" if nino else "Listo, salimos del ejercicio.")


# ---------------------------------------------------------------- mensajes
async def corregir_directo(update, context, user_id: int, texto: str):
    """Modo "Corregir un texto": solo corrección, sin conversación (no hace falta el agente)."""
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    r = await herramienta("corregir_gramatica", {"texto": texto}, user_id,
                          tiempo_max=50, evitar_modelos=modelos_en_pausa())
    if "error" in r:
        await decir(update, context, "No pude corregir el texto en este momento 🦜 Intenta de nuevo en un minuto.",
                    teclados.solo_menu())
        return
    await decir(update, context, formatear_correccion(r), teclados.despues_de_corregir())


async def turno_del_agente(update, context, usuario: dict, mensaje: str, ruta=None, transcripcion=None,
                           transcripcion_ingles=None):
    """Un turno del agente ReAct, con la celebración de la mascota si el niño subió de nivel."""
    antes = foto_nivel(usuario["user_id"])
    respuesta, traza, usadas = await asyncio.to_thread(
        agente.responder, usuario["user_id"], mensaje, usuario["perfil"], ruta, transcripcion, transcripcion_ingles
    )
    await enviar_respuesta_agente(update, context, usuario, respuesta, traza, usadas)
    await celebrar(update, context, usuario, antes)


async def responder_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    usuario = obtener_usuario(user_id)
    if await sin_consentimiento(update, context, usuario):
        return
    try:
        # Si hay un ejercicio activo, la respuesta la revisa el agente aunque esté en modo "Corregir".
        if (modo(context) == "corregir" and not es_nino(usuario)
                and not usuario["ejercicio_texto"] and not usuario["frase_objetivo"]):
            await corregir_directo(update, context, user_id, update.message.text)
            return
        await context.bot.send_chat_action(update.effective_chat.id, "typing")
        await turno_del_agente(update, context, usuario, update.message.text)
    except Exception as e:
        logging.exception("Error en responder_texto")
        await decir(update, context, mensaje_error(e) or "Tuve un problema al revisar tu mensaje, intenta de nuevo.",
                    teclados.solo_menu())


async def responder_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    usuario = obtener_usuario(user_id)
    if await sin_consentimiento(update, context, usuario):
        return
    nino = es_nino(usuario)

    ruta = os.path.join(CARPETA_AUDIOS, f"{user_id}_{update.message.message_id}.ogg")  # id del mensaje se repite entre chats
    logging.info("VOZ: mensaje recibido")
    try:
        archivo = await update.message.voice.get_file()
        await archivo.download_to_drive(ruta)
        logging.info("VOZ: audio descargado")
        await context.bot.send_chat_action(update.effective_chat.id, "typing")

        transcripcion = transcripcion_ingles = None
        if usuario["frase_objetivo"]:
            # Hay un ejercicio activo: el evaluador compara el audio con los fonemas de la frase objetivo.
            # Whisper también la transcribe, para revisar que sí haya leído esa frase.
            logging.info("VOZ: hay ejercicio de pronunciación activo (%s): se evalúa contra esa frase",
                         usuario["frase_objetivo"])
            await decir(update, context, "🎧 ¡Te estoy escuchando! Dame unos segundos..." if nino
                        else "🎧 Evaluando tu pronunciación, dame unos segundos...")
            transcripcion, idioma_detectado = await asyncio.to_thread(transcribir, ruta)
            logging.info("VOZ: Whisper entendió (%s): %s", idioma_detectado, transcripcion)
            if idioma_detectado != "en":
                # Con acento fuerte Whisper suele creer que es español y escribe otra cosa. La primera
                # transcripción decide si leyó la frase (así se rechaza hablar en español); esta segunda,
                # forzada a inglés, sirve para contar cuántas palabras se le entendieron.
                transcripcion_ingles, _ = await asyncio.to_thread(transcribir, ruta, "en")
                logging.info("VOZ: forzando inglés, Whisper entendió: %s", transcripcion_ingles)
            mensaje = (
                f'[El estudiante envió una nota de voz para el ejercicio activo: '
                f'"{usuario["frase_objetivo"]}". Evalúa su pronunciación.]'
            )
        else:
            # Sin ejercicio de pronunciación: Whisper la convierte en texto y se corrige.
            logging.info("VOZ: sin ejercicio de pronunciación activo: se transcribe con Whisper y se corrige")
            texto, _idioma = await asyncio.to_thread(transcribir, ruta)
            logging.info("VOZ: transcripción lista: %s", texto)
            if not texto.strip():
                await decir(update, context, "No alcancé a escucharte, ¿puedes grabarlo otra vez?")
                return
            donde = "🎤 Reto de voz" if nino else "🎯 Ejercicios → 🎙 Pronunciación"
            await decir(update, context,
                        f"Entendí: {texto}\n\n(No tienes un ejercicio de pronunciación activo, así que reviso lo que "
                        f"dijiste. Para evaluar tu pronunciación usa {donde}.)")
            if modo(context) == "corregir" and not nino and not usuario["ejercicio_texto"]:
                await corregir_directo(update, context, user_id, texto)
                return
            mensaje = texto

        await turno_del_agente(update, context, usuario, mensaje, ruta, transcripcion, transcripcion_ingles)
    except Exception as e:
        logging.exception("Error procesando audio")
        await decir(update, context, mensaje_error(e) or "Tuve un problema procesando tu nota de voz, intenta de nuevo.",
                    teclados.solo_menu())
    finally:
        if os.path.exists(ruta):
            os.remove(ruta)  # Ley 1581: el audio no se conserva


async def manejar_error(update, context: ContextTypes.DEFAULT_TYPE):
    """Errores de red con Telegram: una línea en la terminal (el bot reintenta solo cuando vuelve el internet)."""
    err = context.error
    if isinstance(err, NetworkError):  # TimedOut es una subclase de NetworkError
        logging.warning("Problema de red con Telegram (se reintenta solo): %s", err)
        return
    logging.error("Error no controlado", exc_info=err)


async def al_iniciar(app):
    """Lista de comandos que Telegram muestra al tocar "/" (el resto se hace con botones)."""
    await app.bot.set_my_commands([
        BotCommand("start", "Empezar o cambiar de perfil"),
        BotCommand("menu", "Ver el menú"),
    ])


def main():
    logging.info("Iniciando el servidor MCP (la primera vez tarda porque carga el modelo de pronunciación)...")
    mcp.iniciar()
    app = (
        ApplicationBuilder()
        .token(os.getenv("TELEGRAM_TOKEN"))
        .concurrent_updates(True)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .post_init(al_iniciar)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CallbackQueryHandler(botones))
    # Atajos (no aparecen en la lista de comandos, pero funcionan y sirven para la demo)
    app.add_handler(CommandHandler("practicar", practicar))
    app.add_handler(CommandHandler("ejercicio", ejercicio_cmd))
    app.add_handler(CommandHandler("cancelar", cancelar))
    app.add_handler(CommandHandler("progreso", progreso_cmd))
    app.add_handler(CommandHandler("borrar", borrar_cmd))
    app.add_handler(CommandHandler("traza", traza_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_texto))
    app.add_handler(MessageHandler(filters.VOICE, responder_voz))
    app.add_error_handler(manejar_error)
    try:
        app.run_polling()
    finally:
        mcp.cerrar()


if __name__ == "__main__":
    main()
