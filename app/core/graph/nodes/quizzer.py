"""Quizzer node — generates quiz questions and updates state."""

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage

from app.core.state import AgentState
from app.core.agents.quizzer import quizzer_agent


async def quizzer_node(state: AgentState, config: RunnableConfig) -> dict:
    """Generate quiz questions and set quiz_pending."""
    model_override = config.get("configurable", {}).get("model")
    state_dict = dict(state)
    state_dict["thread_id"] = config.get("configurable", {}).get("thread_id", "")
    questions = await quizzer_agent.run(state_dict, model_override)

    if not questions:
        return {
            "messages": [AIMessage(content="暂时无法出题，请换个知识点试试。")],
            "current_phase": "explaining",
        }

    quiz = questions[0]
    # Format quiz as a readable message
    options_text = "\n".join(
        f"{opt['key']}. {opt['text']}" for opt in quiz["options"]
    )
    display = f"📝 **{quiz['question']}**\n\n{options_text}\n\n_请选择 A/B/C/D_"

    return {
        "messages": [AIMessage(content=display)],
        "quiz_pending": quiz,
        "current_phase": "quiz",
    }
