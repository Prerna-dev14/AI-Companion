import time
from typing import Optional, Dict, Any
import jwt
from fastapi import Request, HTTPException, status, Header

from backend.app.core.config import settings

ALGORITHM = "HS256"


def create_access_token(data: Dict[str, Any], expires_delta_seconds: Optional[int] = None) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    expire_seconds = expires_delta_seconds or (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    to_encode.update({"exp": int(time.time()) + expire_seconds, "iat": int(time.time())})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a signed JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_current_user_id(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
) -> Optional[str]:
    """Resolves user_id from Bearer JWT header, X-User-ID header, or query param, falling back to None.
    
    This enables frictionless client demo access while enforcing token parsing if provided.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        payload = decode_access_token(token)
        return payload.get("sub") or payload.get("user_id")

    if x_user_id:
        return x_user_id.strip()

    return request.query_params.get("user_id")
