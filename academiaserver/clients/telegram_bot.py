import os
from pydoc import text
from turtle import title
from unicodedata import category
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = os.getenv("API_URL")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Jarvis Académico conectado.\nEnvíame una idea y la guardaré.")

def classify_message(text: str) -> str:
    text_lower = text.lower()

    if any(word in text_lower for word in ["acuérdame", "recuerdame", "recordar", "recuérdame"]):
        return "recordatorio"

    if any(word in text_lower for word in ["idea", "propuesta", "proyecto"]):
        return "idea"

    if any(word in text_lower for word in ["definición", "concepto", "explicación", "teoría"]):
        return "apunte"

    return "nota"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    category = classify_message(text)
    title = generate_title(text)
    data = {
        "title": title,
        "content": text,
        "tags": [category]
    }

    response = requests.post(f"{API_URL}/save", json=data)

    if response.status_code == 200:
        idea = response.json()
        await update.message.reply_text(f"✅ Idea guardada con ID: {idea['id']}")
    else:
        await update.message.reply_text("❌ Error al guardar la idea.")

def generate_title(text: str) -> str:
    words = text.split()
    return " ".join(words[:8])  # primeras 8 palabras

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot corriendo...")
    app.run_polling()


if __name__ == "__main__":
    main()