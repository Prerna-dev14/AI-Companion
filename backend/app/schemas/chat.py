from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from backend.app.schemas.emotion import EmotionalState

class MessageBase(BaseModel):
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., min_length=1, description="Message text content")

class MessageCreate(MessageBase):
    metadata_payload: Optional[Dict[str, Any]] = None

class MessageResponse(MessageBase):
    id: str
    session_id: str
    created_at: datetime
    metadata_payload: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="User message content")
    session_id: Optional[str] = Field(None, description="Existing session ID, or null to auto-create")
    user_id: Optional[str] = Field(None, description="User ID associated with request")
    emotional_state: Optional[EmotionalState] = Field(
        None,
        description="Fused normalized emotional state from Emotion Engine guiding RLPI conversational strategy",
    )

class ChatResponse(BaseModel):
    session_id: str
    message: MessageResponse
    response_strategy: str = Field(default="neutral_standard", description="Applied RLPI response strategy")
    model_name: str
    created_at: datetime

class SessionBase(BaseModel):
    title: Optional[str] = "Conversation Session"

class SessionCreate(SessionBase):
    user_id: Optional[str] = None

class SessionResponse(SessionBase):
    id: str
    user_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class SessionDetailResponse(SessionResponse):
    messages: List[MessageResponse] = []
