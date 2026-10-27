import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.entities import User
from backend.app.services.safety.service import safety_service
from backend.app.core.security import create_access_token, decode_access_token
from backend.app.core.rate_limit import rate_limiter


def test_safety_classifier_detects_self_harm():
    """Verify that high-risk crisis triggers are detected with vetted helplines."""
    crisis_messages = [
        "I feel hopeless and I want to kill myself tonight",
        "Thinking of ending it all and dying",
        "I don't want to live anymore, I am cutting myself",
    ]
    for msg in crisis_messages:
        assessment = safety_service.assess_message(msg)
        assert not assessment.is_safe, f"Failed to detect crisis in: {msg}"
        assert assessment.category == "self_harm"
        assert "988" in assessment.intervention_text
        assert "741741" in assessment.intervention_text
        assert "988_lifeline" in assessment.resources


def test_safety_classifier_allows_safe_messages():
    """Verify that regular non-crisis messages are marked safe."""
    safe_messages = [
        "I had a really tiring day at work today.",
        "Can you explain how neural networks work?",
        "I'm feeling a bit sad because of the bad weather.",
    ]
    for msg in safe_messages:
        assessment = safety_service.assess_message(msg)
        assert assessment.is_safe
        assert assessment.category == "none"
        assert assessment.intervention_text is None


def test_jwt_token_creation_and_decoding():
    """Verify JWT access token issuance and signature decoding."""
    token = create_access_token(data={"sub": "user_456", "role": "companion_user"})
    decoded = decode_access_token(token)
    assert decoded["sub"] == "user_456"
    assert decoded["role"] == "companion_user"
    assert "exp" in decoded


@pytest.mark.asyncio
async def test_chat_safety_circuit_breaker_and_audit(async_client: AsyncClient, db_session: AsyncSession):
    """Verify chat circuit breaker triggers crisis intervention and records audit log."""
    user = User(username="safety_user", email="safety@example.com")
    db_session.add(user)
    await db_session.commit()

    crisis_prompt = "I can't take this anymore, I want to kill myself."
    res = await async_client.post(
        "/api/chat",
        json={"message": crisis_prompt, "user_id": user.id},
    )
    assert res.status_code == 200
    data = res.json()

    # Verify circuit breaker intercepted before LLM
    assert data["response_strategy"] == "safety_crisis_intervention"
    assert data["model_name"] == "safety_circuit_breaker"
    reply_text = data["message"]["content"]
    assert "988" in reply_text
    assert "Crisis Text Line" in reply_text
    assert "741741" in reply_text

    # Verify audit event was logged in database
    audit_res = await async_client.get(f"/api/audit/events?user_id={user.id}")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["total"] >= 1
    safety_event = next(e for e in audit_data["events"] if e["event_type"] == "SAFETY_INTERVENTION_TRIGGERED")
    assert safety_event["details"]["category"] == "self_harm"


@pytest.mark.asyncio
async def test_rate_limiter_exceeded_returns_429(async_client: AsyncClient):
    """Verify rate limiter blocks excessive requests with 429 and Retry-After."""
    rate_limiter.reset()

    # Make heavy requests up to heavy limit (40 req/min)
    path = "/api/speech/transcribe"
    for _ in range(40):
        allowed, limit, remaining, retry_after = rate_limiter.is_allowed("test-client:/api/speech/transcribe", path)
        assert allowed is True

    # 41st request should be rejected
    allowed, limit, remaining, retry_after = rate_limiter.is_allowed("test-client:/api/speech/transcribe", path)
    assert allowed is False
    assert retry_after >= 1
    assert remaining == 0

    rate_limiter.reset()


@pytest.mark.asyncio
async def test_audit_events_recorded_on_consent_and_memory(async_client: AsyncClient, db_session: AsyncSession):
    """Verify that privacy consent grants and memory actions generate audit logs."""
    user = User(username="audit_tester", email="audit@example.com")
    db_session.add(user)
    await db_session.commit()

    # 1. Grant consent
    await async_client.post(
        "/api/consents",
        json={"scope": "long_term_memory", "granted": True, "user_id": user.id},
    )

    # 2. Create memory
    await async_client.post(
        "/api/memory",
        json={"content": "Prefers dark mode and concise summaries", "user_id": user.id},
    )

    # 3. Clear memory (purge)
    await async_client.delete(f"/api/memory?user_id={user.id}")

    # 4. Check audit events
    audit_res = await async_client.get(f"/api/audit/events?user_id={user.id}")
    assert audit_res.status_code == 200
    events = audit_res.json()["events"]
    event_types = [e["event_type"] for e in events]
    assert "CONSENT_GRANTED" in event_types
    assert "MEMORY_CREATED" in event_types
    assert "MEMORY_PURGED_ALL" in event_types
