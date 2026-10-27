import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.emotion import EmotionalState
from backend.app.services.rlpi.strategy import RLPIEngine
from backend.app.models.entities import Session, User


def test_strategy_selection_sad_empathetic_validation():
    """Verify that sad emotional state triggers empathetic_validation strategy."""
    engine = RLPIEngine()
    state = EmotionalState(
        dominant_emotion="sad",
        probabilities={"sad": 0.80, "neutral": 0.10, "happy": 0.02, "angry": 0.02, "bored": 0.02, "surprised": 0.02, "confused": 0.02},
        confidence=0.85,
        intensity=0.75,
        uncertainty=0.10,
        sources=["text"],
        modality_status={"text": True, "voice": False, "face": False},
    )

    strategy, instruction = engine.determine_strategy(state)
    assert strategy == "empathetic_validation"
    assert "gentle" in instruction.lower() or "compassionate" in instruction.lower()


def test_strategy_selection_happy_supportive_celebration():
    """Verify that happy emotional state triggers supportive_celebration strategy."""
    engine = RLPIEngine()
    state = EmotionalState(
        dominant_emotion="happy",
        probabilities={"happy": 0.85, "neutral": 0.05, "sad": 0.02, "angry": 0.02, "bored": 0.02, "surprised": 0.02, "confused": 0.02},
        confidence=0.90,
        intensity=0.80,
        uncertainty=0.08,
        sources=["text", "face"],
        modality_status={"text": True, "voice": False, "face": True},
    )

    strategy, instruction = engine.determine_strategy(state)
    assert strategy == "supportive_celebration"
    assert "joy" in instruction.lower() or "delight" in instruction.lower() or "momentum" in instruction.lower()


def test_strategy_selection_angry_calm_deescalation():
    """Verify that angry emotional state triggers calm_deescalation strategy."""
    engine = RLPIEngine()
    state = EmotionalState(
        dominant_emotion="angry",
        probabilities={"angry": 0.78, "neutral": 0.10, "happy": 0.02, "sad": 0.04, "bored": 0.02, "surprised": 0.02, "confused": 0.02},
        confidence=0.82,
        intensity=0.85,
        uncertainty=0.12,
        sources=["voice"],
        modality_status={"text": False, "voice": True, "face": False},
    )

    strategy, instruction = engine.determine_strategy(state)
    assert strategy == "calm_deescalation"
    assert "calm" in instruction.lower() or "grounded" in instruction.lower()


def test_strategy_selection_confused_structured_clarification():
    """Verify that confused emotional state triggers structured_clarification strategy."""
    engine = RLPIEngine()
    state = EmotionalState(
        dominant_emotion="confused",
        probabilities={"confused": 0.72, "neutral": 0.15, "happy": 0.02, "sad": 0.03, "angry": 0.02, "bored": 0.04, "surprised": 0.02},
        confidence=0.75,
        intensity=0.45,
        uncertainty=0.18,
        sources=["text"],
        modality_status={"text": True, "voice": False, "face": False},
    )

    strategy, instruction = engine.determine_strategy(state)
    assert strategy == "structured_clarification"
    assert "clear" in instruction.lower() or "digestible" in instruction.lower()


def test_strategy_high_uncertainty_inquisitive_attunement():
    """Verify that high uncertainty triggers inquisitive_attunement rather than an arbitrary guess."""
    engine = RLPIEngine()
    state = EmotionalState(
        dominant_emotion="happy",
        probabilities={"happy": 0.35, "sad": 0.30, "neutral": 0.20, "angry": 0.05, "bored": 0.04, "surprised": 0.04, "confused": 0.02},
        confidence=0.55,
        intensity=0.60,
        uncertainty=0.52, # High conflict/uncertainty
        sources=["text", "face"],
        modality_status={"text": True, "voice": False, "face": True},
    )

    strategy, instruction = engine.determine_strategy(state)
    assert strategy == "inquisitive_attunement"
    assert "uncertainty" in instruction.lower() or "inquisitive" in instruction.lower()


def test_system_prompt_strict_safety_and_non_diagnosis():
    """Verify that the generated system prompt strictly enforces clinical non-diagnosis boundaries."""
    engine = RLPIEngine()
    prompt = engine.build_system_prompt(
        strategy="empathetic_validation",
        strategy_instruction="Adopt a gentle tone.",
    )

    assert "NEVER diagnose mental health conditions" in prompt
    assert "NOT a physician, psychologist, or licensed therapist" in prompt
    assert "NEVER declare user emotions as clinical facts" in prompt
    assert "[EMPATHETIC_VALIDATION]" in prompt


@pytest.mark.asyncio
async def test_chat_endpoint_adapts_to_fused_emotion_state(async_client: AsyncClient, db_session: AsyncSession):
    """Verify POST /api/chat receives emotional_state and responds with matching strategy."""
    # Create test user and session
    user = User(username="rlpi_tester", email="rlpi_tester@example.com")
    db_session.add(user)
    await db_session.flush()

    sess = Session(user_id=user.id, title="RLPI Strategy Test")
    db_session.add(sess)
    await db_session.commit()

    # 1. Test Sad Emotion -> empathetic_validation
    sad_payload = {
        "message": "I feel so exhausted and nothing seems to go right lately.",
        "session_id": sess.id,
        "emotional_state": {
            "dominant_emotion": "sad",
            "probabilities": {"sad": 0.85, "neutral": 0.05, "happy": 0.02, "angry": 0.02, "bored": 0.02, "surprised": 0.02, "confused": 0.02},
            "confidence": 0.88,
            "intensity": 0.75,
            "uncertainty": 0.12,
            "sources": ["text"],
            "modality_status": {"text": True, "voice": False, "face": False},
        },
    }

    res_sad = await async_client.post("/api/chat", json=sad_payload)
    assert res_sad.status_code == 200
    data_sad = res_sad.json()

    assert data_sad["response_strategy"] == "empathetic_validation"
    assert "heavy" in data_sad["message"]["content"].lower() or "supportive" in data_sad["message"]["content"].lower()

    # 2. Test Happy Emotion -> supportive_celebration
    happy_payload = {
        "message": "We finally closed the milestone today!",
        "session_id": sess.id,
        "emotional_state": {
            "dominant_emotion": "happy",
            "probabilities": {"happy": 0.88, "neutral": 0.05, "sad": 0.01, "angry": 0.01, "bored": 0.01, "surprised": 0.02, "confused": 0.02},
            "confidence": 0.92,
            "intensity": 0.85,
            "uncertainty": 0.08,
            "sources": ["text", "voice"],
            "modality_status": {"text": True, "voice": True, "face": False},
        },
    }

    res_happy = await async_client.post("/api/chat", json=happy_payload)
    assert res_happy.status_code == 200
    data_happy = res_happy.json()

    assert data_happy["response_strategy"] == "supportive_celebration"
    assert "wonderful" in data_happy["message"]["content"].lower() or "celebrate" in data_happy["message"]["content"].lower()
