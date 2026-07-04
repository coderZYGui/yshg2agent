import hashlib
import hmac
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from .config import settings

# 使用 pbkdf2_hmac 做密码哈希, 避免对 bcrypt 原生库的强依赖, 保证跨平台自验证
_ITERATIONS = 120_000


def hash_password(password: str) -> str:
    salt = hashlib.sha256(settings.secret_key.encode()).digest()[:16]
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return dk.hex()


def verify_password(password: str, password_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password), password_hash)


def create_access_token(subject: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
