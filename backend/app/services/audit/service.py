import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.models.entities import AuditEvent

logger = logging.getLogger("ai_companion.audit")


class AuditService:
    """Security and compliance audit event service."""

    async def record_event(
        self,
        db: AsyncSession,
        event_type: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Records a security, privacy, or safety event in PostgreSQL audit table."""
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            details=details or {},
        )
        db.add(event)
        try:
            await db.commit()
            await db.refresh(event)
            logger.info(f"Audit event recorded: [{event_type}] user={user_id}")
            return event
        except Exception as exc:
            logger.error(f"Failed to record audit event [{event_type}]: {exc}")
            await db.rollback()
            return event

    async def list_events(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[AuditEvent]:
        """Lists recorded audit events."""
        query = select(AuditEvent).order_by(desc(AuditEvent.created_at)).limit(limit)
        if user_id:
            query = query.where(AuditEvent.user_id == user_id)
        if event_type:
            query = query.where(AuditEvent.event_type == event_type)

        res = await db.execute(query)
        return list(res.scalars().all())


audit_service = AuditService()
