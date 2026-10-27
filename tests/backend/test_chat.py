import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_chat_creates_session_and_responds(async_client: AsyncClient):
    """Verify POST /api/chat auto-creates session and generates valid response."""
    payload = {"message": "Hello AI Companion!"}
    response = await async_client.post("/api/chat", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "session_id" in data
    assert data["session_id"] is not None
    assert "message" in data
    assert data["message"]["role"] == "assistant"
    assert len(data["message"]["content"]) > 0
    assert "response_strategy" in data
    assert "model_name" in data
    # Ensure server-side secrets/prompts are not exposed in content
    assert "API_KEY" not in data["message"]["content"]
    assert "System:" not in data["message"]["content"]

@pytest.mark.asyncio
async def test_chat_multi_turn_conversation(async_client: AsyncClient):
    """Verify context preservation across multiple chat turns in the same session."""
    # Turn 1
    resp1 = await async_client.post("/api/chat", json={"message": "I am feeling happy today."})
    assert resp1.status_code == 200
    session_id = resp1.json()["session_id"]

    # Turn 2 in same session
    resp2 = await async_client.post(
        "/api/chat",
        json={"message": "Can you remember what I just said?", "session_id": session_id}
    )
    assert resp2.status_code == 200
    assert resp2.json()["session_id"] == session_id

    # Check session message history endpoint
    history_resp = await async_client.get(f"/api/sessions/{session_id}/messages")
    assert history_resp.status_code == 200
    messages = history_resp.json()
    assert len(messages) >= 4  # 2 user messages + 2 assistant replies

@pytest.mark.asyncio
async def test_chat_validation_error_on_empty_message(async_client: AsyncClient):
    """Verify 422 error is returned on invalid/empty message."""
    response = await async_client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "VALIDATION_ERROR"

@pytest.mark.asyncio
async def test_session_lifecycle_endpoints(async_client: AsyncClient):
    """Verify GET and POST /api/sessions lifecycle."""
    # Create session
    create_resp = await async_client.post("/api/sessions", json={"title": "Test Chat Session"})
    assert create_resp.status_code == 201
    created_session = create_resp.json()
    assert created_session["title"] == "Test Chat Session"

    # List sessions
    list_resp = await async_client.get("/api/sessions")
    assert list_resp.status_code == 200
    sessions = list_resp.json()
    assert any(s["id"] == created_session["id"] for s in sessions)
