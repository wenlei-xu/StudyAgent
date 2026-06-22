"""Knowledge map read/write tool for agents."""

from langchain_core.tools import tool


@tool
def get_knowledge_status(knowledge_point: str, knowledge_map: dict) -> str:
    """Get the mastery status of a knowledge point.

    Args:
        knowledge_point: The name of the knowledge point.
        knowledge_map: The current knowledge map dict.

    Returns:
        Status: mastered / learning / unfamiliar / unknown
    """
    return knowledge_map.get(knowledge_point, "unknown")


@tool
def list_weak_points(knowledge_map: dict) -> list[str]:
    """List all knowledge points that are not yet mastered.

    Args:
        knowledge_map: The current knowledge map dict.

    Returns:
        List of weak knowledge point names.
    """
    return [k for k, v in knowledge_map.items() if v != "已掌握"]
