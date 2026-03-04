from fastapi import FastAPI
from pydantic import BaseModel
from .core import save_idea, list_ideas
from .logger import show_logs
from .core import get_idea_by_id
from fastapi import HTTPException


app = FastAPI(title="AcademiaServer API")


class IdeaRequest(BaseModel):
    text: str


@app.post("/save")
def save_idea_endpoint(request: IdeaRequest):
    save_idea(request.text)
    return {"status": "Idea guardada correctamente"}


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