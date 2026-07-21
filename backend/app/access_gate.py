from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from .config import settings

ACCESS_COOKIE_NAME = "yshg_access"
_ACCESS_SCOPE = "access_gate"


def create_access_gate_token() -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return jwt.encode(
        {"scope": _ACCESS_SCOPE, "exp": expires_at},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def has_valid_access_gate(token: str | None) -> bool:
    if not token:
        return False
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return False
    return payload.get("scope") == _ACCESS_SCOPE
