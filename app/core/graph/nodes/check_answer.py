"""Check Answer node — evaluates student answers and updates knowledge state."""

import logging

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage

from app.core.state import AgentState
from app.core.agents.checker import checker_agent
from app.db.connection import get_pool
from app.db.repositories.error_repo import ErrorRepository

logger = logging.getLogger(__name__)


async def check_answer_node(state: AgentState, config: RunnableConfig) -> dict:
    """Evaluate answer and update knowledge_map, progress, error_notebook."""
    model_override = config.get("configurable", {}).get("model")
    session_id = config.get("configurable", {}).get("thread_id", "")
    result = await checker_agent.run(dict(state), model_override)

    quiz = state.get("quiz_pending") or {}
    knowledge_point = quiz.get("knowledge_point", "未分类")
    is_correct = result.get("correct", False)
    status = result.get("knowledge_point_status", "learning")

    # Update knowledge map
    new_knowledge = dict(state.get("knowledge_map", {}))
    new_knowledge[knowledge_point] = (
        "已掌握" if status == "mastered" else ("学习中" if status == "learning" else "未掌握")
    )

    # Update progress
    total_points = len(new_knowledge) or 1
    mastered = sum(1 for v in new_knowledge.values() if v == "已掌握")
    in_progress = sum(1 for v in new_knowledge.values() if v == "学习中")
    new_progress = (mastered * 1.0 + in_progress * 0.5) / total_points

    # Update error notebook
    new_errors = []
    if not is_correct:
        error_entry = {
            "quiz_id": quiz.get("id", ""),
            "question": quiz.get("question", ""),
            "correct_answer": quiz.get("correct_answer", ""),
            "knowledge_point": knowledge_point,
            "timestamp": "",
        }
        new_errors.append(error_entry)

        # Persist to DB
        if session_id:
            try:
                pool = await get_pool()
                async with pool.acquire() as conn:
                    repo = ErrorRepository(conn)
                    await repo.add_error(session_id, error_entry)
            except Exception:
                logger.exception("Failed to persist error to DB")

    # Format feedback
    emoji = "✅" if is_correct else "❌"
    feedback = f"{emoji} {result.get('explanation', '')}"

    return {
        "messages": [AIMessage(content=feedback)],
        "knowledge_map": new_knowledge,
        "progress": round(new_progress, 2),
        "error_notebook": new_errors,
        "quiz_pending": None,
        "current_phase": "checking",
    }
