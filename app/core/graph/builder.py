"""LangGraph builder — constructs and compiles the full agent graph with supervisor routing."""

from langgraph.graph import StateGraph, END

from app.core.state import AgentState
from app.core.graph.supervisor import supervisor_node
from app.core.graph.nodes.explainer import explainer_node
from app.core.graph.nodes.quizzer import quizzer_node
from app.core.graph.nodes.check_answer import check_answer_node
from app.core.graph.nodes.recommender import recommender_node
from app.core.graph.nodes.stage_planner import stage_planner_node
from app.core.graph.nodes.note_taker import note_taker_node


def _route_from_supervisor(state: AgentState) -> str:
    """Conditional edge: supervisor's 'next' field determines target node."""
    return state.get("next", "explainer")


def build_graph(checkpointer=None):
    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("stage_planner", stage_planner_node)
    graph.add_node("explainer", explainer_node)
    graph.add_node("quizzer", quizzer_node)
    graph.add_node("check_answer", check_answer_node)
    graph.add_node("recommender", recommender_node)
    graph.add_node("note_taker", note_taker_node)

    # Entry → supervisor
    graph.set_entry_point("supervisor")

    # Supervisor → conditional routing to sub-nodes or END
    graph.add_conditional_edges(
        "supervisor",
        _route_from_supervisor,
        {
            "stage_planner": "stage_planner",
            "explainer": "explainer",
            "quizzer": "quizzer",
            "check_answer": "check_answer",
            "recommender": "recommender",
            "note_taker": "note_taker",
            "__end__": END,
        },
    )

    # Teaching/content nodes → note_taker → END: silently save knowledge notes
    graph.add_edge("explainer", "note_taker")
    graph.add_edge("quizzer", "note_taker")
    graph.add_edge("recommender", "note_taker")
    graph.add_edge("check_answer", "note_taker")
    graph.add_edge("note_taker", END)
    # stage_planner → END: wait for user's next message to continue
    graph.add_edge("stage_planner", END)

    return graph.compile(checkpointer=checkpointer)


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
