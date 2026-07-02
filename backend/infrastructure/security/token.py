"""Local JWT token creation and verification — HS256, no external IdP."""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from backend.shared.config import get_settings
from backend.shared.exceptions import AuthenticationError

_settings = get_settings()

ALGORITHM = "HS256"
_DEFAULT_EXPIRY_MINUTES = 60


def _secret() -> str:
    return _settings.jwt_secret_key  # type: ignore[attr-defined]


def create_access_token(
    user_id: str,
    username: str,
    roles: list[str],
    permissions: list[str],
    session_id: str,
    expiry_minutes: int = _DEFAULT_EXPIRY_MINUTES,
) -> tuple[str, datetime]:
    """Return (encoded_jwt, expires_at)."""
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=expiry_minutes)
    payload = {
        "sub": user_id,
        "username": username,
        "roles": roles,
        "permissions": permissions,
        "session_id": session_id,
        "iat": now,
        "exp": expires_at,
        "jti": secrets.token_hex(16),
    }
    encoded = jwt.encode(payload, _secret(), algorithm=ALGORITHM)
    return encoded, expires_at


def decode_access_token(token: str) -> dict:
    """Decode and validate token.  Raises AuthenticationError on failure."""
    try:
        payload = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError as e:
        raise AuthenticationError("Token expired") from e
    except InvalidTokenError as e:
        raise AuthenticationError("Invalid token") from e


def hash_token(token: str) -> str:
    """SHA-256 fingerprint stored in session table."""
    return hashlib.sha256(token.encode()).hexdigest()
