"""Quizzer agent — generates structured quiz questions with spaced repetition."""

import json
import time
import random
import logging

from pydantic import BaseModel, Field

from app.core.agents.base import BaseAgent
from app.core.prompts.quizzer import QUIZZER_SYSTEM_PROMPT
from app.db.connection import get_pool
from app.db.repositories.error_repo import ErrorRepository
from app.config import settings

logger = logging.getLogger(__name__)


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

    async def build_prompt(self, state: dict) -> tuple[str, str]:
        knowledge_map = state.get("knowledge_map", {})
        weak = [k for k, v in knowledge_map.items() if v == "未掌握"]
        mastered = [k for k, v in knowledge_map.items() if v == "已掌握"]

        # In-memory errors (latest from current session)
        errors = state.get("error_notebook", [])
        recent_errors = errors[-3:] if errors else []

        # Load older errors from DB for spaced repetition
        old_errors = []
        session_id = ""
        messages = state.get("messages", [])
        # Try to infer session_id from state
        for m in reversed(messages):
            if hasattr(m, "type") and m.type == "human":
                break

        try:
            pool = await get_pool()
            async with pool.acquire() as conn:
                repo = ErrorRepository(conn)
                # Get all errors for spaced repetition sampling
                all_errors = await repo.get_error_notebook(state.get("thread_id", "")) if state.get("thread_id") else []
                if not all_errors:
                    # Sample from any session if current session has no errors
                    old_errors_sample = await repo.sample_old_errors_any(limit=2)
                    old_errors = old_errors_sample
                else:
                    old_errors = all_errors[:5]
        except Exception:
            logger.exception("Failed to load old errors for quizzer")

        # Merge recent and old errors for the prompt
        all_error_context = list(recent_errors)
        for old in old_errors:
            if old not in all_error_context:
                all_error_context.append(old)

        system = QUIZZER_SYSTEM_PROMPT.format(
            learning_goal=state.get("learning_goal", "未设定"),
            weak_points=", ".join(weak) if weak else "暂无（全范围出题）",
            recent_errors=json.dumps(all_error_context, ensure_ascii=False) if all_error_context else "暂无错题",
            mastered_points=", ".join(mastered) if mastered else "暂无",
            question_count=1,
        )

        return system, "请根据我的学习情况出一道题"

    async def run(self, state: dict, model_override: str | None = None) -> list[dict]:
        system, user = await self.build_prompt(state)
        try:
            result = await self.generate_structured(system, user, QuizResponseModel, model_override)
            return [q.model_dump() for q in result.questions]
        except Exception:
            # Fallback: generate plain text and wrap as a single question
            text = await self.generate(system, user, model_override)
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
