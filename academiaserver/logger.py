from datetime import datetime
import os
 
# LOG_DIR = "logs"

from .config import LOG_DIR

def ensure_log_directory():
    os.makedirs(LOG_DIR, exist_ok=True)

def log_event(message):
    ensure_log_directory()
    log_file = os.path.join(LOG_DIR, "activity.log")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {message}\n")