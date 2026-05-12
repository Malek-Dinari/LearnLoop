"""Pure-logic auth helpers: password hashing + JWT encode/decode."""

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def create_access_token(user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(days=settings.jwt_expiry_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode a JWT and return its payload.

    Raises:
        jwt.ExpiredSignatureError: token past expiry.
        jwt.InvalidTokenError: malformed / bad signature / etc.
    """
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
