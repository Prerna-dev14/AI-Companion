import time
from typing import Dict, List, Tuple
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.app.schemas.common import ApiErrorResponse


class SlidingWindowRateLimiter:
    """Thread-safe sliding-window in-memory rate limiter."""

    def __init__(
        self,
        default_limit: int = 120,
        heavy_limit: int = 40,
        window_seconds: int = 60,
    ):
        self.default_limit = default_limit
        self.heavy_limit = heavy_limit
        self.window_seconds = window_seconds
        # Mapping: client_key -> list of timestamp floats
        self._history: Dict[str, List[float]] = {}
        # Routes considered compute-heavy (vision frames, speech audio, voice prosody)
        self.heavy_prefixes = (
            "/api/speech/transcribe",
            "/api/speech/synthesize",
            "/api/emotion/face",
            "/api/emotion/voice",
        )

    def _get_limit(self, path: str) -> int:
        for prefix in self.heavy_prefixes:
            if path.startswith(prefix):
                return self.heavy_limit
        return self.default_limit

    def is_allowed(self, client_id: str, path: str) -> Tuple[bool, int, int, int]:
        """Checks if request is within limits.
        
        Returns:
            (allowed: bool, limit: int, remaining: int, retry_after: int)
        """
        now = time.time()
        limit = self._get_limit(path)
        cutoff = now - self.window_seconds

        timestamps = self._history.get(client_id, [])
        # Prune entries outside window
        timestamps = [ts for ts in timestamps if ts > cutoff]

        if len(timestamps) >= limit:
            oldest = timestamps[0]
            retry_after = max(1, int(oldest + self.window_seconds - now))
            self._history[client_id] = timestamps
            return False, limit, 0, retry_after

        timestamps.append(now)
        self._history[client_id] = timestamps
        remaining = max(0, limit - len(timestamps))
        return True, limit, remaining, 0

    def reset(self):
        """Clears rate limiter records (useful for test isolation)."""
        self._history.clear()


rate_limiter = SlidingWindowRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Starlette middleware intercepting requests to enforce rate limits."""

    async def dispatch(self, request: Request, call_next):
        # Exempt health and docs endpoints from rate limiting
        if request.url.path in ("/api/health", "/docs", "/redoc", "/openapi.json", "/"):
            return await call_next(request)

        # Identify client by IP or forwarded header
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        key = f"{client_ip}:{request.url.path}"
        allowed, limit, remaining, retry_after = rate_limiter.is_allowed(key, request.url.path)

        if not allowed:
            error_payload = ApiErrorResponse(
                success=False,
                error_code="RATE_LIMIT_EXCEEDED",
                message=f"Rate limit exceeded. Maximum {limit} requests per minute allowed.",
                details={"retry_after_seconds": retry_after},
            ).model_dump()
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error_payload,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
