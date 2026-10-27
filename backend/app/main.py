from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.database.session import engine
from backend.app.database.base import Base
import backend.app.models  # Ensure all SQLAlchemy models are registered
from backend.app.api.v1 import api_v1_router, chat_router, sessions_router, speech_router
from backend.app.api.v1.health import router as health_router
from backend.app.schemas.common import ApiErrorResponse

logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables are created (development convenience)
    logger.info("Initializing database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized successfully.")
    except Exception as exc:
        logger.error(f"Failed to auto-initialize database tables: {exc}")
    
    yield
    
    # Shutdown
    logger.info("Closing database engine...")
    await engine.dispose()
    logger.info("Application shutdown complete.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI Companion Multimodal Emotion-Aware Backend API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralized Error Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiErrorResponse(
            success=False,
            error_code=f"HTTP_{exc.status_code}",
            message=exc.detail if isinstance(exc.detail, str) else "HTTP Exception",
            details=exc.detail if not isinstance(exc.detail, str) else None,
        ).model_dump(),
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ApiErrorResponse(
            success=False,
            error_code="VALIDATION_ERROR",
            message="Input validation failed",
            details=exc.errors(),
        ).model_dump(),
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiErrorResponse(
            success=False,
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred.",
            details=str(exc) if settings.DEBUG else None,
        ).model_dump(),
    )

# Direct root API contract endpoints as specified in Master Spec Section 11:
# GET /api/health
# POST /api/chat
# POST /api/speech/transcribe
# POST /api/speech/synthesize
# GET/POST /api/sessions
app.include_router(health_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")
app.include_router(speech_router, prefix="/api")

# API v1 routes
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/health",
        "chat": "/api/chat",
        "sessions": "/api/sessions",
        "speech": {
            "transcribe": "/api/speech/transcribe",
            "synthesize": "/api/speech/synthesize",
        },
    }
