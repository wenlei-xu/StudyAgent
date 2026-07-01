"""Stages REST API — stage plan generation, listing, and homework submission."""

from fastapi import APIRouter

from app.db.connection import get_connection, release_connection
from app.db.repositories.stage_repo import StageRepository
from app.db.repositories.session_repo import SessionRepository
from app.core.agents.stage_planner import StagePlannerAgent
from app.core.agents.homework_checker import HomeworkCheckerAgent
from app.models.stage import (
    StageResponse,
    StageListResponse,
    HomeworkSubmitRequest,
    HomeworkResultResponse,
)

router = APIRouter()


@router.get("/{session_id}/stages")
async def list_stages(session_id: str):
    """Get all learning stages for a session."""
    conn = await get_connection()
    try:
        repo = StageRepository(conn)
        stages = await repo.get_stages(session_id)
        return {"stages": stages}
    finally:
        await release_connection(conn)


@router.post("/{session_id}/stages/generate")
async def generate_stages(session_id: str):
    """Generate a learning stage plan for the session via LLM.

    This is called once after session creation. If stages already exist,
    returns the existing stages instead of regenerating.
    """
    conn = await get_connection()
    try:
        stage_repo = StageRepository(conn)
        session_repo = SessionRepository(conn)

        # Check if stages already exist
        if await stage_repo.has_stages(session_id):
            stages = await stage_repo.get_stages(session_id)
            return {"stages": stages, "regenerated": False}

        # Get the session to read learning_goal
        session = await session_repo.get_session(session_id)
        if not session:
            return {"error": "会话不存在"}, 404

        # Generate stages via LLM
        planner = StagePlannerAgent()
        stage_data = await planner.generate_stages(session["learning_goal"])

        # Persist stages
        stages = await stage_repo.create_stages(session_id, stage_data)

        return {"stages": stages, "regenerated": True}
    finally:
        await release_connection(conn)


@router.post("/{session_id}/stages/{stage_id}/submit-homework")
async def submit_homework(session_id: str, stage_id: int, body: HomeworkSubmitRequest):
    """Submit homework for a stage. LLM evaluates and decides pass/fail.

    If passed, the next stage is automatically unlocked.
    """
    conn = await get_connection()
    try:
        stage_repo = StageRepository(conn)
        session_repo = SessionRepository(conn)

        # Get current stage
        stage = await stage_repo.get_stage(stage_id)
        if not stage or stage["session_id"] != session_id:
            return {"error": "阶段不存在"}, 404

        if stage["status"] == "locked":
            return {"error": "该阶段尚未解锁，请先完成前面的阶段"}, 400

        if stage["status"] == "completed":
            return {"error": "该阶段已完成"}, 400

        # Get session for learning goal context
        session = await session_repo.get_session(session_id)
        if not session:
            return {"error": "会话不存在"}, 404

        # Evaluate homework
        checker = HomeworkCheckerAgent()
        result = await checker.check_homework(
            learning_goal=session["learning_goal"],
            stage_title=stage["title"],
            stage_description=stage["description"],
            homework=stage["homework"],
            user_answer=body.answer,
        )

        next_unlocked = False
        if result["passed"]:
            # Mark current stage as completed
            await stage_repo.update_stage_status(stage_id, "completed")

            # Unlock the next stage
            stages = await stage_repo.get_stages(session_id)
            for s in stages:
                if s["stage_number"] == stage["stage_number"] + 1 and s["status"] == "locked":
                    await stage_repo.update_stage_status(s["id"], "active")
                    next_unlocked = True
                    break

            # Update overall session progress
            completed = sum(1 for s in stages if s["status"] == "completed" or s["id"] == stage_id)
            progress = completed / len(stages) if stages else 0
            await session_repo.update_progress(session_id, progress)

        return HomeworkResultResponse(
            passed=result["passed"],
            feedback=result["feedback"],
            stage_number=stage["stage_number"],
            next_stage_unlocked=next_unlocked,
        )
    finally:
        await release_connection(conn)
