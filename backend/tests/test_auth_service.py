"""Pure-logic auth tests: hashing + JWT round-trips."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.config import settings
from app.services.auth_service import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_round_trip():
    h = hash_password("hunter2hunter2")
    assert verify_password("hunter2hunter2", h) is True


def test_verify_wrong_password_fails():
    h = hash_password("correct-password-123")
    assert verify_password("wrong-password", h) is False


def test_create_and_decode_token_round_trip():
    token = create_access_token("abc-123", "expert")
    payload = decode_token(token)
    assert payload["sub"] == "abc-123"
    assert payload["role"] == "expert"
    assert "exp" in payload and "iat" in payload


def test_decode_expired_token_raises():
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "u",
        "role": "user",
        "iat": now - timedelta(days=10),
        "exp": now - timedelta(seconds=1),
    }
    expired = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(expired)


def test_decode_invalid_signature_raises():
    bad = jwt.encode({"sub": "x", "role": "user"}, "different-secret", algorithm="HS256")
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(bad)
