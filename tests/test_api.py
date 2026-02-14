import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_ask():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.post("/api/v1/ask", json={"query": "FastAPI websocket?"})
    assert res.status_code == 200
    body = res.json()
    assert "explanation" in body
    assert "code_example" in body
