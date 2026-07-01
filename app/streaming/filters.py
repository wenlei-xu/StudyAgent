"""LangGraph event filters for SSE streaming.

Filters astream_events(v2) into structured SSE event dicts the frontend consumes.
Supervisor tokens are suppressed — only sub-agent output reaches the client.
"""

from typing import AsyncIterator


async def filter_stream_events(events: AsyncIterator[dict]) -> AsyncIterator[dict]:
    """Transform raw LangGraph astream_events into SSE-ready event dicts."""
    async for event in events:
        kind = event.get("event", "")

        if kind == "on_chat_model_stream":
            # Skip supervisor and stage_planner tokens — these are internal LLM calls
            if event.get("metadata", {}).get("langgraph_node") in ("supervisor", "stage_planner"):
                continue
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                yield {"type": "token", "content": chunk.content}
            continue

        if kind == "on_chain_end" and event.get("name") in (
            "stage_planner", "quizzer", "check_answer", "recommender"
        ):
            output = event.get("data", {}).get("output", {})
            node_name = event["name"]

            if node_name == "stage_planner":
                stages = output.get("stages")
                current_stage = output.get("current_stage")
                # Emit summary message text so it appears in the chat
                messages = output.get("messages", [])
                for m in messages:
                    if hasattr(m, "content") and m.content:
                        yield {"type": "token", "content": m.content}
                if stages:
                    yield {"type": "stages_generated", "stages": stages}
                if current_stage:
                    yield {"type": "stage_change", "current_stage": current_stage}
                yield {"type": "phase_change", "phase": "explaining", "from": "stage_planner"}

            elif node_name == "quizzer":
                quiz = output.get("quiz_pending")
                if quiz:
                    yield {"type": "quiz_card", "data": quiz}
                yield {"type": "phase_change", "phase": "quiz", "from": "supervisor"}

            elif node_name == "check_answer":
                messages = output.get("messages", [])
                feedback = ""
                for m in reversed(messages):
                    if hasattr(m, "content"):
                        feedback = m.content
                        break
                is_correct = "✅" in feedback
                explanation = feedback.replace("✅ ", "").replace("❌ ", "")
                yield {
                    "type": "check_result",
                    "correct": is_correct,
                    "explanation": explanation,
                    "correct_answer": "",
                }
                yield {"type": "phase_change", "phase": "checking", "from": "quiz"}
                progress = output.get("progress", 0)
                km = output.get("knowledge_map", {})
                yield {
                    "type": "progress_update",
                    "progress": progress,
                    "knowledge_map": km,
                }

            elif node_name == "recommender":
                yield {"type": "phase_change", "phase": "recommending", "from": "supervisor"}
