"""Test sessions REST API."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_and_list_sessions():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create
        r = await client.post("/sessions/", json={"learning_goal": "Python 异步"})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert data["learning_goal"] == "Python 异步"

        # List
        r2 = await client.get("/sessions/")
        assert r2.status_code == 200
        assert "sessions" in r2.json()


@pytest.mark.asyncio
async def test_delete_session():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/sessions/", json={"learning_goal": "test"})
        sid = r.json()["id"]

        r2 = await client.delete(f"/sessions/{sid}")
        assert r2.status_code == 200
