"""SSE formatter — encodes internal event dicts into SSE byte strings.

Format: "data: {json}\n\n"
"""

import json


def format_sse(event: dict) -> bytes:
    """Encode a single event dict as an SSE frame."""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode("utf-8")


def format_done() -> bytes:
    """Send the [DONE] sentinel some frontends expect."""
    return b"data: [DONE]\n\n"
