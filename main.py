from datetime import datetime
import os

INBOX_DIR = "inbox"
LOG_DIR = "logs"

def ensure_directories():
    os.makedirs(INBOX_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

def save_idea(text):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}.md"
    filepath = os.path.join(INBOX_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Idea\n\n")
        f.write(f"**Fecha:** {datetime.now()}\n\n")
        f.write(text)

    log_event(f"Idea guardada: {filename}")

def log_event(message):
    log_file = os.path.join(LOG_DIR, "activity.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {message}\n")

if __name__ == "__main__":
    ensure_directories()
    idea = input("Escribe tu idea académica: ")
    save_idea(idea)
    print("Idea guardada correctamente.")