from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

# --- Text Emotion Schemas ---

class TextEmotionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Input text to analyze for emotion and intent")
    language: Optional[str] = Field("en", description="Expected or detected language code")

class TextEmotionResponse(BaseModel):
    modality: str = Field(default="text", description="Modality identifier")
    intent: str = Field(..., description="Detected conversational intent")
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Valence score from -1.0 (very negative) to +1.0 (very positive)")
    probabilities: Dict[str, float] = Field(..., description="Probability distribution over emotion categories")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence of the text emotion estimation")
    detected_language: str = Field(default="en", description="Identified language code")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Signal extraction timestamp"
    )

# --- Voice Emotion / Prosody Schemas ---

class VoiceEmotionRequest(BaseModel):
    audio_base64: str = Field(..., description="Base64-encoded audio bytes for prosody analysis")
    filename: Optional[str] = "audio.wav"

class VoiceEmotionResponse(BaseModel):
    modality: str = Field(default="voice", description="Modality identifier")
    acoustic_features: Dict[str, float] = Field(
        ...,
        description="Acoustic metrics including pitch_hz, rms_energy, tempo_estimate, spectral_brightness"
    )
    probabilities: Dict[str, float] = Field(
        ...,
        description="Probability distribution over emotion categories derived from prosody"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence of the prosodic estimation")
    speaking_rate: str = Field(default="normal", description="Estimated speaking rate: 'slow', 'normal', or 'fast'")
    energy_level: str = Field(default="medium", description="Acoustic intensity level: 'low', 'medium', or 'high'")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Signal extraction timestamp"
    )

# --- Multimodal Emotion Fusion Schemas (Phase 6) ---

class EmotionalState(BaseModel):
    dominant_emotion: str = Field(
        ...,
        description="Dominant emotion category: neutral, happy, sad, angry, bored, surprised, confused"
    )
    probabilities: Dict[str, float] = Field(
        ...,
        description="Normalized probability distribution over all emotion categories"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence of the fused emotional state")
    intensity: float = Field(..., ge=0.0, le=1.0, description="Emotional intensity / arousal from 0.0 to 1.0")
    uncertainty: float = Field(..., ge=0.0, le=1.0, description="Degree of uncertainty or conflict from 0.0 to 1.0")
    sources: list[str] = Field(..., description="Active contributing modalities: ['text', 'voice', 'face']")
    modality_status: Dict[str, bool] = Field(..., description="Availability status per modality")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of the fused emotional state"
    )

class MultimodalFusionRequest(BaseModel):
    text_signal: Optional[TextEmotionResponse] = Field(None, description="NLP intent and sentiment signal")
    voice_signal: Optional[VoiceEmotionResponse] = Field(None, description="Voice acoustic prosody signal")
    face_signal: Optional[Any] = Field(None, description="Facial vision and expression signal")
    session_id: Optional[str] = Field(None, description="Associated conversation session ID")
    previous_state: Optional[EmotionalState] = Field(None, description="Prior emotional state for temporal smoothing")
    persist: bool = Field(False, description="Whether to persist the fused event to PostgreSQL")

class MultimodalFusionResponse(EmotionalState):
    event_id: Optional[str] = Field(None, description="Database event ID if persisted")

