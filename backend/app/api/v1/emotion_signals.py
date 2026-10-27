import base64
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, status, UploadFile, File

from backend.app.schemas.emotion import (
    TextEmotionRequest,
    TextEmotionResponse,
    VoiceEmotionRequest,
    VoiceEmotionResponse,
)
from backend.app.services.emotion.nlp_signals import NLPTextSignalService
from backend.app.services.speech.prosody import VoiceProsodyService

router = APIRouter()
logger = logging.getLogger("ai_companion.api.emotion_signals")

nlp_service = NLPTextSignalService()
prosody_service = VoiceProsodyService()

@router.post(
    "/emotion/text",
    response_model=TextEmotionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract text intent and sentiment signals",
    description="Analyzes input text to determine conversational intent, sentiment score, and emotion probabilities. Modality signals remain independent."
)
async def extract_text_emotion(payload: TextEmotionRequest) -> TextEmotionResponse:
    try:
        return nlp_service.analyze(text=payload.text, language=payload.language or "en")
    except Exception as exc:
        logger.error(f"Text emotion analysis failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"NLP signal extraction failed: {str(exc)}",
        )


@router.post(
    "/emotion/voice",
    response_model=VoiceEmotionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract acoustic/prosodic voice signals",
    description="Processes audio bytes in memory to extract pitch, RMS energy, and pacing cues. Raw audio is never retained."
)
async def extract_voice_emotion(
    request: Request,
    file: Optional[UploadFile] = File(None),
) -> VoiceEmotionResponse:
    content_type = request.headers.get("content-type", "").lower()
    audio_bytes: bytes = b""
    filename = "voice.wav"

    if "multipart/form-data" in content_type:
        form = await request.form()
        uploaded = form.get("file")
        if uploaded is not None and hasattr(uploaded, "read"):
            filename = getattr(uploaded, "filename", "voice.wav")
            audio_bytes = await uploaded.read()
    elif "application/json" in content_type:
        try:
            body = await request.json()
            payload = VoiceEmotionRequest.model_validate(body)
            filename = payload.filename or "voice.wav"
            data = payload.audio_base64
            if "," in data:
                data = data.split(",")[1]
            audio_bytes = base64.b64decode(data)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid base64 audio payload: {str(exc)}",
            )
    elif content_type.startswith("audio/"):
        audio_bytes = await request.body()
    else:
        audio_bytes = await request.body()

    if not audio_bytes or len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty audio data received for prosody analysis.",
        )

    try:
        # Analyze in-memory and immediately discard raw audio
        return prosody_service.analyze_audio(audio_bytes=audio_bytes, filename=filename)
    except Exception as exc:
        logger.error(f"Voice prosody extraction failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prosody extraction failed: {str(exc)}",
        )
    finally:
        del audio_bytes
