"""Recommender node — suggests learning resources."""

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage

from app.core.state import AgentState
from app.core.agents.recommender import recommender_agent


async def recommender_node(state: AgentState, config: RunnableConfig) -> dict:
    """Generate learning resource recommendations."""
    cards = await recommender_agent.run(dict(state))

    if not cards or cards[0].get("title") == "推荐系统暂不可用":
        return {
            "messages": [AIMessage(content="暂无可推荐的资源，请继续学习或换个知识点。")],
            "current_phase": "explaining",
        }

    # Format cards as a readable message
    lines = ["📚 **学习资源推荐**\n"]
    for i, card in enumerate(cards, 1):
        lines.append(f"{i}. [{card['title']}]({card['url']})")
        lines.append(f"   {card['summary']}")
        lines.append(f"   _{card['relevance']}_\n")

    return {
        "messages": [AIMessage(content="\n".join(lines))],
        "current_phase": "recommending",
    }
