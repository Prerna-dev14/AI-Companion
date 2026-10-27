from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.sessions import router as sessions_router
from backend.app.api.v1.speech import router as speech_router
from backend.app.api.v1.vision import router as vision_router
from backend.app.api.v1.emotion_signals import router as emotion_signals_router
from backend.app.api.v1.memory import router as memory_router
from backend.app.api.v1.audit import router as audit_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, tags=["Health"])
api_v1_router.include_router(chat_router, tags=["Conversation"])
api_v1_router.include_router(sessions_router, tags=["Sessions"])
api_v1_router.include_router(speech_router, tags=["Speech AI"])
api_v1_router.include_router(vision_router, tags=["Vision Signals"])
api_v1_router.include_router(emotion_signals_router, tags=["Emotion Signals"])
api_v1_router.include_router(memory_router, tags=["Memory & Consent"])
api_v1_router.include_router(audit_router, tags=["Security & Audit"])

__all__ = [
    "api_v1_router",
    "chat_router",
    "sessions_router",
    "speech_router",
    "vision_router",
    "emotion_signals_router",
    "memory_router",
    "audit_router",
]
