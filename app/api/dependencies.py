"""FastAPI dependencies — inject DB sessions, graph instance, etc."""

from app.core.graph.builder import get_graph


async def get_graph_dependency():
    """Inject the compiled LangGraph graph singleton."""
    return get_graph()
