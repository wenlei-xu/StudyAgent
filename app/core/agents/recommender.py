"""Recommender agent — suggests learning resources based on weak points."""

from pydantic import BaseModel

from app.core.agents.base import BaseAgent
from app.core.prompts.recommender import RECOMMENDER_SYSTEM_PROMPT
from app.config import settings


class ResourceCardModel(BaseModel):
    title: str
    url: str
    summary: str
    relevance: str


class RecommendationResultModel(BaseModel):
    cards: list[ResourceCardModel]


class RecommenderAgent(BaseAgent):
    def __init__(self):
        super().__init__(model_name=settings.recommender_model)

    def build_prompt(self, state: dict) -> tuple[str, str]:
        knowledge_map = state.get("knowledge_map", {})
        weak = [k for k, v in knowledge_map.items() if v == "未掌握"]

        errors = state.get("error_notebook", [])
        error_kp = list({e.get("knowledge_point", "") for e in errors if e.get("knowledge_point")})

        system = RECOMMENDER_SYSTEM_PROMPT.format(
            learning_goal=state.get("learning_goal", "未设定"),
            weak_points=", ".join(weak) if weak else "暂无明确薄弱点",
            error_knowledge_points=", ".join(error_kp) if error_kp else "暂无",
            progress=state.get("progress", 0.0),
        )

        return system, "请推荐学习资源"

    async def run(self, state: dict, model_override: str | None = None) -> list[dict]:
        system, user = self.build_prompt(state)
        try:
            result = await self.generate_structured(system, user, RecommendationResultModel, model_override)
            return [c.model_dump() for c in result.cards]
        except Exception:
            return [{
                "title": "推荐系统暂不可用",
                "url": "",
                "summary": "结构化输出失败，请稍后重试",
                "relevance": "系统错误",
            }]


recommender_agent = RecommenderAgent()
