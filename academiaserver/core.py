from datetime import datetime
import os
from .logger import log_event
#INBOX_DIR = "inbox"
from .config import INBOX_DIR


def ensure_inbox_directory():
    os.makedirs(INBOX_DIR, exist_ok=True)

def save_idea(text):
    ensure_inbox_directory()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}.md"
    filepath = os.path.join(INBOX_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Idea Académica\n\n")
        f.write(f"**Fecha:** {datetime.now()}\n\n")
        f.write(text)

    log_event(f"Idea guardada: {filename}")

def list_ideas():
    if not os.path.exists(INBOX_DIR):
        print("No hay ideas guardadas aún.")
        return

    files = sorted(os.listdir(INBOX_DIR))
    if not files:
        print("No hay ideas guardadas.")
        return

    for f in files:
        print(f)

