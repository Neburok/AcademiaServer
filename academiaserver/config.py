import os
from dotenv import load_dotenv

load_dotenv()


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


INBOX_DIR = os.getenv("INBOX_DIR", "inbox")
LOG_DIR = os.getenv("LOG_DIR", "logs")
SCHEDULER_INTERVAL_SECONDS = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "60"))
REMINDER_MAX_RETRIES = int(os.getenv("REMINDER_MAX_RETRIES", "3"))
REMINDER_RETRY_DELAY_SECONDS = int(os.getenv("REMINDER_RETRY_DELAY_SECONDS", "5"))
AI_PROVIDER = os.getenv("AI_PROVIDER", "rules")
AI_TIMEOUT_SECONDS = int(os.getenv("AI_TIMEOUT_SECONDS", "25"))
AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "2"))
AI_HTTP_MAX_RETRIES = int(os.getenv("AI_HTTP_MAX_RETRIES", "2"))
AI_HTTP_RETRY_DELAY_SECONDS = int(os.getenv("AI_HTTP_RETRY_DELAY_SECONDS", "1"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "gemma3")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "embeddinggemma")
AI_ENABLE_CLOUD_FALLBACK = _to_bool(os.getenv("AI_ENABLE_CLOUD_FALLBACK"), default=False)
