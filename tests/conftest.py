"""pytest fixtures — test database, mock LLM, test graph."""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_llm_response():
    """Mock LLM that returns a fixed response."""
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value=MagicMock(content="这是一个模拟的 LLM 回答。"))
    return mock


@pytest.fixture
def mock_graph():
    """Mock LangGraph that returns a fixed state."""
    mock = MagicMock()
    mock.ainvoke = AsyncMock(
        return_value={
            "messages": [MagicMock(content="Echo 测试", type="ai")],
            "current_phase": "explaining",
        }
    )
    mock.astream_events = AsyncMock(return_value=__import__("asyncio").Queue().__aiter__())
    return mock


@pytest.fixture
def sample_state():
    return {
        "messages": [],
        "thread_id": "test-thread-001",
        "learning_goal": "掌握 Python 异步编程",
        "knowledge_map": {"async/await": "学习中", "事件循环": "未掌握"},
        "error_notebook": [],
        "current_phase": "explaining",
        "progress": 0.3,
        "quiz_pending": None,
        "next": "explainer",
    }
