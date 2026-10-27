from typing import Optional
from pydantic import BaseModel, Field

class TranscriptionResponse(BaseModel):
    text: str = Field(..., description="Transcribed text content")
    language: str = Field(default="en", description="Detected language code")
    duration_sec: Optional[float] = Field(None, description="Audio duration in seconds")

class SynthesisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize into speech")
    voice: Optional[str] = Field("default", description="Voice profile identifier")
    language: Optional[str] = Field("en", description="Language code")

class SynthesisResponse(BaseModel):
    audio_base64: str = Field(..., description="Base64-encoded audio bytes")
    format: str = Field(default="audio/mpeg", description="MIME format of the audio")
    duration_sec: Optional[float] = Field(None, description="Audio duration in seconds")
