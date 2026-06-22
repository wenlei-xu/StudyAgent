"""Sessions REST API — CRUD operations for learning sessions.

Uses SessionRepository backed by PostgreSQL (via asyncpg connection pool).
"""

from fastapi import APIRouter

from app.db.connection import get_connection, release_connection
from app.db.repositories.session_repo import SessionRepository
from app.models.session import SessionCreate

router = APIRouter()


@router.get("/")
async def list_sessions():
    conn = await get_connection()
    try:
        repo = SessionRepository(conn)
        sessions = await repo.list_sessions()
        return {"sessions": sessions}
    finally:
        await release_connection(conn)


@router.post("/")
async def create_session(body: SessionCreate):
    conn = await get_connection()
    try:
        repo = SessionRepository(conn)
        session = await repo.create_session(body.learning_goal)
        return session
    finally:
        await release_connection(conn)


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    conn = await get_connection()
    try:
        repo = SessionRepository(conn)
        await repo.delete_session(session_id)
        return {"id": session_id, "status": "deleted"}
    finally:
        await release_connection(conn)
