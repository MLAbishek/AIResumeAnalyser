import pytest

from app.auth.models import User
from app.auth.password import hash_password
from app.auth.service import (
    AuthService,
    AuthenticationError,
)


def make_user(
    email="recruiter@example.com",
    password="StrongPassword123!",
    role="recruiter",
    is_active=True,
):
    return User(
        id=1,
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    )


def test_authenticate_valid_user(db):
    user = make_user()

    db.add(user)
    db.flush()

    service = AuthService()

    authenticated = service.authenticate(
        db=db,
        email="recruiter@example.com",
        password="StrongPassword123!",
    )

    assert authenticated.id == user.id
    assert authenticated.email == user.email


def test_authenticate_unknown_email_fails(db):
    service = AuthService()

    with pytest.raises(
        AuthenticationError,
        match="Invalid email or password",
    ):
        service.authenticate(
            db=db,
            email="missing@example.com",
            password="StrongPassword123!",
        )


def test_authenticate_wrong_password_fails(db):
    user = make_user()

    db.add(user)
    db.flush()

    service = AuthService()

    with pytest.raises(
        AuthenticationError,
        match="Invalid email or password",
    ):
        service.authenticate(
            db=db,
            email="recruiter@example.com",
            password="WrongPassword!",
        )


def test_inactive_user_cannot_authenticate(db):
    user = make_user(
        is_active=False
    )

    db.add(user)
    db.flush()

    service = AuthService()

    with pytest.raises(
        AuthenticationError,
        match="inactive",
    ):
        service.authenticate(
            db=db,
            email="recruiter@example.com",
            password="StrongPassword123!",
        )


def test_create_token_for_user():
    user = make_user()

    service = AuthService()

    token = service.create_token(user)

    assert isinstance(token, str)
    assert token