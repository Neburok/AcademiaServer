from datetime import datetime
import os
from .logger import log_event
#INBOX_DIR = "inbox"
from .config import INBOX_DIR
import json
from .models import Idea


INBOX_DIR = "inbox"


def ensure_inbox_directory():
    os.makedirs(INBOX_DIR, exist_ok=True)

def generate_daily_id():
    today_str = datetime.now().strftime("%Y%m%d")
    ensure_inbox_directory()

    existing_files = os.listdir(INBOX_DIR)
    daily_ids = [
        f for f in existing_files
        if f.startswith(today_str)
    ]

    counter = len(daily_ids) + 1
    return f"{today_str}-{counter:03d}"


def generate_id():
    today = datetime.now().strftime("%Y%m%d")

    if not os.path.exists(INBOX_DIR):
        os.makedirs(INBOX_DIR)

    files = [f for f in os.listdir(INBOX_DIR) if f.startswith(today)]

    counter = len(files) + 1

    return f"{today}-{counter:03d}"


def save_idea(note: dict):

    # Validación mínima
    if "content" not in note:
        raise ValueError("La nota debe contener 'content'")

    idea_id = generate_id()

    note["id"] = idea_id
    note["created_at"] = datetime.now().isoformat()

    # valores por defecto
    note.setdefault("type", "nota")
    note.setdefault("title", note["content"][:60])
    note.setdefault("tags", [])
    note.setdefault("metadata", {})
    note.setdefault("links", [])
    note.setdefault("source", "unknown")

    filepath = os.path.join(INBOX_DIR, f"{idea_id}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(note, f, ensure_ascii=False, indent=4)

    return note

def list_ideas():
    if not os.path.exists(INBOX_DIR):
        return []

    files = sorted(os.listdir(INBOX_DIR))
    return files

import json

def load_all_ideas():
    ideas = []

    if not os.path.exists(INBOX_DIR):
        return ideas

    files = sorted(os.listdir(INBOX_DIR))

    for filename in files:
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(INBOX_DIR, filename)

        if os.path.getsize(filepath) == 0:
            continue  # saltar archivos vacíos

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                idea = json.load(f)
                ideas.append(idea)
        except json.JSONDecodeError:
            print(f"⚠️ Archivo corrupto ignorado: {filename}")
            continue

    return ideas

def get_idea_by_id(idea_id: str):
    filepath = os.path.join(INBOX_DIR, f"{idea_id}.json")

    if not os.path.exists(filepath):
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def search_ideas(query: str):
    ideas = load_all_ideas()
    query = query.lower()

    return [
        idea for idea in ideas
        if query in idea["title"].lower()
        or query in idea["content"].lower()
    ]
