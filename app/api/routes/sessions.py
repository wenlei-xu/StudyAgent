"""Sessions REST API — CRUD operations for learning sessions."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

from app.models.session import SessionCreate, SessionResponse

router = APIRouter()

# In-memory fallback (replaced by DB repositories in Phase 4 with real PostgreSQL)
_sessions: dict[str, dict] = {}


@router.get("/", response_model=dict)
async def list_sessions():
    return {
        "sessions": [
            {
                "id": s["id"],
                "thread_id": s["thread_id"],
                "learning_goal": s["learning_goal"],
                "progress": s["progress"],
                "status": s["status"],
                "created_at": s["created_at"],
            }
            for s in _sessions.values()
        ]
    }


@router.post("/", response_model=dict)
async def create_session(body: SessionCreate):
    sid = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    session = {
        "id": sid,
        "thread_id": thread_id,
        "learning_goal": body.learning_goal,
        "progress": 0.0,
        "status": "active",
        "created_at": now.isoformat(),
    }
    _sessions[sid] = session
    return session


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    _sessions.pop(session_id, None)
    return {"id": session_id, "status": "deleted"}
