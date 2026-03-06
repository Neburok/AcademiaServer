import os
import asyncio
from pydoc import text
from turtle import title
from unicodedata import category
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from academiaserver.processing.pipeline import process_note
from academiaserver.core import save_idea
from academiaserver.scheduler.reminders_scheduler import get_due_reminders, mark_as_reminded

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

     #   print(update.effective_chat.id)
async def send_reminder(application, chat_id, message):

    await application.bot.send_message(
        chat_id=1248337517,
        text=message
    )

async def scheduler_loop(application, chat_id):

    print("Scheduler activo")

    while True:

        reminders = get_due_reminders()

        for r in reminders:

            message = f"📌 Recordatorio:\n{r['content']}"

            await application.bot.send_message(
                chat_id=chat_id,
                text=message
            )

            mark_as_reminded(r)

        await asyncio.sleep(60)


CHAT_ID=1248337517

async def post_init(application):

    application.create_task(
        scheduler_loop(application, CHAT_ID)
    )


def main():
    
    
    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()


if __name__ == "__main__":
    main()


