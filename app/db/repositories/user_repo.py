"""User repository."""

import uuid

from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def create_user(self, name: str) -> dict:
        uid = str(uuid.uuid4())

        await self.execute(
            "INSERT INTO users (id, name) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            uid, name,
        )
        return {"id": uid, "name": name}

    async def get_user(self, user_id: str) -> dict | None:
        return await self.fetchrow(
            "SELECT id, name, created_at FROM users WHERE id = $1",
            user_id,
        )
