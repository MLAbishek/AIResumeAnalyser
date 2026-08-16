from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import settings


def create_access_token(
    *,
    user_id: int,
    role: str,
) -> str:
    now = datetime.now(timezone.utc)

    expires_at = (
        now
        + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    )

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(
    token: str,
) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise ValueError(
            "Invalid or expired access token."
        ) from exc

    subject = payload.get("sub")
    role = payload.get("role")

    if subject is None:
        raise ValueError(
            "Access token is missing subject."
        )

    if role is None:
        raise ValueError(
            "Access token is missing role."
        )

    return payload