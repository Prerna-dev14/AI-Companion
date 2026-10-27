import base64
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, status, Response
from pydantic import BaseModel

from backend.app.schemas.speech import TranscriptionResponse, SynthesisRequest
from backend.app.services.speech.adapters import get_stt_adapter, get_tts_adapter

router = APIRouter()
logger = logging.getLogger("ai_companion.api.speech")

class Base64AudioPayload(BaseModel):
    audio_base64: str
    filename: Optional[str] = "audio.wav"

@router.post(
    "/speech/transcribe",
    response_model=TranscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Transcribe audio to text",
    description="Processes audio stream in memory and converts spoken voice to text. Raw audio is never stored."
)
async def transcribe_speech(request: Request) -> TranscriptionResponse:
    content_type = request.headers.get("content-type", "").lower()
    audio_bytes: bytes = b""
    filename = "audio.wav"

    if "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_file = form.get("file")
        if uploaded_file is not None and hasattr(uploaded_file, "read"):
            filename = getattr(uploaded_file, "filename", "audio.wav")
            audio_bytes = await uploaded_file.read()
    elif "application/json" in content_type:
        try:
            body = await request.json()
            payload = Base64AudioPayload.model_validate(body)
            filename = payload.filename or "audio.wav"
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
        filename = "recording.wav" if "wav" in content_type else "recording.webm"
        audio_bytes = await request.body()
    else:
        # Fallback body read
        audio_bytes = await request.body()

    if not audio_bytes or len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty audio data received.",
        )

    try:
        stt_adapter = get_stt_adapter()
        # In-memory transcription; raw audio is discarded immediately
        result = await stt_adapter.transcribe(audio_bytes=audio_bytes, filename=filename)
        return TranscriptionResponse(
            text=result.get("text", ""),
            language=result.get("language", "en"),
            duration_sec=result.get("duration_sec"),
        )
    except Exception as exc:
        logger.error(f"Speech transcription failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech transcription failed: {str(exc)}",
        )
    finally:
        # Explicit garbage collection reference removal for privacy
        del audio_bytes


@router.post(
    "/speech/synthesize",
    summary="Synthesize text to speech",
    description="Converts text to spoken audio. Returns audio stream (audio/mpeg or audio/wav) directly."
)
async def synthesize_speech(
    payload: SynthesisRequest,
):
    try:
        tts_adapter = get_tts_adapter()
        audio_bytes, mime_type = await tts_adapter.synthesize(
            text=payload.text,
            language=payload.language or "en",
            voice=payload.voice,
        )

        return Response(
            content=audio_bytes,
            media_type=mime_type,
            headers={
                "Content-Disposition": 'inline; filename="synthesized_speech.mp3"',
                "Cache-Control": "no-cache",
            },
        )
    except Exception as exc:
        logger.error(f"Text-to-speech synthesis failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speech synthesis error: {str(exc)}",
        )
