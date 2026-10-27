import base64
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, status

from backend.app.schemas.vision import VisionSignalResponse, Base64VisionPayload
from backend.app.services.vision.adapters import get_vision_adapter

router = APIRouter()
logger = logging.getLogger("ai_companion.api.vision")

@router.post(
    "/emotion/face",
    response_model=VisionSignalResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract visual & facial expression signals",
    description="Processes an image frame in memory to detect face presence, lighting, and anonymous expression cues. Raw frames are never retained."
)
async def extract_facial_signals(request: Request) -> VisionSignalResponse:
    content_type = request.headers.get("content-type", "").lower()
    image_bytes: bytes = b""

    if "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_file = form.get("file")
        if uploaded_file is not None and hasattr(uploaded_file, "read"):
            image_bytes = await uploaded_file.read()
    elif "application/json" in content_type:
        try:
            body = await request.json()
            payload = Base64VisionPayload.model_validate(body)
            data = payload.image_base64
            if "," in data:
                data = data.split(",")[1]
            image_bytes = base64.b64decode(data)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid base64 image payload: {str(exc)}",
            )
    elif content_type.startswith("image/"):
        image_bytes = await request.body()
    else:
        # Fallback body read
        image_bytes = await request.body()

    if not image_bytes or len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty image data received.",
        )

    try:
        adapter = get_vision_adapter()
        result = await adapter.analyze_frame(image_bytes=image_bytes)
        return result
    except Exception as exc:
        logger.error(f"Facial signal estimation failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vision analysis error: {str(exc)}",
        )
    finally:
        # Guarantee zero retention
        del image_bytes
