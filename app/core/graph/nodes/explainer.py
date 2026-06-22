"""Explainer node — calls ExplainerAgent and streams LLM tokens."""

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage

from app.core.state import AgentState
from app.core.agents.explainer import explainer_agent


async def explainer_node(state: AgentState, config: RunnableConfig) -> dict:
    """Generate explanation using LLM."""
    model_override = config.get("configurable", {}).get("model")
    response_text = await explainer_agent.run(dict(state), model_override)

    return {
        "messages": [AIMessage(content=response_text)],
        "current_phase": "explaining",
    }
