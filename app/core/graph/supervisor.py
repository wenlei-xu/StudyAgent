"""Supervisor node — LLM-powered routing decision.

Reads AgentState, decides next node. NEVER modifies state.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from app.core.state import AgentState
from app.core.prompts.supervisor import SUPERVISOR_SYSTEM_PROMPT
from app.config import settings

VALID_TARGETS = {"explainer", "quizzer", "check_answer", "recommender", "FINISH"}


async def supervisor_node(state: AgentState, config: RunnableConfig) -> dict:
    """Analyze state and return routing decision."""
    knowledge_map = state.get("knowledge_map", {})
    current_phase = state.get("current_phase", "explaining")
    learning_goal = state.get("learning_goal", "未设定")
    progress = state.get("progress", 0.0)

    # Build conversation history snippet
    messages = state.get("messages", [])
    history_lines = []
    for m in messages[-10:]:
        role = "用户" if getattr(m, "type", None) == "human" else "AI"
        content = getattr(m, "content", "")
        history_lines.append(f"[{role}]: {content[:200]}")
    conversation_history = "\n".join(history_lines)

    system = SUPERVISOR_SYSTEM_PROMPT.format(
        learning_goal=learning_goal,
        current_phase=current_phase,
        knowledge_map=str(knowledge_map) if knowledge_map else "暂无数据",
        progress=f"{progress:.0%}",
        conversation_history=conversation_history,
    )

    # Get the last user message
    last_user_msg = ""
    for m in reversed(messages):
        if hasattr(m, "type") and m.type == "human":
            last_user_msg = m.content
            break

    model = ChatOpenAI(
        model=settings.supervisor_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=0.1,
        timeout=15,
        max_retries=1,
    )

    try:
        response = await model.ainvoke([
            SystemMessage(content=system),
            HumanMessage(content=f"用户最新消息: {last_user_msg}\n\n请决定下一步路由。只回复模块名称。"),
        ])
        target = response.content.strip().lower()
    except Exception:
        target = "explainer"

    # Validate and normalize target
    if target not in VALID_TARGETS:
        target = "explainer"

    if target == "FINISH":
        target = "__end__"

    return {"current_phase": target if target != "__end__" else "explaining", "next": target}
