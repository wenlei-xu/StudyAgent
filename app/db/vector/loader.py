"""Document loader pipeline: PDF → chunks → embeddings → pgvector."""

import uuid
from pathlib import Path

import pymupdf
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.db.vector.store import insert_chunk, delete_chunks_by_source


async def load_pdf(file_path: str, source_name: str | None = None) -> int:
    """Load a PDF, chunk it, embed chunks, and store in pgvector.

    Returns the number of chunks inserted.
    """
    path = Path(file_path)
    if source_name is None:
        source_name = path.name

    # Clear old chunks for this source
    await delete_chunks_by_source(source_name)

    # Extract text
    doc = pymupdf.open(file_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " "],
    )
    chunks = splitter.split_text(full_text)

    # Embed and insert each chunk
    count = 0
    for i, chunk in enumerate(chunks):
        await insert_chunk(
            content=chunk,
            metadata={
                "source": source_name,
                "chunk_index": i,
                "total_chunks": len(chunks),
            },
        )
        count += 1

    return count


async def load_text(text: str, source_name: str, metadata: dict | None = None) -> int:
    """Load raw text, chunk it, embed, and store."""
    await delete_chunks_by_source(source_name)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " "],
    )
    chunks = splitter.split_text(text)

    base_meta = metadata or {}
    base_meta["source"] = source_name

    for i, chunk in enumerate(chunks):
        await insert_chunk(
            content=chunk,
            metadata={**base_meta, "chunk_index": i, "total_chunks": len(chunks)},
        )

    return len(chunks)
