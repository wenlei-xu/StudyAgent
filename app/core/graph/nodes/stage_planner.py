"""Stage Planner Node — generates learning stages when user first sets a learning goal.

Called by the supervisor when the session has no stages yet.
Generates a staged learning plan via LLM and persists it to the database.
"""

import logging

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage

from app.core.state import AgentState
from app.core.agents.stage_planner import StagePlannerAgent
from app.db.connection import get_pool
from app.db.repositories.stage_repo import StageRepository
from app.db.repositories.session_repo import SessionRepository

logger = logging.getLogger(__name__)


async def stage_planner_node(state: AgentState, config: RunnableConfig) -> dict:
    """Generate learning stages from the user's learning goal and persist to DB."""
    session_id = config.get("configurable", {}).get("thread_id", "")
    learning_goal = state.get("learning_goal", "")
    messages = state.get("messages", [])

    # Extract the user's latest message as the learning goal context
    user_messages = [m for m in messages if hasattr(m, "type") and m.type == "human"]
    last_user_msg = user_messages[-1].content if user_messages else ""

    # If we don't have a concrete learning_goal yet, use the last user message
    if not learning_goal or learning_goal == "新学习会话":
        learning_goal = last_user_msg.strip()

    # Check if stages already exist for this session
    stages_exist = False
    if session_id:
        try:
            pool = await get_pool()
            async with pool.acquire() as conn:
                repo = StageRepository(conn)
                stages_exist = await repo.has_stages(session_id)
        except Exception:
            logger.exception("Failed to check if stages exist")

    if stages_exist:
        # Stages already exist, just return current state info
        try:
            pool = await get_pool()
            async with pool.acquire() as conn:
                repo = StageRepository(conn)
                stages = await repo.get_stages(session_id)
                active = next((s for s in stages if s["status"] == "active"), None)
                return {
                    "current_stage": active,
                    "stages": stages,
                }
        except Exception:
            logger.exception("Failed to load existing stages")
            # Return empty stages to prevent infinite retry
            return {"stages": []}

    # Generate stages via LLM
    planner = StagePlannerAgent()
    try:
        stage_data = await planner.generate_stages(learning_goal)
    except Exception:
        logger.exception("Failed to generate stages via LLM")
        # Fallback stages — always include stages to prevent infinite retry
        stage_data = planner._fallback_stages(learning_goal)
        return {
            "messages": [AIMessage(content=f"已为「{learning_goal}」生成默认学习计划，包含 {len(stage_data)} 个阶段。请开始学习！")],
            "current_stage": stage_data[0] if stage_data else None,
            "stages": stage_data,
        }

    # Persist to DB
    persisted_stages = []
    if session_id:
        try:
            pool = await get_pool()
            async with pool.acquire() as conn:
                stage_repo = StageRepository(conn)
                persisted_stages = await stage_repo.create_stages(session_id, stage_data)

                # Update session learning_goal if it was generic, and init progress
                session_repo = SessionRepository(conn)
                session = await session_repo.get_session(session_id)
                if session and (not session.get("learning_goal") or session["learning_goal"] == "新学习会话"):
                    # Update learning_goal in sessions table
                    await conn.execute(
                        "UPDATE sessions SET learning_goal = $1, updated_at = NOW() WHERE id = $2",
                        learning_goal[:500],
                        session_id,
                    )
                # Initialize progress based on stages (0 completed initially)
                await session_repo.update_progress(session_id, 0.0)
        except Exception:
            logger.exception("Failed to persist stages to DB")

    # Find active stage (first one)
    active_stage = None
    for s in (persisted_stages or stage_data):
        if s.get("status") == "active":
            active_stage = {
                "stage_number": s["stage_number"],
                "title": s["title"],
                "description": s.get("description", ""),
                "homework": s.get("homework", ""),
                "status": s["status"],
            }
            break

    # Build a brief summary message — explainer will start teaching next
    if persisted_stages or stage_data:
        stages_list = persisted_stages or stage_data
        stage_names = " → ".join(
            f"阶段{s['stage_number']}「{s['title']}」"
            for s in stages_list
        )
        first_stage = stages_list[0]
        summary = (
            f"好的！我已经为「{learning_goal}」制定了 {len(stages_list)} 个阶段的学习计划：\n\n"
            f"{stage_names}\n\n"
            f"每个阶段都有一份作业，通过后才能解锁下一阶段。"
            f"现在让我们从**阶段 1「{first_stage['title']}」**开始吧！"
        )
    else:
        summary = f"已为「{learning_goal}」生成学习计划，让我们开始吧！"

    return {
        "messages": [AIMessage(content=summary)],
        "current_stage": active_stage,
        "stages": persisted_stages or stage_data,
    }
