"""Knowledge note repository — CRUD and text search for distilled learning notes."""

import uuid
from datetime import datetime, timezone

from app.db.repositories.base import BaseRepository


class KnowledgeNoteRepository(BaseRepository):
    async def create_note(
        self,
        session_id: str,
        topic: str,
        content: str,
        tags: list[str] | None = None,
        source_type: str = "auto",
    ) -> dict:
        note_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.execute(
            """INSERT INTO knowledge_notes (id, session_id, topic, content, tags, source_type, created_at, updated_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            note_id, session_id, topic, content, tags or [], source_type, now, now,
        )
        return {
            "id": note_id,
            "session_id": session_id,
            "topic": topic,
            "content": content,
            "tags": tags or [],
            "source_type": source_type,
            "created_at": now.isoformat(),
        }

    async def get_note(self, note_id: str) -> dict | None:
        row = await self.fetchrow(
            "SELECT * FROM knowledge_notes WHERE id = $1",
            note_id,
        )
        if row:
            row["tags"] = list(row["tags"]) if row.get("tags") else []
        return row

    async def list_notes(
        self,
        session_id: str | None = None,
        tag: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """List notes. If session_id is None, returns notes across all sessions with session_goal."""
        if session_id:
            return await self._list_by_session(session_id, tag, limit, offset)
        return await self._list_all_with_session(tag, limit, offset)

    async def _list_by_session(
        self, session_id: str, tag: str | None, limit: int, offset: int
    ) -> list[dict]:
        conditions = ["kn.session_id = $1"]
        params = [session_id]
        idx = 2

        if tag:
            conditions.append(f"${idx} = ANY(kn.tags)")
            params.append(tag)
            idx += 1

        rows = await self.fetch(
            f"""SELECT kn.*, s.learning_goal AS session_name
                FROM knowledge_notes kn
                LEFT JOIN sessions s ON s.id = kn.session_id
                WHERE {' AND '.join(conditions)}
                ORDER BY kn.created_at DESC LIMIT ${idx} OFFSET ${idx + 1}""",
            *params, limit, offset,
        )
        for r in rows:
            r["tags"] = list(r["tags"]) if r.get("tags") else []
        return rows

    async def _list_all_with_session(
        self, tag: str | None, limit: int, offset: int
    ) -> list[dict]:
        conditions = []
        params = []
        idx = 1

        if tag:
            conditions.append(f"${idx} = ANY(kn.tags)")
            params.append(tag)
            idx += 1

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        rows = await self.fetch(
            f"""SELECT kn.*, s.learning_goal AS session_name
                FROM knowledge_notes kn
                LEFT JOIN sessions s ON s.id = kn.session_id
                {where}
                ORDER BY kn.created_at DESC LIMIT ${idx} OFFSET ${idx + 1}""",
            *params, limit, offset,
        )
        for r in rows:
            r["tags"] = list(r["tags"]) if r.get("tags") else []
        return rows

    async def search_notes(
        self,
        query: str,
        session_id: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Full-text search across topic and content using pg_trgm ILIKE."""
        conditions = ["(topic ILIKE $1 OR content ILIKE $1)"]
        params = [f"%{query}%"]

        if session_id:
            conditions.append(f"session_id = ${len(params) + 1}")
            params.append(session_id)

        rows = await self.fetch(
            f"SELECT * FROM knowledge_notes WHERE {' AND '.join(conditions)} ORDER BY created_at DESC LIMIT ${len(params) + 1}",
            *params, limit,
        )
        for r in rows:
            r["tags"] = list(r["tags"]) if r.get("tags") else []
        return rows

    async def update_note(self, note_id: str, topic: str | None = None, content: str | None = None, tags: list[str] | None = None) -> dict | None:
        sets = []
        params = []
        idx = 1

        if topic is not None:
            sets.append(f"topic = ${idx}")
            params.append(topic)
            idx += 1
        if content is not None:
            sets.append(f"content = ${idx}")
            params.append(content)
            idx += 1
        if tags is not None:
            sets.append(f"tags = ${idx}")
            params.append(tags)
            idx += 1

        if not sets:
            return await self.get_note(note_id)

        sets.append(f"updated_at = ${idx}")
        params.append(datetime.now(timezone.utc).replace(tzinfo=None))
        idx += 1

        params.append(note_id)
        await self.execute(
            f"UPDATE knowledge_notes SET {', '.join(sets)} WHERE id = ${idx}",
            *params,
        )
        return await self.get_note(note_id)

    async def delete_note(self, note_id: str) -> bool:
        r = await self.execute("DELETE FROM knowledge_notes WHERE id = $1", note_id)
        return r == "DELETE 1"

    async def get_all_tags(self, session_id: str | None = None) -> list[str]:
        if session_id:
            rows = await self.fetch(
                "SELECT DISTINCT unnest(tags) AS tag FROM knowledge_notes WHERE session_id = $1 ORDER BY tag",
                session_id,
            )
        else:
            rows = await self.fetch(
                "SELECT DISTINCT unnest(tags) AS tag FROM knowledge_notes ORDER BY tag",
            )
        return [r["tag"] for r in rows]

    async def get_graph_data(self, session_id: str | None = None) -> dict:
        """Return nodes and edges for knowledge graph visualization.

        Nodes = topics. Edges = shared tags between topics.
        When knowledge_points exist for matching topics, sets mastery_status.
        """
        notes = await self.list_notes(session_id=session_id, limit=500)

        # ── Fetch knowledge point statuses ──
        CN_TO_EN = {"已掌握": "mastered", "学习中": "learning", "未掌握": "unfamiliar"}
        STATUS_RANK = {"mastered": 3, "learning": 2, "unfamiliar": 1}
        kp_map: dict[str, str] = {}  # topic_lower -> status (English)

        if session_id:
            kp_rows = await self.fetch(
                "SELECT name, status FROM knowledge_points WHERE session_id = $1",
                session_id,
            )
            for r in kp_rows:
                kp_map[r["name"].strip().lower()] = CN_TO_EN.get(r["status"], r["status"])
        else:
            kp_rows = await self.fetch(
                "SELECT name, status FROM knowledge_points"
            )
            for r in kp_rows:
                key = r["name"].strip().lower()
                cur_rank = STATUS_RANK.get(kp_map.get(key), 0)
                new_rank = STATUS_RANK.get(CN_TO_EN.get(r["status"]), 0)
                if new_rank > cur_rank:
                    kp_map[key] = CN_TO_EN.get(r["status"])

        # ── Build nodes ──
        nodes = []
        edges = []
        seen_topics = {}

        for note in notes:
            key = note["topic"].strip().lower()
            if key not in seen_topics:
                mastery = kp_map.get(key)
                seen_topics[key] = {
                    "id": note["id"],
                    "name": note["topic"],
                    "symbolSize": 30,
                    "category": note["source_type"],
                    "mastery_status": mastery,
                }
                nodes.append(seen_topics[key])

        # Build edges: if two topics share a tag, draw a connection
        topic_tags = {n["id"]: set() for n in nodes}
        for note in notes:
            tid = seen_topics.get(note["topic"].strip().lower(), {}).get("id")
            if tid:
                topic_tags[tid].update(note.get("tags") or [])

        node_ids = list(topic_tags.keys())
        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                shared = topic_tags[node_ids[i]] & topic_tags[node_ids[j]]
                if shared:
                    edges.append({
                        "source": node_ids[i],
                        "target": node_ids[j],
                        "label": ", ".join(list(shared)[:3]),
                    })

        return {"nodes": nodes, "edges": edges}
