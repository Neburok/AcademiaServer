import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "academia.db")
LOG_DIR = os.getenv("LOG_DIR", "logs")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
SCHEDULER_INTERVAL_SECONDS = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "60"))
REMINDER_MAX_RETRIES = int(os.getenv("REMINDER_MAX_RETRIES", "3"))
REMINDER_RETRY_DELAY_SECONDS = int(os.getenv("REMINDER_RETRY_DELAY_SECONDS", "5"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_CHAT_MODEL = os.getenv("ANTHROPIC_CHAT_MODEL", "claude-3-5-sonnet-20241022")
ANTHROPIC_MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "1024"))
