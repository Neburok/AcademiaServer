from datetime import datetime
import os
from .logger import log_event
#INBOX_DIR = "inbox"
from .config import INBOX_DIR
import json
from .models import Idea




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

import json
from .models import Idea


def save_idea(title, content, tags=None, source="cli"):
    if tags is None:
        tags = []

    ensure_inbox_directory()

    idea_id = generate_daily_id()

    idea = Idea(
        id=idea_id,
        title=title,
        content=content,
        created_at=datetime.now(),
        tags=tags,
        source=source
    )

    filename = f"{idea.id}.json"
    filepath = os.path.join(INBOX_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(idea.dict(), f, indent=4, default=str)

    log_event(f"Idea guardada: {idea.id}")

    return idea

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
