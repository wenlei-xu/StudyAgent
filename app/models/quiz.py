from pydantic import BaseModel, Field
from typing import Optional


class QuizOption(BaseModel):
    key: str = Field(..., description="选项标识 A/B/C/D")
    text: str = Field(..., description="选项文本")


class QuizCard(BaseModel):
    id: str
    question: str = Field(..., description="题目题干")
    options: list[QuizOption]
    correct_answer: str = Field(..., description="正确答案的 key")
    explanation: str = Field(..., description="题目解析")
    knowledge_point: str = Field(..., description="关联的知识点名称")


class AnswerSubmission(BaseModel):
    session_id: str
    quiz_id: str
    selected_option: str = Field(..., description="用户选择的选项 key")
