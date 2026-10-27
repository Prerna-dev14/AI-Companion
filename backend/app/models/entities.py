import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Text, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.base import Base, TimestampMixin

def generate_uuid() -> str:
    return str(uuid.uuid4())

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    settings: Mapped[Optional["UserSettings"]] = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    consents: Mapped[List["Consent"]] = relationship("Consent", back_populates="user", cascade="all, delete-orphan")
    memories: Mapped[List["MemoryItem"]] = relationship("MemoryItem", back_populates="user", cascade="all, delete-orphan")


class UserSettings(Base, TimestampMixin):
    __tablename__ = "user_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    voice_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    camera_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_long_term_memory: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_emotion_storage: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship("User", back_populates="settings")


class Consent(Base, TimestampMixin):
    __tablename__ = "consents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scope: Mapped[str] = mapped_column(String(64), nullable=False) # e.g. "camera", "microphone", "long_term_memory"
    granted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="consents")


class Session(Base, TimestampMixin):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="sessions")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    emotion_events: Mapped[List["EmotionEvent"]] = relationship("EmotionEvent", back_populates="session", cascade="all, delete-orphan")


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False) # 'user', 'assistant', 'system'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    session: Mapped["Session"] = relationship("Session", back_populates="messages")


class EmotionEvent(Base, TimestampMixin):
    __tablename__ = "emotion_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    
    dominant_emotion: Mapped[str] = mapped_column(String(32), nullable=False) # happy, sad, angry, bored, neutral, etc.
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    intensity: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    uncertainty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    probabilities: Mapped[Optional[Dict[str, float]]] = mapped_column(JSON, nullable=True)
    sources: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True) # ['text', 'voice', 'face']
    modality_status: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    session: Mapped["Session"] = relationship("Session", back_populates="emotion_events")
    emotion_sources: Mapped[List["EmotionSource"]] = relationship("EmotionSource", back_populates="emotion_event", cascade="all, delete-orphan")


class EmotionSource(Base, TimestampMixin):
    __tablename__ = "emotion_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    emotion_event_id: Mapped[str] = mapped_column(String(36), ForeignKey("emotion_events.id", ondelete="CASCADE"), index=True, nullable=False)
    modality: Mapped[str] = mapped_column(String(20), nullable=False) # 'text', 'voice', 'face'
    raw_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extracted_features: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    emotion_event: Mapped["EmotionEvent"] = relationship("EmotionEvent", back_populates="emotion_sources")


class MemoryItem(Base, TimestampMixin):
    __tablename__ = "memory_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="preference") # preference, context, topic
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="memories")


class AuditEvent(Base, TimestampMixin):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
