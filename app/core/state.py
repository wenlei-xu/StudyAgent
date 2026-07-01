"""AgentState — the single source of truth for the entire agent graph.

Uses TypedDict + Annotated reducers per LangGraph convention:
- `messages` and `error_notebook` use list-append reducer (no overwrite)
- Other fields are overwrite-on-write
"""

from typing import Annotated, Optional, TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    thread_id: str
    learning_goal: str
    knowledge_map: dict[str, str]  # {"知识点": "已掌握"|"未掌握"|"学习中"}
    error_notebook: Annotated[list[dict], lambda left, right: (left or []) + (right or [])]
    current_phase: str  # explaining / quiz / checking / recommending
    progress: float  # 0.0 ~ 1.0
    quiz_pending: Optional[dict]  # QuizCard dict, set by quizzer, cleared by checker
    next: str  # supervisor routing target, transient
    current_stage: Optional[dict]  # {stage_number, title, description, homework, status}
    stages: Optional[list[dict]]  # Full list of stage dicts, set by stage_planner
