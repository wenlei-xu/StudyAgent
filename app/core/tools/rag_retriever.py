"""RAG retriever tool — wraps pgvector similarity search for LangGraph agents."""

from langchain_core.tools import tool

from app.db.vector.store import similarity_search


@tool
async def rag_retriever(query: str) -> str:
    """Search the local knowledge base for relevant learning materials.

    Args:
        query: The search query, ideally a specific question or concept.

    Returns:
        Formatted text with the top matching document chunks.
    """
    results = await similarity_search(query, top_k=3)

    if not results:
        return "（知识库中未找到相关内容）"

    formatted = []
    for i, r in enumerate(results, 1):
        formatted.append(f"【资料 {i}】（相似度: {r['similarity']:.2f}）\n{r['content']}")

    return "\n\n".join(formatted)
