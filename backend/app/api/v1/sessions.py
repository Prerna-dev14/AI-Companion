from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db
from backend.app.schemas.chat import SessionCreate, SessionResponse, MessageResponse
from backend.app.services.conversation.manager import ConversationManager

router = APIRouter()
conversation_manager = ConversationManager()

@router.get(
    "/sessions",
    response_model=List[SessionResponse],
    status_code=status.HTTP_200_OK,
    summary="List conversation sessions",
)
async def list_sessions(
    db: AsyncSession = Depends(get_db),
) -> List[SessionResponse]:
    sessions = await conversation_manager.get_sessions(db)
    return [SessionResponse.model_validate(s) for s in sessions]

@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new conversation session",
)
async def create_session(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    session = await conversation_manager.get_or_create_session(
        db,
        user_id=payload.user_id,
        title=payload.title,
    )
    return SessionResponse.model_validate(session)

@router.get(
    "/sessions/{session_id}/messages",
    response_model=List[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Get messages for a conversation session",
)
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[MessageResponse]:
    messages = await conversation_manager.get_session_messages(db, session_id=session_id)
    return [MessageResponse.model_validate(m) for m in messages]
