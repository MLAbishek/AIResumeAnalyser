import pytest

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.dependencies import (
    get_current_user,
    require_role,
)
from app.auth.jwt import create_access_token
from app.auth.models import User
from app.auth.password import hash_password


def make_user(
    user_id=1,
    role="recruiter",
    is_active=True,
):
    return User(
        id=user_id,
        email=f"user{user_id}@example.com",
        password_hash=hash_password(
            "StrongPassword123!"
        ),
        role=role,
        is_active=is_active,
    )


def test_get_current_user_returns_user(db):
    user = make_user()

    db.add(user)
    db.flush()

    token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    result = get_current_user(
        credentials=credentials,
        db=db,
    )

    assert result.id == user.id
    assert result.role == "recruiter"


def test_get_current_user_rejects_invalid_token(db):
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid-token",
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_missing_user(db):
    token = create_access_token(
        user_id=999999,
        role="viewer",
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_inactive_user(db):
    user = make_user(
        is_active=False
    )

    db.add(user)
    db.flush()

    token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        get_current_user(
            credentials=credentials,
            db=db,
        )

    assert exc_info.value.status_code == 403


def test_require_role_allows_authorized_role():
    user = make_user(
        role="admin"
    )

    dependency = require_role(
        "admin"
    )

    result = dependency(
        current_user=user
    )

    assert result is user


def test_require_role_rejects_unauthorized_role():
    user = make_user(
        role="viewer"
    )

    dependency = require_role(
        "admin"
    )

    with pytest.raises(
        HTTPException
    ) as exc_info:
        dependency(
            current_user=user
        )

    assert exc_info.value.status_code == 403


def test_require_role_supports_multiple_roles():
    user = make_user(
        role="recruiter"
    )

    dependency = require_role(
        "admin",
        "recruiter",
    )

    result = dependency(
        current_user=user
    )

    assert result is user