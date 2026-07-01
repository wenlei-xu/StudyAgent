"""Error notebook repository."""

import json
from datetime import datetime, timezone

from app.db.repositories.base import BaseRepository


class ErrorRepository(BaseRepository):
    async def add_error(self, session_id: str, error_entry: dict):
        await self.execute(
            """INSERT INTO error_notebook (session_id, quiz_data, user_answer, is_correct, created_at)
               VALUES ($1, $2, $3, $4, $5)""",
            session_id,
            json.dumps(error_entry, ensure_ascii=False),
            error_entry.get("user_answer", ""),
            False,
            datetime.now(timezone.utc).replace(tzinfo=None),
        )

    async def get_error_notebook(self, session_id: str) -> list[dict]:
        rows = await self.fetch(
            "SELECT quiz_data, created_at FROM error_notebook WHERE session_id = $1 ORDER BY created_at DESC",
            session_id,
        )
        return [json.loads(r["quiz_data"]) for r in rows]

    async def sample_old_errors(self, session_id: str, limit: int = 3) -> list[dict]:
        rows = await self.fetch(
            """SELECT quiz_data FROM error_notebook
               WHERE session_id = $1
               ORDER BY RANDOM() LIMIT $2""",
            session_id, limit,
        )
        return [json.loads(r["quiz_data"]) for r in rows]

    async def sample_old_errors_any(self, limit: int = 3) -> list[dict]:
        """Sample errors from any session for spaced repetition."""
        rows = await self.fetch(
            """SELECT quiz_data FROM error_notebook
               ORDER BY RANDOM() LIMIT $1""",
            limit,
        )
        return [json.loads(r["quiz_data"]) for r in rows]
