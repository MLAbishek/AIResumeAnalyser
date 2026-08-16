import pytest

from app.auth.password import (
    hash_password,
    verify_password,
)


def test_hash_password_returns_different_hash():
    password = "StrongPassword123!"

    hashed = hash_password(password)

    assert isinstance(hashed, str)
    assert hashed
    assert hashed != password


def test_hash_password_is_not_deterministic():
    password = "StrongPassword123!"

    first = hash_password(password)
    second = hash_password(password)

    assert first != second


def test_verify_password_accepts_correct_password():
    password = "StrongPassword123!"
    hashed = hash_password(password)

    assert verify_password(
        password,
        hashed,
    ) is True


def test_verify_password_rejects_wrong_password():
    hashed = hash_password(
        "StrongPassword123!"
    )

    assert verify_password(
        "WrongPassword!",
        hashed,
    ) is False


def test_hash_password_rejects_empty_password():
    with pytest.raises(ValueError):
        hash_password("")


def test_verify_password_rejects_empty_password():
    hashed = hash_password(
        "StrongPassword123!"
    )

    assert verify_password(
        "",
        hashed,
    ) is False


def test_verify_password_rejects_empty_hash():
    assert verify_password(
        "StrongPassword123!",
        "",
    ) is False