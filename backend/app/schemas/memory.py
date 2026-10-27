from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class MemoryItemCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="Memory content / user preference fact")
    category: str = Field(default="preference", description="Memory category: 'preference', 'topic', 'context'")
    user_id: Optional[str] = None

class MemoryItemResponse(BaseModel):
    id: str
    user_id: str
    content: str
    category: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class ConsentUpdate(BaseModel):
    scope: str = Field(..., description="Consent scope: 'long_term_memory', 'emotion_storage', 'camera', 'microphone'")
    granted: bool = Field(..., description="Whether consent is granted or revoked")
    user_id: Optional[str] = None

class ConsentResponse(BaseModel):
    id: str
    user_id: str
    scope: str
    granted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class EmotionEventItem(BaseModel):
    id: str
    session_id: str
    dominant_emotion: str
    confidence: float
    intensity: float
    uncertainty: float
    sources: Optional[List[str]] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class EmotionHistoryResponse(BaseModel):
    total: int
    items: List[EmotionEventItem]
