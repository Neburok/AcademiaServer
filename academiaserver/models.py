from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import uuid


class Idea(BaseModel):
    id: str
    title: str
    content: str
    created_at: datetime
    tags: List[str] = []
    source: Optional[str] = "unknown"

   # @staticmethod
   # def create(title: str, content: str, source: str = "cli"):
   #     return Idea(
   #         id=str(uuid.uuid4()),
   #         title=title,
   #         content=content,
   #         created_at=datetime.now(),
   #         tags=[],
   #         source=source
   #     )