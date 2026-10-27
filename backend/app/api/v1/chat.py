import logging
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.conversation.manager import ConversationManager

router = APIRouter()
logger = logging.getLogger("ai_companion.api.chat")
conversation_manager = ConversationManager()

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send chat message",
    description="Processes text conversation, persists message history, and generates AI Companion response via RLPI layer."
)
async def send_chat_message(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    try:
        response = await conversation_manager.process_chat(
            db=db,
            message_text=payload.message,
            session_id=payload.session_id,
            user_id=payload.user_id,
        )
        return response
    except Exception as exc:
        logger.exception(f"Error handling chat message: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate conversation response",
        )
