from datetime import datetime
import os

from .config import LOG_DIR

def ensure_log_directory():
    os.makedirs(LOG_DIR, exist_ok=True)

def log_event(message):
    ensure_log_directory()
    log_file = os.path.join(LOG_DIR, "activity.log")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {message}\n")

def show_logs():
    log_file = os.path.join(LOG_DIR, "activity.log")

    if not os.path.exists(log_file):
        print("No hay logs aún.")
        return

    with open(log_file, "r", encoding="utf-8") as f:
        print(f.read())