from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class DatabaseStatus(BaseModel):
    connected: bool
    dialect: str
    details: Optional[str] = None

class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Overall system health status")
    app_name: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    database: DatabaseStatus
    services: Dict[str, str] = Field(
        default_factory=lambda: {
            "conversation": "ready",
            "emotion_engine": "ready",
            "speech": "standby",
            "vision": "standby",
            "memory": "ready",
        }
    )
