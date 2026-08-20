"""Password-hashing and JWT tests (no DB required)."""

from __future__ import annotations

import time

import jwt
import pytest

from app.config import settings
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_roundtrip():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert hashed.startswith("$argon2")
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_hash_password_is_salted():
    a = hash_password("same-password")
    b = hash_password("same-password")
    assert a != b  # random salt per hash


def test_access_token_roundtrip():
    token = create_access_token("user-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
    assert payload["exp"] > payload["iat"]


def test_access_token_rejects_bad_signature():
    token = create_access_token("user-123")
    tampered = jwt.encode(
        {"sub": "attacker"}, "not-the-secret", algorithm=settings.jwt_algorithm
    )
    assert tampered != token
    with pytest.raises(jwt.PyJWTError):
        jwt.decode(tampered, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def test_access_token_expiry():
    # Expire immediately; pyjwt raises ExpiredSignatureError on decode.
    token = create_access_token("user-123", expires_minutes=-1)
    time.sleep(0.01)
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)
