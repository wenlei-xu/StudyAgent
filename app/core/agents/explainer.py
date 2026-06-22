"""Explainer agent — RAG-enhanced knowledge explanation with web search fallback."""

from app.core.agents.base import BaseAgent
from app.core.prompts.explainer import EXPLAINER_SYSTEM_PROMPT
from app.db.vector.store import similarity_search
from app.core.tools.search import web_search
from app.config import settings


class ExplainerAgent(BaseAgent):
    def __init__(self):
        super().__init__(model_name=settings.explainer_model)

    async def build_prompt(self, state: dict) -> tuple[str, str]:
        knowledge_map = state.get("knowledge_map", {})
        mastered = [k for k, v in knowledge_map.items() if v == "已掌握"]
        weak = [k for k, v in knowledge_map.items() if v == "未掌握"]

        errors = state.get("error_notebook", [])
        error_points = list({e.get("knowledge_point", "") for e in errors[-5:] if e.get("knowledge_point")})

        # Get the last user message as search query
        messages = state.get("messages", [])
        last_user_msg = ""
        for m in reversed(messages):
            if hasattr(m, "type") and m.type == "human":
                last_user_msg = m.content
                break

        # RAG: search local knowledge base
        rag_texts = ["（知识库中暂无相关内容）"]
        try:
            results = await similarity_search(last_user_msg or state.get("learning_goal", ""), top_k=3)
            if results:
                rag_texts = []
                for i, r in enumerate(results, 1):
                    rag_texts.append(f"【本地资料 {i}】（相似度: {r['similarity']:.2f}）\n{r['content']}")
        except Exception:
            pass

        # Web search: fallback for broader context
        web_text = ""
        try:
            if settings.tavily_api_key:
                search_result = await web_search.ainvoke(last_user_msg or state.get("learning_goal", ""))
                if search_result and "（" not in search_result:
                    web_text = f"\n\n## 网络搜索结果\n{search_result}"
        except Exception:
            pass

        rag_context = "\n\n".join(rag_texts) + web_text

        system = EXPLAINER_SYSTEM_PROMPT.format(
            learning_goal=state.get("learning_goal", "未设定"),
            mastered_points=", ".join(mastered) if mastered else "暂无",
            weak_points=", ".join(weak) if weak else "暂无",
            error_points=", ".join(error_points) if error_points else "暂无",
            rag_context=rag_context,
        )

        return system, last_user_msg or "请开始讲解"

    async def run(self, state: dict, model_override: str | None = None) -> str:
        system, user = await self.build_prompt(state)
        return await self.generate(system, user, model_override)


# Singleton
explainer_agent = ExplainerAgent()
