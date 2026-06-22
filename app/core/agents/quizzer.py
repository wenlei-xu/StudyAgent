"""Quizzer agent — generates structured quiz questions."""

import json
import time
import random

from pydantic import BaseModel, Field

from app.core.agents.base import BaseAgent
from app.core.prompts.quizzer import QUIZZER_SYSTEM_PROMPT
from app.config import settings


class QuizOptionModel(BaseModel):
    key: str
    text: str


class QuizQuestionModel(BaseModel):
    id: str
    question: str
    options: list[QuizOptionModel]
    correct_answer: str
    explanation: str
    knowledge_point: str


class QuizResponseModel(BaseModel):
    questions: list[QuizQuestionModel]


class QuizzerAgent(BaseAgent):
    def __init__(self):
        super().__init__(model_name=settings.quizzer_model)

    def build_prompt(self, state: dict) -> tuple[str, str]:
        knowledge_map = state.get("knowledge_map", {})
        weak = [k for k, v in knowledge_map.items() if v == "未掌握"]
        mastered = [k for k, v in knowledge_map.items() if v == "已掌握"]

        errors = state.get("error_notebook", [])
        recent_errors = errors[-3:] if errors else []

        system = QUIZZER_SYSTEM_PROMPT.format(
            learning_goal=state.get("learning_goal", "未设定"),
            weak_points=", ".join(weak) if weak else "暂无（全范围出题）",
            recent_errors=json.dumps(recent_errors, ensure_ascii=False) if recent_errors else "暂无错题",
            mastered_points=", ".join(mastered) if mastered else "暂无",
            question_count=1,
        )

        return system, "请根据我的学习情况出一道题"

    async def run(self, state: dict) -> list[dict]:
        system, user = self.build_prompt(state)
        try:
            result = await self.generate_structured(system, user, QuizResponseModel)
            return [q.model_dump() for q in result.questions]
        except Exception:
            # Fallback: generate plain text and wrap as a single question
            text = await self.generate(system, user)
            return [{
                "id": f"q_{int(time.time())}_{random.randint(0, 9999)}",
                "question": text[:200],
                "options": [
                    {"key": "A", "text": "（结构化输出失败，请重试）"},
                ],
                "correct_answer": "A",
                "explanation": "出题模块暂时不可用，请重试",
                "knowledge_point": state.get("learning_goal", "未分类"),
            }]


quizzer_agent = QuizzerAgent()
