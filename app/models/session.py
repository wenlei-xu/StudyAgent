from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SessionCreate(BaseModel):
    learning_goal: str = Field(..., min_length=1, max_length=500, description="学习目标")


class SessionResponse(BaseModel):
    id: str
    thread_id: str
    learning_goal: str
    progress: float
    status: str
    created_at: datetime
