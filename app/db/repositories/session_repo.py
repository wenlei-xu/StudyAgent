"""Session repository."""

import uuid
from datetime import datetime, timezone

from app.db.repositories.base import BaseRepository


class SessionRepository(BaseRepository):
    async def create_session(self, learning_goal: str, user_id: str = "default") -> dict:
        sid = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        await self.execute(
            """INSERT INTO sessions (id, thread_id, user_id, learning_goal, progress, status, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            sid, thread_id, user_id, learning_goal, 0.0, "active", now, now,
        )

        return {
            "id": sid,
            "thread_id": thread_id,
            "learning_goal": learning_goal,
            "progress": 0.0,
            "status": "active",
            "created_at": now.isoformat(),
        }

    async def get_session(self, session_id: str) -> dict | None:
        row = await self.fetchrow(
            """SELECT s.id, s.thread_id, s.learning_goal,
                      COALESCE(
                          (SELECT COUNT(*) FILTER (WHERE ls.status = 'completed')::float
                           / NULLIF(COUNT(*), 0)
                           FROM learning_stages ls WHERE ls.session_id = s.id),
                          s.progress
                      ) as progress,
                      s.status, s.created_at
               FROM sessions s WHERE s.id = $1""",
            session_id,
        )
        if row:
            row["created_at"] = row["created_at"].isoformat() if row.get("created_at") else ""
        return row

    async def list_sessions(self, user_id: str = "default") -> list[dict]:
        rows = await self.fetch(
            """SELECT s.id, s.thread_id, s.learning_goal,
                      COALESCE(
                          (SELECT COUNT(*) FILTER (WHERE ls.status = 'completed')::float
                           / NULLIF(COUNT(*), 0)
                           FROM learning_stages ls WHERE ls.session_id = s.id),
                          s.progress
                      ) as progress,
                      s.status, s.created_at
               FROM sessions s
               WHERE s.user_id = $1
               ORDER BY s.created_at DESC""",
            user_id,
        )
        for r in rows:
            r["created_at"] = r["created_at"].isoformat() if r.get("created_at") else ""
        return rows

    async def delete_session(self, session_id: str):
        await self.execute("DELETE FROM sessions WHERE id = $1", session_id)

    async def update_progress(self, session_id: str, progress: float):
        await self.execute(
            "UPDATE sessions SET progress = $1, updated_at = $2 WHERE id = $3",
            progress, datetime.now(timezone.utc), session_id,
        )
