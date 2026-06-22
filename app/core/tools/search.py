"""Tavily search tool — web search for extended knowledge."""

from langchain_core.tools import tool
from tavily import TavilyClient

from app.config import settings

_client = TavilyClient(api_key=settings.tavily_api_key) if settings.tavily_api_key else None


@tool
async def web_search(query: str) -> str:
    """Search the web for learning resources and information.

    Args:
        query: The search query.

    Returns:
        Formatted search results.
    """
    if _client is None:
        return "（联网搜索未配置，请设置 TAVILY_API_KEY）"

    try:
        response = _client.search(query, max_results=3)
        results = response.get("results", [])
        if not results:
            return "（未找到相关搜索结果）"

        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"{i}. **{r.get('title', '无标题')}**\n   {r.get('content', '')}\n   {r.get('url', '')}")

        return "\n\n".join(formatted)
    except Exception as e:
        return f"（搜索服务暂时不可用: {str(e)}）"
