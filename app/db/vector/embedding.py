"""Embedding model wrapper using OpenAI text-embedding-3-small."""

from openai import AsyncOpenAI

from app.config import settings

_client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)


async def embed(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts into vectors."""
    response = await _client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    return [d.embedding for d in response.data]


async def embed_single(text: str) -> list[float]:
    """Embed a single text."""
    results = await embed([text])
    return results[0]
