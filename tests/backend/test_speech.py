import io
import base64
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_speech_synthesis_contract(async_client: AsyncClient):
    """Verify POST /api/speech/synthesize produces valid audio payload."""
    payload = {
        "text": "Hello, I am your AI Companion. This is speech synthesis verification.",
        "language": "en",
        "voice": "default",
    }
    response = await async_client.post("/api/speech/synthesize", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/")
    assert len(response.content) > 100  # Generated valid audio stream

@pytest.mark.asyncio
async def test_speech_transcription_multipart(async_client: AsyncClient):
    """Verify POST /api/speech/transcribe handles multipart audio input."""
    # Create sample in-memory audio bytes
    audio_content = b"RIFF....WAVEfmt ....data....mock_text:Hello from audio test"
    files = {"file": ("test_speech.wav", io.BytesIO(audio_content), "audio/wav")}

    response = await async_client.post("/api/speech/transcribe", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert len(data["text"]) > 0
    assert "language" in data

@pytest.mark.asyncio
async def test_speech_transcription_base64(async_client: AsyncClient):
    """Verify POST /api/speech/transcribe handles base64 audio payload."""
    raw_bytes = b"RIFF....WAVEfmt ....data....mock_text:Testing base64 audio upload"
    b64_str = base64.b64encode(raw_bytes).decode("utf-8")

    response = await async_client.post(
        "/api/speech/transcribe",
        json={"audio_base64": b64_str, "filename": "sample.wav"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert len(data["text"]) > 0

@pytest.mark.asyncio
async def test_speech_transcription_empty_audio_fails_safely(async_client: AsyncClient):
    """Verify error handling on empty audio stream."""
    response = await async_client.post(
        "/api/speech/transcribe",
        json={"audio_base64": ""}
    )
    assert response.status_code in [400, 422]
