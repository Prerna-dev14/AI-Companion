from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.chat import router as chat_router
from backend.app.api.v1.sessions import router as sessions_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, tags=["Health"])
api_v1_router.include_router(chat_router, tags=["Conversation"])
api_v1_router.include_router(sessions_router, tags=["Sessions"])

__all__ = ["api_v1_router", "chat_router", "sessions_router"]
