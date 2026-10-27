from datetime import datetime, timezone
from typing import Optional, Dict
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int

class VisionSignalResponse(BaseModel):
    face_detected: bool = Field(..., description="Whether a face was detected in the frame")
    face_count: int = Field(default=0, description="Number of faces detected")
    status: str = Field(
        default="ok",
        description="Vision status: 'ok', 'no_face', 'multiple_faces', 'poor_lighting', 'low_confidence'"
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Detection confidence score")
    lighting_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Luminance and contrast quality score")
    facial_features: Optional[Dict[str, float]] = Field(
        default=None,
        description="Derived anonymous facial geometry ratios (smile, openness, eyebrow tension)"
    )
    expression_signals: Optional[Dict[str, float]] = Field(
        default=None,
        description="Approved facial-expression signal probabilities (neutral, happy, surprised, etc.)"
    )
    bounding_box: Optional[BoundingBox] = Field(
        default=None,
        description="Coordinates of primary face bounding box for tracking"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Signal extraction timestamp"
    )

class Base64VisionPayload(BaseModel):
    image_base64: str = Field(..., description="Base64-encoded image frame bytes")
    format: Optional[str] = "image/jpeg"
