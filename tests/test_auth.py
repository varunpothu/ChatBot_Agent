import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app


@pytest.mark.asyncio
async def test_oidc_mode_requires_bearer_token(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "oidc")
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/chat",
                json={"message": "What is the course fee?"},
            )
        assert response.status_code == 401
    finally:
        monkeypatch.setenv("AUTH_MODE", "development")


def test_development_mode_uses_local_principal(monkeypatch):
    from security.auth import require_principal
    from starlette.requests import Request

    monkeypatch.setenv("AUTH_MODE", "development")
    request = Request(
        {
            "type": "http",
            "headers": [
                (b"x-coachai-user-id", b"test-user"),
                (b"x-coachai-role", b"student"),
            ],
        }
    )
    principal = require_principal(request)
    assert principal.user_id == "test-user"
    assert principal.role == "student"
