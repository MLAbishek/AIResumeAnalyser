from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.auth.password import verify_password
from app.auth.models import User


class AuthenticationError(Exception):
    pass


class AuthService:

    def authenticate(
        self,
        db: Session,
        email: str,
        password: str,
    ) -> User:

        user = (
            db.query(User)
            .filter(
                User.email == email
            )
            .first()
        )

        if user is None:
            raise AuthenticationError(
                "Invalid email or password."
            )

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise AuthenticationError(
                "Invalid email or password."
            )

        if not user.is_active:
            raise AuthenticationError(
                "User account is inactive."
            )

        return user

    def create_token(
        self,
        user: User,
    ) -> str:
        return create_access_token(
            user_id=user.id,
            role=user.role,
        )