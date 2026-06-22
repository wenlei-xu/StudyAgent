"""Database initialization script: creates tables and enables pgvector extension."""
import asyncio
import asyncpg


async def init_db():
    conn = await asyncpg.connect(
        "postgresql://agent:agent123@localhost:5432/agent_learning"
    )
    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    print("Extensions enabled: vector, pg_trgm")
    await conn.close()
    print("Database initialization complete.")


if __name__ == "__main__":
    asyncio.run(init_db())
