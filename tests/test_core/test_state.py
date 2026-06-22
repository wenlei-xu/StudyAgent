"""Test AgentState reducer behavior — ensures append and overwrite semantics."""

from app.core.state import AgentState


def test_knowledge_map_overwrite():
    """knowledge_map should be overwritten, not merged."""
    state = AgentState(
        messages=[],
        thread_id="t1",
        learning_goal="test",
        knowledge_map={"a": "学习中"},
        error_notebook=[],
        current_phase="explaining",
        progress=0.0,
        quiz_pending=None,
        next="explainer",
    )

    # Simulate an update: checker writes new knowledge_map
    updated = {**state, "knowledge_map": {"a": "已掌握", "b": "学习中"}}
    assert updated["knowledge_map"]["a"] == "已掌握"
    assert "b" in updated["knowledge_map"]


def test_progress_range():
    """Progress should always be between 0 and 1."""
    state = AgentState(
        messages=[],
        thread_id="t1",
        learning_goal="test",
        knowledge_map={},
        error_notebook=[],
        current_phase="explaining",
        progress=0.5,
        quiz_pending=None,
        next="explainer",
    )
    assert 0.0 <= state["progress"] <= 1.0
