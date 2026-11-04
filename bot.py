import os
import asyncio
import logging
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)
from llm import corregir

load_dotenv()
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

os.makedirs("audios", exist_ok=True)

modelo = WhisperModel("base", device="cpu", compute_type="int8")

def transcribir(ruta):
    segmentos, info = modelo.transcribe(ruta)
    texto = " ".join(s.text.strip() for s in segmentos)
    return texto, info.language

def formatear(r):
    if not r["ediciones"]:
        return f"({r['idioma']}) No encontré errores, ¡bien hecho!"
    lineas = [f"({r['idioma']}) Corregida\n{r['corregida']}\n"]
    for e in r["ediciones"]:
        lineas.append(f"• {e['original']} → {e['correccion']}\n  {e['explicacion']}")
    return "\n".join(lineas)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy Parley, tu compañero para practicar inglés y francés.\n\n"
        "Escríbeme o mándame una nota de voz y te ayudo a mejorar."
    )

async def responder_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = await asyncio.to_thread(corregir, update.message.text)
        await update.message.reply_text(formatear(r))
    except Exception:
        logging.exception("Error al corregir")
        await update.message.reply_text("Tuve un problema al revisar tu mensaje, intenta de nuevo.")

async def responder_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voz = update.message.voice
    archivo = await voz.get_file()
    ruta = f"audios/{update.message.message_id}.ogg"
    await archivo.download_to_drive(ruta)
    try:
        texto, idioma = await asyncio.to_thread(transcribir, ruta)
    finally:
        os.remove(ruta)
    await update.message.reply_text(f"Entendí\n{texto}")
    try:
        r = await asyncio.to_thread(corregir, texto)
        await update.message.reply_text(formatear(r))
    except Exception:
        logging.exception("Error al corregir")
        await update.message.reply_text("No pude revisar la gramática esta vez.")

app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_texto))
app.add_handler(MessageHandler(filters.VOICE, responder_voz))
app.run_polling()