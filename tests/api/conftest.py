import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.auth.models import User
from app.auth.password import hash_password
from app.auth.jwt import create_access_token
from app.database.connection import engine
from main import app


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        expire_on_commit=False,
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    # Create authenticated test user
    user = User(
        email="api-test@example.com",
        password_hash=hash_password("TestPassword123!"),
        role="admin",
        is_active=True,
    )

    db.add(user)
    db.flush()

    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    test_client = TestClient(app)

    test_client.headers.update(
        {
            "Authorization": f"Bearer {access_token}"
        }
    )

    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()