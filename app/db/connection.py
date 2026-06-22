"""Database connection pool management using asyncpg."""

import asyncpg
from app.config import settings

_pool: asyncpg.Pool | None = None


def _to_asyncpg_dsn(url: str) -> str:
    """Convert SQLAlchemy DSN (postgresql+asyncpg://...) to asyncpg DSN (postgresql://...)."""
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=_to_asyncpg_dsn(settings.database_url),
            min_size=2,
            max_size=10,
            command_timeout=30,
        )
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_connection() -> asyncpg.Connection:
    pool = await get_pool()
    return await pool.acquire()


async def release_connection(conn: asyncpg.Connection):
    pool = await get_pool()
    await pool.release(conn)
