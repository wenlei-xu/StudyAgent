"""LangGraph event filters for SSE streaming.

Filters astream_events(v2) output down to only the events
the frontend cares about.
"""

from typing import AsyncIterator


async def filter_stream_events(events: AsyncIterator[dict]) -> AsyncIterator[dict]:
    """Pass through events used for SSE — no heavy filtering at this stage.

    The formatter layer decides which events become SSE messages.
    """
    async for event in events:
        kind = event.get("event", "")

        # Token-level streaming from chat models
        if kind == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                yield {"type": "token", "content": chunk.content}
            continue

        # Node completion
        if kind == "on_chain_end":
            node_name = event.get("name", "")
            if node_name in ("explainer", "quizzer", "check_answer", "recommender"):
                yield {"type": "done", "node": node_name}
            continue

        # Custom events dispatched by nodes (phase 2+)
        if kind == "on_custom_event":
            yield event.get("data", {})
            continue
