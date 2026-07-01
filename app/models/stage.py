"""Stage & homework models for the staged learning plan feature."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StageResponse(BaseModel):
    """A single learning stage returned to the frontend."""
    id: int
    stage_number: int
    title: str
    description: str
    homework: str
    status: str  # "locked" | "active" | "completed"
    created_at: Optional[datetime] = None


class StageListResponse(BaseModel):
    """Wrapper for stage list endpoint."""
    stages: list[StageResponse]


class HomeworkSubmitRequest(BaseModel):
    """User submits homework answer/response for evaluation."""
    answer: str = Field(..., min_length=1, description="用户提交的作业答案")


class HomeworkResultResponse(BaseModel):
    """Result of homework evaluation."""
    passed: bool
    feedback: str
    stage_number: int
    next_stage_unlocked: bool = False
