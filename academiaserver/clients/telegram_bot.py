import os
from pydoc import text
from turtle import title
from unicodedata import category
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from academiaserver.processing.pipeline import process_note
from academiaserver.core import save_idea


load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = os.getenv("API_URL")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Jarvis Académico conectado.\nEnvíame una idea y la guardaré.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    try:

        # pipeline
        note = process_note(text, source="telegram")

        # guardar
        saved = save_idea(note)

        await update.message.reply_text(
            f"✅ Nota guardada con ID: {saved['id']}"
        )

    except Exception as e:

        await update.message.reply_text(
            "❌ Error al guardar la nota"
        )

        print("Error:", e)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot corriendo...")
    app.run_polling()


if __name__ == "__main__":
    main()