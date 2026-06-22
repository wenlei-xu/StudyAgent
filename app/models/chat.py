from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户消息文本")


class SSEEvent(BaseModel):
    type: str
    content: str | None = None
    data: dict | None = None
