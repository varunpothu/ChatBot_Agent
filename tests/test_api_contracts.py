from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_config_exposes_runtime_contract():
    response = client.get("/config")
    assert response.status_code == 200
    body = response.json()
    assert "runtime_backend" in body
    assert "ingestion_mode" in body
    assert "distributed_cache" in body


def test_languages_exposes_auto_detect_and_capabilities():
    response = client.get("/languages")
    assert response.status_code == 200
    codes = {item["code"] for item in response.json()}
    assert "auto" in codes
    assert "en-GB" in codes
    assert "hi-IN" in codes


def test_chat_without_knowledge_abstains():
    response = client.post("/chat", json={
        "message": "What is the course fee?",
        "language": "en-GB",
    })
    assert response.status_code == 200
    body = response.json()
    assert body["abstained"] is True
    assert body["next_action"] == "human_review"
