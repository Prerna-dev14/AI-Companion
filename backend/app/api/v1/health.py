import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.database.session import get_db, engine
from backend.app.schemas.health import HealthResponse, DatabaseStatus

router = APIRouter()
logger = logging.getLogger("ai_companion.health")

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health and Readiness Check",
    description="Returns service health status, runtime configuration, and database connectivity."
)
async def check_health(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    db_connected = False
    details = None
    dialect = engine.dialect.name

    try:
        # Check DB connectivity
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            db_connected = True
            details = "Connection healthy"
    except Exception as exc:
        logger.warning(f"Database health check failed: {str(exc)}")
        db_connected = False
        details = str(exc)

    return HealthResponse(
        status="ok" if db_connected else "degraded",
        app_name=settings.APP_NAME,
        version=settings.VERSION,
        environment=settings.APP_ENV,
        database=DatabaseStatus(
            connected=db_connected,
            dialect=dialect,
            details=details,
        ),
        services={
            "conversation": "ready",
            "emotion_engine": "ready",
            "speech": "standby",
            "vision": "standby",
            "memory": "ready",
        }
    )
