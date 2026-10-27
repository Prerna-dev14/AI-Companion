import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.emotion import (
    TextEmotionResponse,
    VoiceEmotionResponse,
    MultimodalFusionRequest,
    EmotionalState,
)
from backend.app.schemas.vision import VisionSignalResponse
from backend.app.services.emotion.engine import emotion_engine, MultimodalEmotionEngine
from backend.app.models.entities import Session, User


@pytest.mark.asyncio
async def test_fusion_empty_modalities_fallback():
    """Verify that fusion with no active modalities falls back to neutral baseline."""
    req = MultimodalFusionRequest()
    result = await emotion_engine.fuse(req)
    
    assert result.dominant_emotion == "neutral"
    assert result.confidence == 0.50
    assert result.intensity == 0.10
    assert result.sources == []
    assert result.modality_status["text"] is False
    assert result.modality_status["voice"] is False
    assert result.modality_status["face"] is False


@pytest.mark.asyncio
async def test_fusion_text_only_happy():
    """Verify single modality (text) fusion produces expected dominant emotion and provenance."""
    text_sig = TextEmotionResponse(
        modality="text",
        intent="gratitude",
        sentiment_score=0.85,
        probabilities={
            "neutral": 0.05,
            "happy": 0.85,
            "sad": 0.01,
            "angry": 0.01,
            "bored": 0.01,
            "surprised": 0.05,
            "confused": 0.02,
        },
        confidence=0.90,
        detected_language="en",
    )
    req = MultimodalFusionRequest(text_signal=text_sig)
    result = await emotion_engine.fuse(req)

    assert result.dominant_emotion == "happy"
    assert result.sources == ["text"]
    assert result.modality_status["text"] is True
    assert result.modality_status["voice"] is False
    assert result.modality_status["face"] is False
    assert result.probabilities["happy"] > 0.70
    assert result.confidence > 0.70


@pytest.mark.asyncio
async def test_fusion_trimodal_coherent():
    """Verify trimodal fusion with coherent positive signals achieves high confidence and low uncertainty."""
    text_sig = TextEmotionResponse(
        modality="text",
        intent="emotional_venting",
        sentiment_score=0.90,
        probabilities={
            "neutral": 0.05,
            "happy": 0.85,
            "sad": 0.01,
            "angry": 0.01,
            "bored": 0.01,
            "surprised": 0.05,
            "confused": 0.02,
        },
        confidence=0.88,
        detected_language="en",
    )
    voice_sig = VoiceEmotionResponse(
        modality="voice",
        acoustic_features={
            "pitch_hz": 260.0,
            "rms_energy": 0.05,
            "tempo_estimate": 1.4,
            "spectral_brightness": 1800.0,
        },
        probabilities={
            "neutral": 0.10,
            "happy": 0.75,
            "sad": 0.02,
            "angry": 0.03,
            "bored": 0.02,
            "surprised": 0.06,
            "confused": 0.02,
        },
        confidence=0.82,
        speaking_rate="normal",
        energy_level="high",
    )
    face_sig = VisionSignalResponse(
        face_detected=True,
        face_count=1,
        status="ok",
        confidence=0.92,
        lighting_score=0.95,
        facial_features={
            "smile_ratio": 0.75,
            "eye_openness": 0.60,
        },
    )

    req = MultimodalFusionRequest(
        text_signal=text_sig,
        voice_signal=voice_sig,
        face_signal=face_sig,
    )
    result = await emotion_engine.fuse(req)

    assert result.dominant_emotion == "happy"
    assert set(result.sources) == {"text", "voice", "face"}
    assert result.modality_status["text"] is True
    assert result.modality_status["voice"] is True
    assert result.modality_status["face"] is True
    assert result.probabilities["happy"] > 0.75
    assert result.uncertainty < 0.40
    assert result.intensity > 0.50


@pytest.mark.asyncio
async def test_fusion_conflicting_modalities_elevates_uncertainty():
    """Verify that conflicting modalities (e.g. sad text vs happy face) elevate uncertainty."""
    text_sig = TextEmotionResponse(
        modality="text",
        intent="emotional_venting",
        sentiment_score=-0.80,
        probabilities={
            "neutral": 0.05,
            "happy": 0.02,
            "sad": 0.85,
            "angry": 0.02,
            "bored": 0.02,
            "surprised": 0.02,
            "confused": 0.02,
        },
        confidence=0.90,
        detected_language="en",
    )
    face_sig = VisionSignalResponse(
        face_detected=True,
        face_count=1,
        status="ok",
        confidence=0.85,
        lighting_score=0.90,
        facial_features={
            "smile_ratio": 0.80, # Smiling face
            "eye_openness": 0.60,
        },
    )

    req = MultimodalFusionRequest(
        text_signal=text_sig,
        face_signal=face_sig,
    )
    result = await emotion_engine.fuse(req)

    # Uncertainty should be elevated due to modality disagreement
    assert result.uncertainty > 0.25
    assert set(result.sources) == {"text", "face"}


