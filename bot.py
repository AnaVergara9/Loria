import os
import random
import asyncio
import logging
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import NetworkError
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
for _nombre in ("httpx", "httpx2", "huggingface_hub", "telegram.ext.Application"):
    logging.getLogger(_nombre).setLevel(logging.WARNING)

from db import init_db, obtener_usuario, guardar_perfil, guardar_ejercicio, eliminar_usuario
from pronunciacion import EJERCICIOS_PRONUNCIACION
import agente
from llm import es_error_de_red

os.makedirs("audios", exist_ok=True)
init_db()

modelo_whisper = WhisperModel("base", device="cpu", compute_type="int8")


def transcribir(ruta):
    segmentos, info = modelo_whisper.transcribe(ruta)
    texto = " ".join(s.text.strip() for s in segmentos)
    return texto, info.language


def mensaje_error(e: Exception) -> str:
    if isinstance(e, TimeoutError):
        return "Estoy tardando más de lo normal en responder 🦜 Intenta de nuevo en un momento."
    if es_error_de_red(e):
        return "Se está cortando la conexión a internet 🦜 Intenta de nuevo en unos segundos."
    codigo = getattr(e, "code", None)
    if codigo in (429, 500, 502, 503, 504):
        return "Mis servidores de IA están muy ocupados en este momento 🦜 Intenta de nuevo en unos segundos."
    return None


async def sin_consentimiento(update: Update, usuario: dict) -> bool:
    """True si el usuario aún no aceptó el tratamiento de datos (Ley 1581)."""
    if not usuario["consentimiento"]:
        await update.message.reply_text("Antes de empezar necesito tu autorización. Usa /start 🦜")
        return True
    return False


async def enviar(update: Update, context: ContextTypes.DEFAULT_TYPE, respuesta: str, traza: list):
    await update.message.reply_text(respuesta or "...")
    if context.user_data.get("traza") and traza:
        await update.message.reply_text(("🧠 Traza del agente (ReAct):\n" + "\n".join(traza))[:3500])


# ---------------------------------------------------------------- comandos
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧒 Soy Niño / Niña", callback_data="perfil_nino"),
            InlineKeyboardButton("🧑 Soy Adulto", callback_data="perfil_adulto"),
        ]
    ])
    await update.message.reply_text(
        "¡Hola! Soy *Loria* 🦜, tu tutor para practicar inglés y francés.\n\n"
        "🔒 *Aviso de privacidad (Ley 1581):* Tus notas de voz se procesan únicamente para darte "
        "retroalimentación y se eliminan inmediatamente después. Puedes borrar tu historial en "
        "cualquier momento con /borrar.\n\n"
        "Al elegir tu perfil aceptas este tratamiento. ¿Quién va a practicar hoy?",
        parse_mode="Markdown",
        reply_markup=teclado,
    )


async def seleccionar_perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    perfil = "nino" if query.data == "perfil_nino" else "adulto"
    guardar_perfil(query.from_user.id, perfil)

    if perfil == "nino":
        texto = (
            "🎉 ¡Genial! Soy Loria, tu loro maestro 🦜\n\n"
            "• Escríbeme o mándame audios en inglés o francés y charlamos.\n"
            "• Usa /practicar para ganar puntos de pronunciación.\n"
            "• Usa /borrar si quieres eliminar tus datos."
        )
    else:
        texto = (
            "✅ Perfil de adulto configurado.\n\n"
            "• Escríbeme o envíame notas de voz en inglés o francés para conversar y corregir gramática.\n"
            "• Usa /practicar para un ejercicio guiado de pronunciación (inglés).\n"
            "• Usa /borrar si deseas eliminar tus datos."
        )
    await query.edit_message_text(texto)


