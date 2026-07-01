"""Stage repository — CRUD for learning_stages table."""

from datetime import datetime, timezone

from app.db.repositories.base import BaseRepository


class StageRepository(BaseRepository):
    async def create_stages(self, session_id: str, stages: list[dict]) -> list[dict]:
        """Batch-insert stages for a session. Each dict: {stage_number, title, description, homework, status}."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        result = []
        for s in stages:
            row = await self.fetchrow(
                """INSERT INTO learning_stages (session_id, stage_number, title, description, homework, status, created_at, updated_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                   RETURNING id, stage_number, title, description, homework, status, created_at""",
                session_id,
                s["stage_number"],
                s["title"],
                s.get("description", ""),
                s.get("homework", ""),
                s.get("status", "locked"),
                now,
                now,
            )
            if row:
                row["created_at"] = row["created_at"].isoformat() if row.get("created_at") else ""
                result.append(dict(row))
        return result

    async def get_stages(self, session_id: str) -> list[dict]:
        """List all stages for a session, ordered by stage_number."""
        rows = await self.fetch(
            """SELECT id, stage_number, title, description, homework, status, created_at
               FROM learning_stages
               WHERE session_id = $1
               ORDER BY stage_number""",
            session_id,
        )
        for r in rows:
            r["created_at"] = r["created_at"].isoformat() if r.get("created_at") else ""
        return rows

    async def get_stage(self, stage_id: int) -> dict | None:
        """Get a single stage by id."""
        row = await self.fetchrow(
            """SELECT id, session_id, stage_number, title, description, homework, status, created_at
               FROM learning_stages WHERE id = $1""",
            stage_id,
        )
        if row:
            row["created_at"] = row["created_at"].isoformat() if row.get("created_at") else ""
        return row

    async def update_stage_status(self, stage_id: int, status: str):
        """Update a stage's status (e.g., 'locked' → 'active' → 'completed')."""
        await self.execute(
            "UPDATE learning_stages SET status = $1, updated_at = $2 WHERE id = $3",
            status,
            datetime.now(timezone.utc).replace(tzinfo=None),
            stage_id,
        )

    async def get_current_stage(self, session_id: str) -> dict | None:
        """Get the currently active stage (the first one with status='active')."""
        row = await self.fetchrow(
            """SELECT id, session_id, stage_number, title, description, homework, status, created_at
               FROM learning_stages
               WHERE session_id = $1 AND status = 'active'
               ORDER BY stage_number
               LIMIT 1""",
            session_id,
        )
        if row:
            row["created_at"] = row["created_at"].isoformat() if row.get("created_at") else ""
        return row

    async def delete_stages(self, session_id: str):
        """Delete all stages for a session (cascade handled by FK, but explicit)."""
        await self.execute("DELETE FROM learning_stages WHERE session_id = $1", session_id)

    async def has_stages(self, session_id: str) -> bool:
        """Check if a session already has stages generated."""
        count = await self.fetchval(
            "SELECT COUNT(*) FROM learning_stages WHERE session_id = $1",
            session_id,
        )
        return count > 0 if count else False
