import json
import os
from datetime import datetime

from .config import LOG_DIR


def ensure_log_directory():
    os.makedirs(LOG_DIR, exist_ok=True)


def log_event(event: str, level: str = "INFO", **context):
    ensure_log_directory()
    log_file = os.path.join(LOG_DIR, "activity.log")
    payload = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "event": event,
        "context": context,
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def show_logs():
    log_file = os.path.join(LOG_DIR, "activity.log")
    if not os.path.exists(log_file):
        return ""

    with open(log_file, "r", encoding="utf-8") as f:
        return f.read()
