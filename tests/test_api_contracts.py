import httpx
import pytest

from apps.api.main import app


@pytest.mark.asyncio
async def test_config_exposes_runtime_contract():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/config")
    assert response.status_code == 200
    body = response.json()
    assert "runtime_backend" in body
    assert "ingestion_mode" in body
    assert "distributed_cache" in body


@pytest.mark.asyncio
async def test_languages_exposes_auto_detect_and_capabilities():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/languages")
    assert response.status_code == 200
    codes = {item["code"] for item in response.json()}
    assert "auto" in codes
    assert "en-GB" in codes
    assert "hi-IN" in codes


@pytest.mark.asyncio
async def test_chat_requires_upstream_identity_in_production(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "api_gateway")
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/chat",
                json={"message": "What is the course fee?"},
            )
        assert response.status_code == 401
    finally:
        monkeypatch.setenv("AUTH_MODE", "development")


@pytest.mark.asyncio
async def test_document_upload_requires_admin_key():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/documents/upload",
            files={"file": ("notes.txt", b"hello", "text/plain")},
        )
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_chat_without_knowledge_abstains():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/chat",
            json={
                "message": "What is the course fee?",
                "language": "en-GB",
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["abstained"] is True
    assert body["next_action"] == "human_review"
