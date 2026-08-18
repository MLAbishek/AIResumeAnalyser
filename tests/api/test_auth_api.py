from app.auth.models import User


def test_register_endpoint_creates_user(client, db):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "api-register@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "api-register@example.com"
    assert data["role"] == "recruiter"
    assert data["is_active"] is True
    assert "password" not in data
    assert "password_hash" not in data

    user = (
        db.query(User)
        .filter(
            User.email == "api-register@example.com"
        )
        .first()
    )

    assert user is not None
    assert user.password_hash != "StrongPassword123!"


def test_register_duplicate_email_returns_409(
    client,
):
    payload = {
        "email": "api-duplicate@example.com",
        "password": "StrongPassword123!",
    }

    first = client.post(
        "/api/auth/register",
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        "/api/auth/register",
        json=payload,
    )

    assert second.status_code == 409

    detail = second.json()["detail"]

    assert "already exists" in detail
    assert "IntegrityError" not in detail
    assert "UNIQUE constraint" not in detail


def test_register_invalid_email_returns_422(
    client,
):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "not-an-email",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 422


def test_register_short_password_returns_422(
    client,
):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "api-shortpw@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_register_rejects_privileged_role_field(
    client, db,
):
    # RegisterRequest.role is a closed
    # Literal["recruiter", "candidate"] (see
    # tests/api/test_candidate_portal_api.py for the
    # recruiter/candidate role assignment tests) - "admin" is not a
    # valid value at all, so the request is rejected outright rather
    # than silently downgraded.
    response = client.post(
        "/api/auth/register",
        json={
            "email": "api-escalation@example.com",
            "password": "StrongPassword123!",
            "role": "admin",
        },
    )

    assert response.status_code == 422

    user = (
        db.query(User)
        .filter(
            User.email == "api-escalation@example.com"
        )
        .first()
    )

    assert user is None


def test_login_with_newly_registered_account(
    client,
):
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "api-login-flow@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "api-login-flow@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert login_response.status_code == 200

    body = login_response.json()

    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 0
