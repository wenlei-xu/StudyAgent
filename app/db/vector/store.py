"""pgvector store — similarity search and CRUD for document chunks."""

import json
import uuid

from app.db.connection import get_pool
from app.db.vector.embedding import embed_single


async def similarity_search(
    query: str,
    top_k: int = 5,
    filter_meta: dict | None = None,
) -> list[dict]:
    """Search for chunks similar to the query using cosine distance."""
    query_vec = await embed_single(query)
    vec_str = f"[{','.join(str(v) for v in query_vec)}]"

    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, content, metadata, 1 - (embedding <=> $1::vector) AS similarity
               FROM document_chunks
               ORDER BY embedding <=> $1::vector
               LIMIT $2""",
            vec_str, top_k,
        )
    return [
        {
            "id": r["id"],
            "content": r["content"],
            "metadata": json.loads(r["metadata"]) if r["metadata"] else {},
            "similarity": r["similarity"],
        }
        for r in rows
    ]


async def insert_chunk(content: str, metadata: dict) -> str:
    """Insert a single document chunk with its embedding."""
    vec = await embed_single(content)
    vec_str = f"[{','.join(str(v) for v in vec)}]"
    chunk_id = str(uuid.uuid4())

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO document_chunks (id, content, metadata, embedding)
               VALUES ($1, $2, $3, $4::vector)""",
            chunk_id, content, json.dumps(metadata, ensure_ascii=False), vec_str,
        )
    return chunk_id


async def delete_chunks_by_source(source: str):
    """Delete all chunks from a given source document."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM document_chunks WHERE metadata->>'source' = $1",
            source,
        )
