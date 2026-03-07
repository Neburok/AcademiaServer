from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .core import get_daily_digest, get_idea_by_id, list_ideas, save_idea, search_ideas
from .logger import show_logs

app = FastAPI(title="AcademiaServer API")


class IdeaRequest(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = []


@app.post("/save")
def save_idea_endpoint(request: IdeaRequest):
    note = {
        "title": request.title,
        "content": request.content,
        "tags": request.tags or [],
        "source": "api",
    }
    return save_idea(note)


@app.get("/list")
def list_ideas_endpoint():
    return {"ideas": list_ideas()}


@app.get("/log")
def show_logs_endpoint():
    return {"logs": show_logs()}


@app.get("/idea/{idea_id}")
def get_idea_endpoint(idea_id: str):
    idea = get_idea_by_id(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea no encontrada")

    return idea


@app.get("/search")
def search_ideas_endpoint(query: str, backend: str = "keyword"):
    return {"results": search_ideas(query=query, backend=backend)}


@app.get("/digest/daily")
def daily_digest_endpoint():
    return get_daily_digest()
