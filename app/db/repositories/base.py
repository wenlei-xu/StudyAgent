"""Base repository with common CRUD operations."""

from typing import Any


class BaseRepository:
    def __init__(self, conn):
        self.conn = conn

    async def execute(self, query: str, *args) -> str:
        return await self.conn.execute(query, *args)

    async def fetchrow(self, query: str, *args) -> dict | None:
        row = await self.conn.fetchrow(query, *args)
        return dict(row) if row else None

    async def fetch(self, query: str, *args) -> list[dict]:
        rows = await self.conn.fetch(query, *args)
        return [dict(r) for r in rows]

    async def fetchval(self, query: str, *args) -> Any:
        return await self.conn.fetchval(query, *args)
