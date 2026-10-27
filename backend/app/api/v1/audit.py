import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db
from backend.app.schemas.audit import AuditEventResponse, AuditEventListResponse
from backend.app.services.audit.service import audit_service
from backend.app.core.security import get_optional_current_user_id

router = APIRouter()
logger = logging.getLogger("ai_companion.api.audit")


@router.get(
    "/audit/events",
    response_model=AuditEventListResponse,
    status_code=status.HTTP_200_OK,
    summary="List security and compliance audit events",
)
async def list_audit_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    auth_user_id: Optional[str] = Depends(get_optional_current_user_id),
) -> AuditEventListResponse:
    effective_user = user_id or auth_user_id
    events = await audit_service.list_events(
        db=db,
        user_id=effective_user,
        event_type=event_type,
        limit=limit,
    )
    return AuditEventListResponse(
        events=[AuditEventResponse.model_validate(e) for e in events],
        total=len(events),
    )
