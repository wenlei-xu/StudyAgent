"""Knowledge notes API — CRUD + text search + auto-summarize."""

import json

from fastapi import APIRouter, HTTPException
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.db.connection import get_connection, release_connection
from app.db.repositories.knowledge_note_repo import KnowledgeNoteRepository

router = APIRouter()
# Cross-session endpoint (mounted at /notes in main.py)
notes_router = APIRouter()

SUMMARIZE_PROMPT = """你是一个知识提炼助手。分析以下对话，提取用户学到的核心知识点。

每条笔记格式要求：
- topic: 简洁的知识点名称（如 "Python闭包", "HTTP状态码"）
- content: 详细的笔记内容，包含关键概念和例子
- tags: 标签数组，便于分类检索（如 ["Python", "函数式编程"]）

输出要求：
- 从对话中提取 1-3 条知识点
- 如果对话中没有实质性的教学内容，返回空数组
- 使用 JSON 数组格式，不要包含其他文字
- 每条笔记必须包含 topic, content, tags 三个字段"""


def _parse_json_array(raw: str) -> list | None:
    """Extract JSON array from LLM output, handling ```json blocks."""
    if "```json" in raw:
        start = raw.index("```json") + 7
        end = raw.index("```", start)
        raw = raw[start:end].strip()
    elif "```" in raw:
        start = raw.index("```") + 3
        end = raw.index("```", start)
        raw = raw[start:end].strip()
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "notes" in data:
            return data["notes"]
        return data if isinstance(data, list) else None
    except (json.JSONDecodeError, ValueError):
        return None


@router.get("/{session_id}/notes")
async def list_notes(
    session_id: str,
    tag: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """List knowledge notes for a session, optionally filtered by tag."""
    conn = await get_connection()
    try:
        repo = KnowledgeNoteRepository(conn)
        notes = await repo.list_notes(
            session_id=session_id, tag=tag, limit=limit, offset=offset
        )
        return {"notes": notes}
    finally:
        await release_connection(conn)


@notes_router.get("/notes")
async def list_all_notes(
    tag: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """List all knowledge notes across sessions, with session names."""
    conn = await get_connection()
    try:
        repo = KnowledgeNoteRepository(conn)
        notes = await repo.list_notes(
            session_id=None, tag=tag, limit=limit, offset=offset
        )
        return {"notes": notes}
    finally:
        await release_connection(conn)


@router.get("/{session_id}/notes/search")
async def search_notes(session_id: str, q: str = ""):
    """Search knowledge notes by topic or content text."""
    if not q.strip():
        return {"notes": []}
    conn = await get_connection()
    try:
        repo = KnowledgeNoteRepository(conn)
        notes = await repo.search_notes(query=q.strip(), session_id=session_id)
        return {"notes": notes}
    finally:
        await release_connection(conn)


@router.post("/{session_id}/notes")
async def create_note(session_id: str, body: dict):
    """Manually create a knowledge note."""
    topic = (body.get("topic") or "").strip()
    content = (body.get("content") or "").strip()
    if not topic or not content:
        raise HTTPException(status_code=400, detail="topic 和 content 不能为空")
    conn = await get_connection()
    try:
        repo = KnowledgeNoteRepository(conn)
        note = await repo.create_note(
            session_id=session_id,
            topic=topic[:200],
            content=content,
            tags=body.get("tags") or [],
            source_type=body.get("source_type", "manual"),
        )
        return note
    finally:
        await release_connection(conn)


@router.put("/{session_id}/notes/{note_id}")
async def update_note(session_id: str, note_id: str, body: dict):
    """Update a knowledge note's topic, content, or tags."""
    conn = await get_connection()
    try:
        repo = KnowledgeNoteRepository(conn)
        existing = await repo.get_note(note_id)
        if not existing or existing["session_id"] != session_id:
            raise HTTPException(status_code=404, detail="笔记不存在")
        note = await repo.update_note(
            note_id=note_id,
            topic=body.get("topic"),
            content=body.get("content"),
            tags=body.get("tags"),
        )
        return note
    finally:
        await release_connection(conn)


@router.delete("/{session_id}/notes/{note_id}")
async def delete_note(session_id: str, note_id: str):
    """Delete a knowledge note."""
    conn = await get_connection()
    try:
        repo = KnowledgeNoteRepository(conn)
        existing = await repo.get_note(note_id)
        if not existing or existing["session_id"] != session_id:
            raise HTTPException(status_code=404, detail="笔记不存在")
        await repo.delete_note(note_id)
        return {"ok": True}
    finally:
        await release_connection(conn)


@router.get("/{session_id}/notes/tags")
async def list_tags(session_id: str):
    """Get all unique tags for a session."""
    conn = await get_connection()
    try:
        repo = KnowledgeNoteRepository(conn)
        tags = await repo.get_all_tags(session_id=session_id)
        return {"tags": tags}
    finally:
        await release_connection(conn)


@router.get("/{session_id}/notes/graph")
async def get_knowledge_graph(session_id: str):
    """Get nodes and edges for a session's knowledge graph."""
    conn = await get_connection()
    try:
        repo = KnowledgeNoteRepository(conn)
        data = await repo.get_graph_data(session_id=session_id)
        return data
    finally:
        await release_connection(conn)


@notes_router.get("/notes/graph")
async def get_all_knowledge_graph():
    """Get nodes and edges for all sessions' knowledge graph."""
    conn = await get_connection()
    try:
        repo = KnowledgeNoteRepository(conn)
        data = await repo.get_graph_data(session_id=None)
        return data
    finally:
        await release_connection(conn)


@router.post("/{session_id}/notes/auto-summarize")
async def auto_summarize_notes(session_id: str, body: dict | None = None):
    """Extract knowledge notes from the latest AI teaching interaction.

    Accepts optional body.ai_message to avoid relying on LangGraph checkpoint API.
    Falls back to empty if no message provided.
    """
    last_exchange = (body or {}).get("ai_message", "").strip()
    if not last_exchange or len(last_exchange) < 50:
        return {"notes": []}

    model = ChatOpenAI(
        model=settings.supervisor_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=0.3,
        timeout=15,
        max_retries=1,
    )

    try:
        response = await model.ainvoke([
            SystemMessage(content=SUMMARIZE_PROMPT),
            HumanMessage(content=f"请从以下对话中提炼知识点：\n\n{last_exchange[:4000]}"),
        ])
        extracted = _parse_json_array(response.content.strip())
        if not extracted:
            return {"notes": []}
    except Exception:
        return {"notes": []}

    conn = await get_connection()
    try:
        repo = KnowledgeNoteRepository(conn)
        saved = []
        for item in extracted:
            topic = (item.get("topic") or "").strip()
            content = (item.get("content") or "").strip()
            if not topic or not content:
                continue
            note = await repo.create_note(
                session_id=session_id,
                topic=topic[:200],
                content=content,
                tags=(item.get("tags") or [])[:5],
                source_type="auto",
            )
            saved.append(note)
        return {"notes": saved}
    finally:
        await release_connection(conn)
