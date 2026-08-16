from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.auth.jwt import (
    create_access_token,
    decode_access_token,
)
from app.core.config import settings


def test_create_access_token_returns_string():
    token = create_access_token(
        user_id=123,
        role="recruiter",
    )

    assert isinstance(token, str)
    assert token


def test_created_token_contains_expected_claims():
    token = create_access_token(
        user_id=123,
        role="recruiter",
    )

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == "123"
    assert payload["role"] == "recruiter"
    assert "iat" in payload
    assert "exp" in payload


def test_decode_access_token_returns_payload():
    token = create_access_token(
        user_id=42,
        role="admin",
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "42"
    assert payload["role"] == "admin"


def test_invalid_token_is_rejected():
    with pytest.raises(ValueError, match="Invalid or expired"):
        decode_access_token(
            "invalid.token.value"
        )


def test_expired_token_is_rejected():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": "1",
            "role": "viewer",
            "iat": now - timedelta(minutes=10),
            "exp": now - timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(ValueError, match="Invalid or expired"):
        decode_access_token(token)


def test_token_without_subject_is_rejected():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "role": "viewer",
            "iat": now,
            "exp": now + timedelta(minutes=10),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(
        ValueError,
        match="missing subject",
    ):
        decode_access_token(token)


def test_token_without_role_is_rejected():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": "1",
            "iat": now,
            "exp": now + timedelta(minutes=10),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(
        ValueError,
        match="missing role",
    ):
        decode_access_token(token)