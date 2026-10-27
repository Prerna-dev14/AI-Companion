import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.entities import User, Session, EmotionEvent
from backend.app.services.memory.service import memory_service


@pytest.mark.asyncio
async def test_memory_creation_without_consent_fails_403(async_client: AsyncClient, db_session: AsyncSession):
    """Verify that creating memory items without consent is strictly rejected with 403 Forbidden."""
    user = User(username="no_consent_user", email="no_consent@example.com")
    db_session.add(user)
    await db_session.commit()

    payload = {
        "content": "User prefers concise answers and works as a bioinformatician.",
        "category": "preference",
        "user_id": user.id,
    }

    res = await async_client.post("/api/memory", json=payload)
    assert res.status_code == 403
    err_body = res.json()
    err_text = (err_body.get("message") or err_body.get("detail", "")).lower()
    assert "consent" in err_text


@pytest.mark.asyncio
async def test_consent_granting_and_listing(async_client: AsyncClient, db_session: AsyncSession):
    """Verify that consent can be granted and listed."""
    user = User(username="consent_user", email="consent_user@example.com")
    db_session.add(user)
    await db_session.commit()

    # Grant long-term memory consent
    update_res = await async_client.post(
        "/api/consents",
        json={"scope": "long_term_memory", "granted": True, "user_id": user.id},
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["scope"] == "long_term_memory"
    assert data["granted"] is True

    # List consents
    list_res = await async_client.get(f"/api/consents?user_id={user.id}")
    assert list_res.status_code == 200
    consents = list_res.json()
    assert any(c["scope"] == "long_term_memory" and c["granted"] for c in consents)


@pytest.mark.asyncio
async def test_memory_lifecycle_with_consent(async_client: AsyncClient, db_session: AsyncSession):
    """Verify full memory lifecycle: create, list, delete item, and clear all."""
    user = User(username="memory_lifecycle_user", email="lifecycle@example.com")
    db_session.add(user)
    await db_session.commit()

    # 1. Grant consent
    await memory_service.update_consent(
        db_session, user_id=user.id, scope="long_term_memory", granted=True
    )

    # 2. Create memory item
    payload = {
        "content": "Favorite programming language is Python and Rust.",
        "category": "preference",
        "user_id": user.id,
    }
    create_res = await async_client.post("/api/memory", json=payload)
    assert create_res.status_code == 201
    mem_data = create_res.json()
    mem_id = mem_data["id"]
    assert mem_data["content"] == payload["content"]

    # 3. List memories
    list_res = await async_client.get(f"/api/memory?user_id={user.id}")
    assert list_res.status_code == 200
    memories = list_res.json()
    assert len(memories) >= 1
    assert any(m["id"] == mem_id for m in memories)

    # 4. Delete specific item
    del_res = await async_client.delete(f"/api/memory/{mem_id}?user_id={user.id}")
    assert del_res.status_code == 200

    # Verify deleted
    list_after_del = await async_client.get(f"/api/memory?user_id={user.id}")
    assert not any(m["id"] == mem_id for m in list_after_del.json())

    # 5. Add two items and clear all (Right to be Forgotten)
    await async_client.post("/api/memory", json={"content": "Item A", "user_id": user.id})
    await async_client.post("/api/memory", json={"content": "Item B", "user_id": user.id})

    clear_res = await async_client.delete(f"/api/memory?user_id={user.id}")
    assert clear_res.status_code == 200
    assert clear_res.json()["cleared_count"] >= 2

    empty_res = await async_client.get(f"/api/memory?user_id={user.id}")
    assert len(empty_res.json()) == 0


@pytest.mark.asyncio
async def test_emotion_history_query_and_clear(async_client: AsyncClient, db_session: AsyncSession):
    """Verify emotion history retrieval and clearing endpoints."""
    user = User(username="emotion_history_user", email="eh@example.com")
    db_session.add(user)
    await db_session.flush()

    sess = Session(user_id=user.id, title="Emotion History Session")
    db_session.add(sess)
    await db_session.flush()

    # Create logged emotion event
    event = EmotionEvent(
        session_id=sess.id,
        dominant_emotion="happy",
        confidence=0.88,
        intensity=0.70,
        uncertainty=0.10,
        sources=["text", "face"],
    )
    db_session.add(event)
    await db_session.commit()

    # Query history
    res = await async_client.get(f"/api/emotion/history?session_id={sess.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert data["items"][0]["dominant_emotion"] == "happy"

    # Clear history
    clear_res = await async_client.delete(f"/api/emotion/history?session_id={sess.id}")
    assert clear_res.status_code == 200

    # Verify cleared
    res_after = await async_client.get(f"/api/emotion/history?session_id={sess.id}")
    assert res_after.json()["total"] == 0
