import pytest

from app.auth.google_oauth import GoogleIdentity, GoogleTokenError
from app.auth.models import User
from app.auth.password import hash_password
import app.api.routes.auth as auth_routes


def _mock_google_identity(
    monkeypatch,
    *,
    sub="google-sub-1",
    email="google-user@example.com",
    email_verified=True,
):
    def fake_verify(credential: str) -> GoogleIdentity:
        return GoogleIdentity(
            sub=sub,
            email=email,
            email_verified=email_verified,
        )

    monkeypatch.setattr(
        auth_routes, "verify_google_id_token", fake_verify
    )


def _mock_google_failure(monkeypatch, message: str):
    def fake_verify(credential: str):
        raise GoogleTokenError(message)

    monkeypatch.setattr(
        auth_routes, "verify_google_id_token", fake_verify
    )


class TestGoogleAuthHappyPath:
    def test_new_recruiter_google_user_is_created(
        self, client, db, monkeypatch
    ):
        _mock_google_identity(
            monkeypatch,
            sub="google-sub-recruiter",
            email="google-recruiter@example.com",
        )

        response = client.post(
            "/api/auth/google",
            json={
                "credential": "fake-id-token",
                "role": "recruiter",
            },
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["token_type"] == "bearer"
        assert isinstance(body["access_token"], str)

        user = (
            db.query(User)
            .filter(
                User.google_sub == "google-sub-recruiter"
            )
            .first()
        )
        assert user is not None
        assert user.email == "google-recruiter@example.com"
        assert user.role == "recruiter"
        assert user.auth_provider == "google"
        assert user.password_hash is None

    def test_new_candidate_google_user_is_created(
        self, client, db, monkeypatch
    ):
        _mock_google_identity(
            monkeypatch,
            sub="google-sub-candidate",
            email="google-candidate@example.com",
        )

        response = client.post(
            "/api/auth/google",
            json={
                "credential": "fake-id-token",
                "role": "candidate",
            },
        )

        assert response.status_code == 200, response.text

        user = (
            db.query(User)
            .filter(
                User.google_sub == "google-sub-candidate"
            )
            .first()
        )
        assert user is not None
        assert user.role == "candidate"

    def test_existing_google_user_logs_in_without_duplication(
        self, client, db, monkeypatch
    ):
        _mock_google_identity(
            monkeypatch,
            sub="google-sub-repeat",
            email="google-repeat@example.com",
        )

        first = client.post(
            "/api/auth/google",
            json={
                "credential": "fake-id-token",
                "role": "recruiter",
            },
        )
        assert first.status_code == 200

        second = client.post(
            "/api/auth/google",
            json={"credential": "fake-id-token-2"},
        )
        assert second.status_code == 200

        users = (
            db.query(User)
            .filter(
                User.google_sub == "google-sub-repeat"
            )
            .all()
        )
        assert len(users) == 1

    def test_google_login_issues_the_applications_own_jwt(
        self, client, db, monkeypatch
    ):
        _mock_google_identity(
            monkeypatch,
            sub="google-sub-jwt",
            email="google-jwt@example.com",
        )

        response = client.post(
            "/api/auth/google",
            json={
                "credential": "fake-id-token",
                "role": "recruiter",
            },
        )

        token = response.json()["access_token"]

        # The returned token is the app's own JWT (decodable with the
        # app's secret/algorithm) - not the raw Google credential.
        from app.auth.jwt import decode_access_token

        payload = decode_access_token(token)
        assert payload["role"] == "recruiter"
        assert token != "fake-id-token"


class TestGoogleRoleHandling:
    def test_role_cannot_be_changed_by_later_google_login(
        self, client, db, monkeypatch
    ):
        _mock_google_identity(
            monkeypatch,
            sub="google-sub-role-lock",
            email="google-role-lock@example.com",
        )

        client.post(
            "/api/auth/google",
            json={
                "credential": "fake-id-token",
                "role": "candidate",
            },
        )

        # Attempting to log back in while claiming "recruiter" must
        # not change the stored role.
        response = client.post(
            "/api/auth/google",
            json={
                "credential": "fake-id-token-2",
                "role": "recruiter",
            },
        )
        assert response.status_code == 200

        user = (
            db.query(User)
            .filter(
                User.google_sub == "google-sub-role-lock"
            )
            .first()
        )
        assert user.role == "candidate"

    def test_admin_role_rejected_by_schema_validation(
        self, client, db, monkeypatch
    ):
        _mock_google_identity(monkeypatch)

        response = client.post(
            "/api/auth/google",
            json={
                "credential": "fake-id-token",
                "role": "admin",
            },
        )

        assert response.status_code == 422

    def test_new_google_user_without_role_is_rejected(
        self, client, db, monkeypatch
    ):
        _mock_google_identity(
            monkeypatch,
            sub="google-sub-norole",
            email="google-norole@example.com",
        )

        response = client.post(
            "/api/auth/google",
            json={"credential": "fake-id-token"},
        )

        assert response.status_code == 400

        user = (
            db.query(User)
            .filter(
                User.google_sub == "google-sub-norole"
            )
            .first()
        )
        assert user is None


class TestGoogleAccountConflict:
    def test_existing_password_account_email_conflict_is_rejected(
        self, client, db, monkeypatch
    ):
        existing = User(
            email="shared-email@example.com",
            password_hash=hash_password(
                "StrongPassword123!"
            ),
            role="recruiter",
            is_active=True,
        )
        db.add(existing)
        db.commit()

        _mock_google_identity(
            monkeypatch,
            sub="google-sub-conflict",
            email="shared-email@example.com",
        )

        response = client.post(
            "/api/auth/google",
            json={
                "credential": "fake-id-token",
                "role": "recruiter",
            },
        )

        assert response.status_code == 409

        # The existing password account was not silently converted
        # to a Google account.
        db.refresh(existing)
        assert existing.google_sub is None
        assert existing.auth_provider == "password"

    def test_google_only_account_cannot_password_login(
        self, client, db, monkeypatch
    ):
        _mock_google_identity(
            monkeypatch,
            sub="google-sub-pwtry",
            email="google-pwtry@example.com",
        )

        client.post(
            "/api/auth/google",
            json={
                "credential": "fake-id-token",
                "role": "recruiter",
            },
        )

        response = client.post(
            "/api/auth/login",
            json={
                "email": "google-pwtry@example.com",
                "password": "anything-at-all",
            },
        )

        assert response.status_code == 401
        assert "Google" in response.json()["detail"]


class TestGoogleTokenVerificationFailures:
    @pytest.mark.parametrize(
        "message",
        [
            "Invalid or expired Google credential.",
            "Token used too early.",
            "Wrong audience.",
            "Wrong issuer.",
        ],
    )
    def test_invalid_token_variants_return_401(
        self, client, db, monkeypatch, message
    ):
        _mock_google_failure(monkeypatch, message)

        response = client.post(
            "/api/auth/google",
            json={
                "credential": "not-a-real-token",
                "role": "recruiter",
            },
        )

        assert response.status_code == 401
        detail = response.json()["detail"]
        assert "Traceback" not in detail

    def test_missing_credential_returns_422(self, client, db):
        response = client.post(
            "/api/auth/google",
            json={"role": "recruiter"},
        )

        assert response.status_code == 422

    def test_not_configured_returns_401_without_calling_google(
        self, client, db, monkeypatch
    ):
        from app.core import config as config_module

        monkeypatch.setattr(
            config_module.settings, "google_client_id", ""
        )

        def fail_if_called(credential: str):
            raise AssertionError(
                "verify_oauth2_token should not be reached "
                "when Google auth is unconfigured"
            )

        # Patch the real verifier (not the route's re-export) to
        # prove the "not configured" guard short-circuits before any
        # network call would happen.
        from app.auth import google_oauth as google_oauth_module

        monkeypatch.setattr(
            google_oauth_module.google_id_token,
            "verify_oauth2_token",
            fail_if_called,
        )

        response = client.post(
            "/api/auth/google",
            json={
                "credential": "irrelevant",
                "role": "recruiter",
            },
        )

        assert response.status_code == 401
        assert "not configured" in response.json()["detail"]
