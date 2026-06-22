"""Test Supervisor routing decisions."""

import pytest

from app.core.graph.supervisor import VALID_TARGETS


def test_valid_targets():
    """Only specific targets are allowed from the supervisor."""
    assert "explainer" in VALID_TARGETS
    assert "quizzer" in VALID_TARGETS
    assert "check_answer" in VALID_TARGETS
    assert "recommender" in VALID_TARGETS
    assert "FINISH" in VALID_TARGETS
    assert "unknown_node" not in VALID_TARGETS
    assert len(VALID_TARGETS) == 5
