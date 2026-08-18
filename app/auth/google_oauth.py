from dataclasses import dataclass

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import settings


_ACCOUNTS_ISSUERS = {
    "accounts.google.com",
    "https://accounts.google.com",
}

# One shared transport so verification reuses HTTP connections /
# Google's cached signing-key fetches instead of opening a new
# session per request.
_request_session = google_requests.Request()


class GoogleTokenError(Exception):
    """
    Raised whenever a Google ID token fails verification for any
    reason - bad signature, expired, wrong audience/issuer, or the
    server has no Google Client ID configured at all. Callers should
    treat every case the same way: reject the request with a generic,
    safe error - never surface which specific check failed.
    """

    pass


@dataclass(frozen=True)
class GoogleIdentity:
    """
    The minimal, already-verified identity extracted from a Google
    ID token. `sub` is Google's stable per-account identifier and is
    what the rest of the app must use as the external identity key -
    never `email`, which a Google account can change.
    """

    sub: str
    email: str | None
    email_verified: bool


def verify_google_id_token(credential: str) -> GoogleIdentity:
    """
    Verify a Google ID token (the `credential` produced by Google
    Identity Services in the browser) and return the identity it
    asserts.

    This delegates signature, expiry, issuer and audience checks
    entirely to google-auth's own `verify_oauth2_token`, per Google's
    documented guidance to verify ID tokens server-side using a
    Google-supported client library rather than hand-rolling JWT
    verification: https://developers.google.com/identity/gsi/web/guides/verify-google-id-token
    """

    if not credential:
        raise GoogleTokenError("Missing Google credential.")

    if not settings.google_client_id:
        raise GoogleTokenError(
            "Google authentication is not configured."
        )

    try:
        claims = google_id_token.verify_oauth2_token(
            credential,
            _request_session,
            audience=settings.google_client_id,
        )
    except (ValueError, GoogleTokenError) as exc:
        # verify_oauth2_token raises ValueError for every failure
        # mode: bad signature, expired token, wrong audience, or a
        # malformed token. Google's own client library is the single
        # source of truth for which of those applies - we don't
        # re-derive or expose that detail to the caller.
        raise GoogleTokenError(
            "Invalid or expired Google credential."
        ) from exc

    issuer = claims.get("iss")

    if issuer not in _ACCOUNTS_ISSUERS:
        raise GoogleTokenError(
            "Invalid or expired Google credential."
        )

    sub = claims.get("sub")

    if not sub:
        raise GoogleTokenError(
            "Invalid or expired Google credential."
        )

    return GoogleIdentity(
        sub=sub,
        email=claims.get("email"),
        email_verified=bool(
            claims.get("email_verified", False)
        ),
    )
