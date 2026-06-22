from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户消息文本")
    model: str | None = Field(None, description="前端选择的模型，覆盖默认值")


class SSEEvent(BaseModel):
    type: str
    content: str | None = None
    data: dict | None = None
