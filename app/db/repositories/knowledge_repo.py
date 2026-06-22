"""Knowledge point repository."""

from app.db.repositories.base import BaseRepository


class KnowledgeRepository(BaseRepository):
    async def upsert_knowledge_point(
        self, session_id: str, name: str, status: str
    ):
        await self.execute(
            """INSERT INTO knowledge_points (session_id, name, status)
               VALUES ($1, $2, $3)
               ON CONFLICT (session_id, name) DO UPDATE SET status = $3, updated_at = NOW()""",
            session_id, name, status,
        )

    async def get_knowledge_map(self, session_id: str) -> dict[str, str]:
        rows = await self.fetch(
            "SELECT name, status FROM knowledge_points WHERE session_id = $1",
            session_id,
        )
        return {r["name"]: r["status"] for r in rows}

    async def bulk_upsert(self, session_id: str, knowledge_map: dict[str, str]):
        for name, status in knowledge_map.items():
            await self.upsert_knowledge_point(session_id, name, status)
