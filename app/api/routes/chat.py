"""POST /chat/{session_id}/stream — Core SSE streaming endpoint.

Uses LangGraph astream_events for real-time LLM token streaming.
"""

import asyncio
import json

from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage
from starlette.responses import StreamingResponse

from app.api.dependencies import get_graph_dependency
from app.models.chat import ChatRequest

router = APIRouter()


@router.post("/{session_id}/stream")
async def chat_stream(
    session_id: str,
    body: ChatRequest,
    graph=Depends(get_graph_dependency),
):
    """Stream agent response as SSE events using LangGraph astream_events."""
    config = {"configurable": {"thread_id": session_id}}
    input_state = {"messages": [HumanMessage(content=body.message)]}

    async def event_generator():
        try:
            async for event in graph.astream_events(input_state, config, version="v2"):
                kind = event.get("event", "")

                # LLM token streaming
                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk.content}, ensure_ascii=False)}\n\n"
                    continue

                # Node completion → check state changes for structured outputs
                if kind == "on_chain_end" and event.get("name") in (
                    "quizzer", "check_answer", "recommender"
                ):
                    # The state after this node contains structured outputs
                    # We dispatch custom events based on the updated state
                    output = event.get("data", {}).get("output", {})
                    node_name = event["name"]

                    if node_name == "quizzer":
                        quiz = output.get("quiz_pending")
                        if quiz:
                            yield f"data: {json.dumps({'type': 'quiz_card', 'data': quiz}, ensure_ascii=False)}\n\n"
                        yield f"data: {json.dumps({'type': 'phase_change', 'phase': 'quiz', 'from': 'supervisor'}, ensure_ascii=False)}\n\n"

                    elif node_name == "check_answer":
                        messages = output.get("messages", [])
                        feedback = ""
                        for m in reversed(messages):
                            if hasattr(m, "content"):
                                feedback = m.content
                                break
                        is_correct = "✅" in feedback
                        explanation = feedback.replace("✅ ", "").replace("❌ ", "")
                        yield f"data: {json.dumps({'type': 'check_result', 'correct': is_correct, 'explanation': explanation, 'correct_answer': ''}, ensure_ascii=False)}\n\n"
                        yield f"data: {json.dumps({'type': 'phase_change', 'phase': 'checking', 'from': 'quiz'}, ensure_ascii=False)}\n\n"

                        # Progress update
                        progress = output.get("progress", 0)
                        km = output.get("knowledge_map", {})
                        yield f"data: {json.dumps({'type': 'progress_update', 'progress': progress, 'knowledge_map': km}, ensure_ascii=False)}\n\n"

                    elif node_name == "recommender":
                        yield f"data: {json.dumps({'type': 'phase_change', 'phase': 'recommending', 'from': 'supervisor'}, ensure_ascii=False)}\n\n"

            yield "data: {\"type\": \"done\"}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'code': 'INTERNAL', 'detail': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
