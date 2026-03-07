import os
import shutil
import tempfile
import unittest

from academiaserver.clients import telegram_bot


class FakeBot:
    def __init__(self, fail_times=0):
        self.fail_times = fail_times
        self.calls = 0

    async def send_message(self, chat_id, text):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("Fallo simulado")


class FakeApp:
    def __init__(self, bot):
        self.bot = bot


class TelegramBotTests(unittest.IsolatedAsyncioTestCase):
    async def test_send_reminder_with_retry_recupera_en_reintento(self):
        fake_bot = FakeBot(fail_times=1)
        app = FakeApp(fake_bot)

        sent = await telegram_bot.send_reminder_with_retry(
            app,
            chat_id=123,
            message="mensaje",
            reminder_id="rem-1",
        )

        self.assertTrue(sent)
        self.assertEqual(fake_bot.calls, 2)

    async def test_send_reminder_with_retry_agota_intentos(self):
        fake_bot = FakeBot(fail_times=10)
        app = FakeApp(fake_bot)

        sent = await telegram_bot.send_reminder_with_retry(
            app,
            chat_id=123,
            message="mensaje",
            reminder_id="rem-2",
        )

        self.assertFalse(sent)
        self.assertEqual(fake_bot.calls, telegram_bot.REMINDER_MAX_RETRIES)

    def test_validate_config_valida_rutas(self):
        temp_inbox = tempfile.mkdtemp(prefix="inbox_")
        temp_logs = tempfile.mkdtemp(prefix="logs_")

        original_token = telegram_bot.TOKEN
        original_chat = telegram_bot.CHAT_ID_ENV
        original_inbox = telegram_bot.INBOX_DIR
        original_logs = telegram_bot.LOG_DIR

        try:
            telegram_bot.TOKEN = "token_prueba"
            telegram_bot.CHAT_ID_ENV = "123456"
            telegram_bot.INBOX_DIR = temp_inbox
            telegram_bot.LOG_DIR = temp_logs
            telegram_bot.validate_config()
        finally:
            telegram_bot.TOKEN = original_token
            telegram_bot.CHAT_ID_ENV = original_chat
            telegram_bot.INBOX_DIR = original_inbox
            telegram_bot.LOG_DIR = original_logs
            shutil.rmtree(temp_inbox, ignore_errors=True)
            shutil.rmtree(temp_logs, ignore_errors=True)

    def test_detecta_consulta_de_recordatorios_pendientes(self):
        self.assertTrue(
            telegram_bot.is_pending_reminders_query("¿Qué recordatorios tengo pendientes?")
        )
        self.assertTrue(
            telegram_bot.is_pending_reminders_query("recordatorios pendientes")
        )
        self.assertFalse(
            telegram_bot.is_pending_reminders_query("recuérdame revisar el artículo")
        )


if __name__ == "__main__":
    unittest.main()
