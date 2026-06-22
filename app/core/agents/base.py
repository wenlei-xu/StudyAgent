"""Base agent class — shared LLM binding, retry, and streaming support."""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings


class BaseAgent:
    def __init__(self, model_name: str | None = None):
        self.model = ChatOpenAI(
            model=model_name or settings.explainer_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.7,
            streaming=True,
            timeout=30,
            max_retries=1,
        )

    def _build_messages(self, system_prompt: str, user_prompt: str) -> list:
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        messages = self._build_messages(system_prompt, user_prompt)
        response = await self.model.ainvoke(messages)
        return response.content

    async def generate_structured(self, system_prompt: str, user_prompt: str, output_schema: type) -> dict:
        structured_model = self.model.with_structured_output(output_schema)
        messages = self._build_messages(system_prompt, user_prompt)
        return await structured_model.ainvoke(messages)
