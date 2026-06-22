"""Checker agent — evaluates student answers."""

from pydantic import BaseModel

from app.core.agents.base import BaseAgent
from app.core.prompts.checker import CHECKER_SYSTEM_PROMPT
from app.config import settings


class CheckResultModel(BaseModel):
    correct: bool
    explanation: str
    knowledge_point_status: str  # mastered / learning / unfamiliar


class CheckerAgent(BaseAgent):
    def __init__(self):
        super().__init__(model_name=settings.checker_model)

    def build_prompt(self, state: dict) -> tuple[str, str]:
        quiz_pending = state.get("quiz_pending") or {}

        # The last user message is the answer submission
        messages = state.get("messages", [])
        last_user_msg = ""
        for m in reversed(messages):
            if hasattr(m, "type") and m.type == "human":
                last_user_msg = m.content
                break

        system = CHECKER_SYSTEM_PROMPT.format(
            question=quiz_pending.get("question", "未知题目"),
            options=str(quiz_pending.get("options", [])),
            correct_answer=quiz_pending.get("correct_answer", ""),
            knowledge_point=quiz_pending.get("knowledge_point", "未分类"),
            selected_option=last_user_msg,
        )

        return system, "请批改"

    async def run(self, state: dict) -> dict:
        system, user = self.build_prompt(state)
        try:
            result = await self.generate_structured(system, user, CheckResultModel)
            return result.model_dump()
        except Exception:
            quiz = state.get("quiz_pending") or {}
            selected = ""
            messages = state.get("messages", [])
            for m in reversed(messages):
                if hasattr(m, "type") and m.type == "human":
                    selected = m.content.strip().upper()
                    break
            correct = selected == quiz.get("correct_answer", "").upper()
            return {
                "correct": correct,
                "explanation": quiz.get("explanation", "无法获取解析"),
                "knowledge_point_status": "mastered" if correct else "learning",
            }


checker_agent = CheckerAgent()
