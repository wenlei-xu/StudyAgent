"""POST /chat/{session_id}/stream — Core SSE streaming endpoint.
GET /chat/{session_id}/history — Read persisted messages from checkpoint.
"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request
from langchain_core.messages import HumanMessage
from starlette.responses import StreamingResponse

from app.api.dependencies import get_graph_dependency
from app.db.connection import get_connection, release_connection
from app.db.repositories.stage_repo import StageRepository
from app.models.chat import ChatRequest
from app.streaming.filters import filter_stream_events
from app.streaming.formatters import format_sse

router = APIRouter()

_ROLE_MAP = {
    "human": "user",
    "ai": "ai",
    "system": "system",
}


@router.get("/{session_id}/history")
async def get_chat_history(
    session_id: str,
    graph=Depends(get_graph_dependency),
):
    """Return messages + state for a session_id from checkpoints."""
    config = {"configurable": {"thread_id": session_id}}
    try:
        snapshot = await graph.aget_state(config)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read checkpoint")

    if not snapshot or not snapshot.values:
        return {"messages": [], "knowledge_map": {}, "progress": 0}

    values = snapshot.values
    messages = values.get("messages", []) or []

    result = []
    for i, m in enumerate(messages):
        role = _ROLE_MAP.get(getattr(m, "type", ""), "user")
        content = getattr(m, "content", "") or ""
        result.append({
            "id": f"hist-{session_id[:8]}-{i}",
            "role": role,
            "content": content,
        })

    return {
        "messages": result,
        "knowledge_map": values.get("knowledge_map", {}),
        "progress": values.get("progress", 0),
    }


@router.post("/{session_id}/stream")
async def chat_stream(
    session_id: str,
    body: ChatRequest,
    request: Request,
    graph=Depends(get_graph_dependency),
):
    # Load current stage info so the supervisor can be stage-aware
    current_stage = None
    stages = None
    conn = await get_connection()
    try:
        stage_repo = StageRepository(conn)
        current_stage = await stage_repo.get_current_stage(session_id)
        if current_stage is None:
            # Check if stages exist at all (might be all completed)
            all_stages = await stage_repo.get_stages(session_id)
            if all_stages:
                stages = all_stages
    except Exception:
        pass  # Table might not exist yet — graceful degradation
    finally:
        await release_connection(conn)

    config = {"configurable": {"thread_id": session_id, "model": body.model}, "recursion_limit": 50}
    input_state = {
        "messages": [HumanMessage(content=body.message)],
        "current_stage": current_stage,
        "stages": stages,
        "thread_id": session_id,
        "learning_goal": "",  # Will be set by stage_planner or from DB
    }

    async def event_generator():
        buffer: list[dict] = []
        done = asyncio.Event()

        async def collect_events():
            try:
                filtered = filter_stream_events(
                    graph.astream_events(input_state, config, version="v2")
                )
                async for event in filtered:
                    if done.is_set():
                        return
                    buffer.append(event)
                buffer.append({"type": "done"})
            except asyncio.CancelledError:
                pass

        task = asyncio.create_task(collect_events())

        try:
            cursor = 0
            while True:
                if await request.is_disconnected():
                    done.set()
                    task.cancel()
                    break

                while cursor < len(buffer):
                    yield format_sse(buffer[cursor])
                    cursor += 1
                    if buffer[cursor - 1].get("type") == "done":
                        return

                if task.done():
                    if task.exception():
                        error = task.exception()
                        yield format_sse({"type": "error", "code": "INTERNAL", "detail": str(error)})
                    break

                await asyncio.sleep(0.05)

        except Exception as e:
            done.set()
            task.cancel()
            yield format_sse({"type": "error", "code": "INTERNAL", "detail": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
