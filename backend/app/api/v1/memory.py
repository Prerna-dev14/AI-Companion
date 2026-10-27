import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db
from backend.app.schemas.memory import (
    MemoryItemCreate,
    MemoryItemResponse,
    ConsentUpdate,
    ConsentResponse,
    EmotionHistoryResponse,
    EmotionEventItem,
)
from backend.app.services.memory.service import memory_service
from backend.app.services.conversation.manager import ConversationManager

router = APIRouter()
logger = logging.getLogger("ai_companion.api.memory")
conv_manager = ConversationManager()


@router.get(
    "/memory",
    response_model=List[MemoryItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List stored user memories",
    description="Returns all active long-term memory items for the user. Requires active consent."
)
async def list_memories(
    user_id: Optional[str] = Query(None, description="User ID"),
    db: AsyncSession = Depends(get_db),
) -> List[MemoryItemResponse]:
    user = await conv_manager.get_or_create_default_user(db, user_id=user_id)
    memories = await memory_service.list_memories(db, user_id=user.id)
    return [MemoryItemResponse.model_validate(m) for m in memories]


@router.post(
    "/memory",
    response_model=MemoryItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create long-term memory item",
    description="Stores a persistent user preference or fact. Strictly consent-gated (returns 403 if consent is revoked)."
)
async def create_memory(
    payload: MemoryItemCreate,
    db: AsyncSession = Depends(get_db),
) -> MemoryItemResponse:
    user = await conv_manager.get_or_create_default_user(db, user_id=payload.user_id)
    try:
        memory = await memory_service.create_memory(
            db=db,
            user_id=user.id,
            content=payload.content,
            category=payload.category,
        )
        return MemoryItemResponse.model_validate(memory)
    except PermissionError as p_err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(p_err),
        )
    except Exception as exc:
        logger.error(f"Failed to create memory item: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist memory item.",
        )


@router.delete(
    "/memory/{memory_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete specific memory item",
    description="Permanently removes a specific memory item."
)
async def delete_memory_item(
    memory_id: str,
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    user = await conv_manager.get_or_create_default_user(db, user_id=user_id)
    deleted = await memory_service.delete_memory(db, user_id=user.id, memory_id=memory_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory item {memory_id} not found.",
        )
    return {"status": "ok", "deleted_id": memory_id}


@router.delete(
    "/memory",
    status_code=status.HTTP_200_OK,
    summary="Clear all user memories",
    description="Right to be Forgotten: Permanently deletes all long-term memory items for the user."
)
async def clear_all_memories(
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    user = await conv_manager.get_or_create_default_user(db, user_id=user_id)
    count = await memory_service.clear_all_memories(db, user_id=user.id)
    return {"status": "ok", "cleared_count": count}


# --- Consent Endpoints ---

@router.get(
    "/consents",
    response_model=List[ConsentResponse],
    status_code=status.HTTP_200_OK,
    summary="List active consent scopes",
    description="Returns user consent permissions for long-term memory, emotion storage, camera, and microphone."
)
async def list_user_consents(
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> List[ConsentResponse]:
    user = await conv_manager.get_or_create_default_user(db, user_id=user_id)
    consents = await memory_service.list_consents(db, user_id=user.id)
    return [ConsentResponse.model_validate(c) for c in consents]


@router.post(
    "/consents",
    response_model=ConsentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update consent permission",
    description="Grants or revokes permission for a specific scope ('long_term_memory', 'emotion_storage', etc.)."
)
async def update_user_consent(
    payload: ConsentUpdate,
    db: AsyncSession = Depends(get_db),
) -> ConsentResponse:
    user = await conv_manager.get_or_create_default_user(db, user_id=payload.user_id)
    consent = await memory_service.update_consent(
        db=db,
        user_id=user.id,
        scope=payload.scope,
        granted=payload.granted,
    )
    return ConsentResponse.model_validate(consent)


# --- Emotion Event History Endpoints ---

@router.get(
    "/emotion/history",
    response_model=EmotionHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query emotion event history",
    description="Retrieves chronological emotion events for the active session or user."
)
async def get_emotion_history(
    session_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> EmotionHistoryResponse:
    total, items = await memory_service.get_emotion_history(
        db=db,
        session_id=session_id,
        user_id=user_id,
        limit=limit,
    )
    return EmotionHistoryResponse(
        total=total,
        items=[EmotionEventItem.model_validate(it) for it in items],
    )


@router.delete(
    "/emotion/history",
    status_code=status.HTTP_200_OK,
    summary="Clear emotion event history",
    description="Purges logged emotion events."
)
async def clear_emotion_history(
    session_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    count = await memory_service.clear_emotion_history(
        db=db,
        session_id=session_id,
        user_id=user_id,
    )
    return {"status": "ok", "cleared_events": count}
