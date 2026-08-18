import pytest

from app.auth.models import User
from app.auth.password import verify_password
from app.auth.service import (
    AuthService,
    EmailAlreadyExistsError,
)


def test_register_creates_user(db):
    service = AuthService()

    user = service.register(
        db=db,
        email="new-recruiter@example.com",
        password="StrongPassword123!",
    )

    assert user.id is not None
    assert user.email == "new-recruiter@example.com"
    assert user.is_active is True

    persisted = (
        db.query(User)
        .filter(
            User.email == "new-recruiter@example.com"
        )
        .first()
    )

    assert persisted is not None
    assert persisted.id == user.id


def test_register_hashes_password(db):
    service = AuthService()

    user = service.register(
        db=db,
        email="hashed-password@example.com",
        password="StrongPassword123!",
    )

    assert user.password_hash != "StrongPassword123!"
    assert verify_password(
        "StrongPassword123!",
        user.password_hash,
    )


def test_register_assigns_default_role(db):
    service = AuthService()

    user = service.register(
        db=db,
        email="default-role@example.com",
        password="StrongPassword123!",
    )

    assert user.role == "recruiter"


def test_register_duplicate_email_fails(db):
    service = AuthService()

    service.register(
        db=db,
        email="duplicate@example.com",
        password="StrongPassword123!",
    )

    with pytest.raises(
        EmailAlreadyExistsError,
        match="already exists",
    ):
        service.register(
            db=db,
            email="duplicate@example.com",
            password="AnotherPassword123!",
        )


def test_registered_user_can_authenticate(db):
    service = AuthService()

    service.register(
        db=db,
        email="login-after-register@example.com",
        password="StrongPassword123!",
    )

    authenticated = service.authenticate(
        db=db,
        email="login-after-register@example.com",
        password="StrongPassword123!",
    )

    assert authenticated.email == (
        "login-after-register@example.com"
    )
    assert authenticated.role == "recruiter"
