import io
import base64
import cv2
import numpy as np
import pytest
from httpx import AsyncClient

def generate_test_image(draw_face: bool = True, dark: bool = False) -> bytes:
    """Generates an in-memory test image with or without simple face geometry."""
    img = np.zeros((240, 320, 3), dtype=np.uint8)
    if not dark:
        img.fill(160)  # Neutral background

    if draw_face and not dark:
        # Draw face oval
        cv2.ellipse(img, (160, 120), (50, 70), 0, 0, 360, (230, 200, 180), -1)
        # Draw eyes
        cv2.circle(img, (140, 105), 8, (40, 40, 40), -1)
        cv2.circle(img, (180, 105), 8, (40, 40, 40), -1)
        # Draw mouth/smile
        cv2.ellipse(img, (160, 145), (20, 10), 0, 0, 180, (50, 50, 200), 3)

    _, buffer = cv2.imencode(".jpg", img)
    return buffer.tobytes()

@pytest.mark.asyncio
async def test_vision_no_face_detection(async_client: AsyncClient):
    """Verify POST /api/emotion/face handles frame without a face."""
    blank_jpg = generate_test_image(draw_face=False)
    files = {"file": ("blank.jpg", io.BytesIO(blank_jpg), "image/jpeg")}

    response = await async_client.post("/api/emotion/face", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["face_detected"] is False
    assert data["face_count"] == 0
    assert data["status"] in ["no_face", "poor_lighting", "ok"]
    assert "lighting_score" in data
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_vision_poor_lighting_case(async_client: AsyncClient):
    """Verify poor lighting detection on very dark frames."""
    dark_jpg = generate_test_image(draw_face=False, dark=True)
    files = {"file": ("dark.jpg", io.BytesIO(dark_jpg), "image/jpeg")}

    response = await async_client.post("/api/emotion/face", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["face_detected"] is False
    assert data["lighting_score"] < 0.5
    assert data["status"] in ["poor_lighting", "no_face"]

@pytest.mark.asyncio
async def test_vision_base64_payload(async_client: AsyncClient):
    """Verify POST /api/emotion/face handles base64 image frames."""
    test_jpg = generate_test_image(draw_face=True)
    b64_str = base64.b64encode(test_jpg).decode("utf-8")

    response = await async_client.post(
        "/api/emotion/face",
        json={"image_base64": b64_str, "format": "image/jpeg"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "face_detected" in data
    assert "lighting_score" in data
    assert "confidence" in data
    assert "status" in data

@pytest.mark.asyncio
async def test_vision_empty_payload_error(async_client: AsyncClient):
    """Verify 400 Bad Request on empty image payload."""
    response = await async_client.post(
        "/api/emotion/face",
        json={"image_base64": ""}
    )
    assert response.status_code in [400, 422]