@pytest.mark.asyncio
async def test_fusion_poor_lighting_degradation():
    """Verify that poor lighting status downweights face signal contribution."""
    text_sig = TextEmotionResponse(
        modality="text",
        intent="general_chat",
        sentiment_score=0.0,
        probabilities={
            "neutral": 0.80,
            "happy": 0.05,
            "sad": 0.05,
            "angry": 0.02,
            "bored": 0.03,
            "surprised": 0.03,
            "confused": 0.02,
        },
        confidence=0.85,
    )
    # Face claims happy, but lighting is very poor
    face_sig = VisionSignalResponse(
        face_detected=True,
        face_count=1,
        status="poor_lighting",
        confidence=0.50,
        lighting_score=0.20,
        facial_features={
            "smile_ratio": 0.80,
            "eye_openness": 0.50,
        },
    )

    req = MultimodalFusionRequest(
        text_signal=text_sig,
        face_signal=face_sig,
    )
    result = await emotion_engine.fuse(req)

    # Text (neutral) should heavily dominate because face weight is severely attenuated
    assert result.dominant_emotion == "neutral"
    assert result.probabilities["neutral"] > result.probabilities["happy"]


@pytest.mark.asyncio
async def test_fusion_temporal_smoothing():
    """Verify that previous_state smoothly attenuates sudden erratic spikes."""
    engine = MultimodalEmotionEngine(temporal_smoothing_alpha=0.60)
    
    prev_state = EmotionalState(
        dominant_emotion="sad",
        probabilities={
            "neutral": 0.10,
            "happy": 0.05,
            "sad": 0.75,
            "angry": 0.02,
            "bored": 0.04,
            "surprised": 0.02,
            "confused": 0.02,
        },
        confidence=0.85,
        intensity=0.70,
        uncertainty=0.15,
        sources=["text"],
        modality_status={"text": True, "voice": False, "face": False},
    )

    current_text = TextEmotionResponse(
        modality="text",
        intent="general_chat",
        sentiment_score=0.50,
        probabilities={
            "neutral": 0.20,
            "happy": 0.60,
            "sad": 0.10,
            "angry": 0.02,
            "bored": 0.03,
            "surprised": 0.03,
            "confused": 0.02,
        },
        confidence=0.80,
    )

    req = MultimodalFusionRequest(
        text_signal=current_text,
        previous_state=prev_state,
    )
    result = await engine.fuse(req)

    # Sad should not immediately drop to 0.10; it should be smoothed: 0.60 * 0.10 + 0.40 * 0.75 ≈ 0.36
    assert result.probabilities["sad"] > 0.25
    assert result.probabilities["happy"] > 0.30


@pytest.mark.asyncio
async def test_api_fusion_endpoint_with_persistence(async_client: AsyncClient, db_session: AsyncSession):
    """Verify POST /api/emotion/fuse endpoint and optional PostgreSQL persistence."""
    # Create test session
    user = User(username="fusion_tester", email="fusion_tester@example.com")
    db_session.add(user)
    await db_session.flush()

    sess = Session(user_id=user.id, title="Fusion Test Session")
    db_session.add(sess)
    await db_session.commit()

    payload = {
        "text_signal": {
            "modality": "text",
            "intent": "gratitude",
            "sentiment_score": 0.80,
            "probabilities": {
                "neutral": 0.10,
                "happy": 0.80,
                "sad": 0.02,
                "angry": 0.02,
                "bored": 0.02,
                "surprised": 0.02,
                "confused": 0.02,
            },
            "confidence": 0.85,
            "detected_language": "en",
        },
        "session_id": sess.id,
        "persist": True,
    }

    response = await async_client.post("/api/emotion/fuse", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["dominant_emotion"] == "happy"
    assert "text" in data["sources"]
    assert data["event_id"] is not None
    assert data["confidence"] > 0.70
