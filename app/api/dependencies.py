"""FastAPI dependencies — inject DB sessions, graph instance, etc."""

from fastapi import Request


async def get_graph_dependency(request: Request):
    """Inject the compiled LangGraph graph singleton (with PostgresSaver)."""
    return request.app.state.graph