async def practicar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    usuario = obtener_usuario(user_id)
    if await sin_consentimiento(update, usuario):
        return
    ejercicio = agente.siguiente_ejercicio(user_id)
    guardar_ejercicio(user_id, ejercicio["frase"], ejercicio["fonemas"])

    intro = (
        "🎯 *¡Reto de pronunciación!* Lee en voz alta y envíame una nota de voz diciendo:"
        if usuario["perfil"] == "nino"
        else "🎙 *Ejercicio de pronunciación.* Envía una nota de voz leyendo esta frase:"
    )
    await update.message.reply_text(
        f"{intro}\n\n👉 *{ejercicio['frase']}*\n\n_(Usa /cancelar si prefieres volver a conversación libre)_",
        parse_mode="Markdown",
    )


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    guardar_ejercicio(update.effective_user.id, None, None)
    await update.message.reply_text("Ejercicio cancelado. Puedes seguir escribiendo o enviando audios libremente.")


async def borrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    eliminar_usuario(update.effective_user.id)
    agente.historial.pop(update.effective_user.id, None)
    await update.message.reply_text(
        "🗑 Tus datos y tu historial fueron eliminados. Usa /start cuando quieras volver."
    )


async def traza_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activa o desactiva mostrar la traza del agente (útil para la demo)."""
    activa = not context.user_data.get("traza", False)
    context.user_data["traza"] = activa
    await update.message.reply_text(
        "🧠 Traza del agente ACTIVADA: verás qué herramientas usa Loria en cada turno."
        if activa else "Traza del agente desactivada."
    )


# ---------------------------------------------------------------- mensajes
async def responder_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    usuario = obtener_usuario(user_id)
    if await sin_consentimiento(update, usuario):
        return
    try:
        await context.bot.send_chat_action(update.effective_chat.id, "typing")
        respuesta, traza = await asyncio.to_thread(
            agente.responder, user_id, update.message.text, usuario["perfil"]
        )
        await enviar(update, context, respuesta, traza)
    except Exception as e:
        logging.exception("Error en responder_texto")
        await update.message.reply_text(mensaje_error(e) or "Tuve un problema al revisar tu mensaje, intenta de nuevo.")


async def responder_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    usuario = obtener_usuario(user_id)
    if await sin_consentimiento(update, usuario):
        return

    ruta = f"audios/{update.message.message_id}.ogg"
    logging.info("VOZ: mensaje recibido")
    try:
        archivo = await update.message.voice.get_file()
        await archivo.download_to_drive(ruta)
        logging.info("VOZ: audio descargado")
        await context.bot.send_chat_action(update.effective_chat.id, "typing")

        if usuario["frase_objetivo"]:
            # Hay un ejercicio activo: no hace falta transcribir, el agente evalúa la pronunciación.
            await update.message.reply_text("🎧 Evaluando tu pronunciación, dame unos segundos...")
            mensaje = (
                f'[El estudiante envió una nota de voz para el ejercicio activo: '
                f'"{usuario["frase_objetivo"]}". Evalúa su pronunciación.]'
            )
        else:
            # Conversación libre: Ruta 1 (Whisper) -> el agente corrige y conversa.
            logging.info("VOZ: transcribiendo con Whisper...")
            texto, _idioma = await asyncio.to_thread(transcribir, ruta)
            logging.info("VOZ: transcripción lista: %s", texto)
            if not texto.strip():
                await update.message.reply_text("No alcancé a escucharte, ¿puedes grabarlo otra vez?")
                return
            await update.message.reply_text(f"Entendí: {texto}")
            mensaje = texto

        respuesta, traza = await asyncio.to_thread(
            agente.responder, user_id, mensaje, usuario["perfil"], ruta
        )
        await enviar(update, context, respuesta, traza)
    except Exception as e:
        logging.exception("Error procesando audio")
        await update.message.reply_text(mensaje_error(e) or "Tuve un problema procesando tu nota de voz, intenta de nuevo.")
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


def main():
    app = (
        ApplicationBuilder()
        .token(os.getenv("TELEGRAM_TOKEN"))
        .concurrent_updates(True)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(seleccionar_perfil, pattern="^perfil_"))
    app.add_handler(CommandHandler("practicar", practicar))
    app.add_handler(CommandHandler("cancelar", cancelar))
    app.add_handler(CommandHandler("borrar", borrar))
    app.add_handler(CommandHandler("traza", traza_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_texto))
    app.add_handler(MessageHandler(filters.VOICE, responder_voz))
    app.add_error_handler(manejar_error)
    app.run_polling()


if __name__ == "__main__":
    main()
