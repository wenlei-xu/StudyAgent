from pydantic import BaseModel, Field
from typing import Literal


class KnowledgePoint(BaseModel):
    name: str
    status: Literal["mastered", "learning", "unfamiliar"]


class KnowledgeMap(BaseModel):
    points: list[KnowledgePoint]
    session_id: str
