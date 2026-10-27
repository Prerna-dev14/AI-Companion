import io
import wave
import math
import struct
import base64
import pytest
from httpx import AsyncClient

def generate_test_wav(freq: float = 220.0, duration: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Generates an in-memory sine wave audio bytes buffer."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        total_samples = int(sample_rate * duration)
        for i in range(total_samples):
            t = float(i) / sample_rate
            sample = int(0.5 * math.sin(2.0 * math.pi * freq * t) * 32767.0)
            wf.writeframes(struct.pack("<h", sample))
    buffer.seek(0)
    return buffer.read()

@pytest.mark.asyncio
async def test_text_emotion_positive_sentiment(async_client: AsyncClient):
    """Verify positive sentiment and happy probability derivation from text."""
    payload = {"text": "I am so happy and excited, this is wonderful and great news!"}
    response = await async_client.post("/api/emotion/text", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["modality"] == "text"
    assert data["sentiment_score"] > 0.3
    assert data["probabilities"]["happy"] > data["probabilities"]["sad"]
    assert data["intent"] in ["sharing_positive", "general_conversation"]
    assert data["confidence"] > 0.6

@pytest.mark.asyncio
async def test_text_emotion_sad_sentiment(async_client: AsyncClient):
    """Verify sad emotion and negative valence derivation from text."""
    payload = {"text": "I feel so lonely, sad, and depressed today."}
    response = await async_client.post("/api/emotion/text", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["sentiment_score"] < -0.3
    assert data["probabilities"]["sad"] > data["probabilities"]["happy"]
    assert data["intent"] == "seeking_comfort"

@pytest.mark.asyncio
async def test_text_intent_classification(async_client: AsyncClient):
    """Verify intent extraction for questions and greetings."""
    # Greeting
    resp_greet = await async_client.post("/api/emotion/text", json={"text": "Hello AI Companion!"})
    assert resp_greet.status_code == 200
    assert resp_greet.json()["intent"] == "greeting"

    # Question
    resp_q = await async_client.post("/api/emotion/text", json={"text": "How does emotional state fusion work?"})
    assert resp_q.status_code == 200
    assert resp_q.json()["intent"] == "question"

    # Gratitude
    resp_thanks = await async_client.post("/api/emotion/text", json={"text": "Thank you so much for your help!"})
    assert resp_thanks.status_code == 200
    assert resp_thanks.json()["intent"] == "gratitude"

@pytest.mark.asyncio
async def test_voice_emotion_prosody_multipart(async_client: AsyncClient):
    """Verify acoustic and prosodic feature extraction from multipart audio."""
    wav_bytes = generate_test_wav(freq=240.0, duration=0.8)
    files = {"file": ("voice_sample.wav", io.BytesIO(wav_bytes), "audio/wav")}

    response = await async_client.post("/api/emotion/voice", files=files)
    assert response.status_code == 200
    data = response.json()
    
    assert data["modality"] == "voice"
    assert "acoustic_features" in data
    assert "pitch_hz" in data["acoustic_features"]
    assert "rms_energy" in data["acoustic_features"]
    assert "probabilities" in data
    assert "speaking_rate" in data
    assert "energy_level" in data
    assert data["confidence"] > 0.0

@pytest.mark.asyncio
async def test_voice_emotion_prosody_base64(async_client: AsyncClient):
    """Verify prosody extraction from base64 audio payload."""
    wav_bytes = generate_test_wav(freq=180.0, duration=0.5)
    b64_str = base64.b64encode(wav_bytes).decode("utf-8")

    response = await async_client.post(
        "/api/emotion/voice",
        json={"audio_base64": b64_str, "filename": "sample.wav"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["modality"] == "voice"
    assert "acoustic_features" in data

@pytest.mark.asyncio
async def test_voice_emotion_empty_audio_fails_safely(async_client: AsyncClient):
    """Verify error handling on empty audio stream for prosody."""
    response = await async_client.post(
        "/api/emotion/voice",
        json={"audio_base64": ""}
    )
    assert response.status_code in [400, 422]
