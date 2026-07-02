"""Note Taker node — silently extracts knowledge notes from the last teaching exchange.

Runs after explainer, never modifies phase or adds visible messages.
Persists notes to the knowledge_notes table via KnowledgeNoteRepository.
"""

import json
import logging

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from app.core.state import AgentState
from app.config import settings
from app.db.connection import get_pool
from app.db.repositories.knowledge_note_repo import KnowledgeNoteRepository
from app.db.repositories.knowledge_repo import KnowledgeRepository

logger = logging.getLogger(__name__)

SUMMARIZE_PROMPT = """你是一个知识提炼助手。分析以下教学对话，提取学生学到的核心知识点。

每条笔记格式要求：
- topic: 简洁的知识点名称（如 "Python闭包", "HTTP状态码"）
- content: 详细的笔记内容，包含关键概念和例子
- tags: 标签数组，便于分类检索（如 ["Python", "函数式编程"]）
- mastery: 学生对知识点的掌握程度，从对话中的提问方式、回答正确率、理解深度判断
  - "mastered": 学生能正确回答、举一反三、深入讨论细节
  - "learning": 学生有一定了解但回答不完整、需要提示
  - "unfamiliar": 学生刚开始接触、提问基础问题、表现出困惑

输出要求：
- 从对话中提取 1-3 条知识点
- 如果对话中没有实质性的教学内容，返回空数组
- 使用 JSON 数组格式，不要包含其他文字
- 每条笔记必须包含 topic, content, tags, mastery 四个字段"""


async def note_taker_node(state: AgentState, config: RunnableConfig) -> dict:
    """Extract and persist knowledge notes from the last teaching exchange."""
    session_id = config.get("configurable", {}).get("thread_id", "")
    if not session_id:
        return {}

    messages = state.get("messages", [])
    if not messages:
        return {}

    # Build last exchange: user question + AI answer
    human_msgs = []
    ai_msgs = []
    for m in messages:
        t = getattr(m, "type", "")
        c = getattr(m, "content", "")
        if t == "human":
            human_msgs.append(c)
        elif t == "ai":
            ai_msgs.append(c)

    # Check if note_taker was directly invoked by user ("帮我记个笔记") vs chained after teaching
    # When last message is from user, show confirmation; when after AI teaching, stay silent
    last_msg_type = getattr(messages[-1], "type", "") if messages else ""
    was_directly_invoked = (last_msg_type == "human")

    if not ai_msgs:
        return {}

    last_exchange = ""
    if human_msgs and ai_msgs:
        # When directly invoked, pair last AI response with its original question
        user_msg = human_msgs[-2] if was_directly_invoked and len(human_msgs) >= 2 else human_msgs[-1]
        last_exchange = f"用户: {user_msg}\n\nAI: {ai_msgs[-1]}"
    else:
        last_exchange = ai_msgs[-1]

    if len(last_exchange) < 50:
        return {}

    # Call LLM to extract notes
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
        raw = response.content.strip()

        # Parse JSON array
        if "```json" in raw:
            start = raw.index("```json") + 7
            end = raw.index("```", start)
            raw = raw[start:end].strip()
        elif "```" in raw:
            start = raw.index("```") + 3
            end = raw.index("```", start)
            raw = raw[start:end].strip()

        extracted = json.loads(raw)
        if isinstance(extracted, dict) and "notes" in extracted:
            extracted = extracted["notes"]
        if not isinstance(extracted, list):
            return {}
    except Exception:
        return {}

    # Persist notes silently and confirm
    pool = await get_pool()
    async with pool.acquire() as conn:
        repo = KnowledgeNoteRepository(conn)
        kp_repo = KnowledgeRepository(conn)
        saved_count = 0
        for item in extracted:
            topic = (item.get("topic") or "").strip()
            content = (item.get("content") or "").strip()
            if not topic or not content:
                continue
            try:
                await repo.create_note(
                    session_id=session_id,
                    topic=topic[:200],
                    content=content,
                    tags=(item.get("tags") or [])[:5],
                    source_type="auto",
                )
                # Also persist mastery to knowledge_points
                mastery_en = item.get("mastery", "learning")
                cn_status = {"mastered": "已掌握", "learning": "学习中", "unfamiliar": "未掌握"}.get(mastery_en, "学习中")
                await kp_repo.upsert_knowledge_point(session_id, topic[:200], cn_status)
                saved_count += 1
            except Exception:
                logger.exception("Failed to persist knowledge note")

    if saved_count > 0 and was_directly_invoked:
        return {"messages": [AIMessage(content=f"📝 已记录 {saved_count} 条知识笔记")]}
    return {}
