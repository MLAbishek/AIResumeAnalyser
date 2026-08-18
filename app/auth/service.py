from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.auth.password import hash_password, verify_password
from app.auth.models import User


DEFAULT_REGISTRATION_ROLE = "recruiter"

ALLOWED_REGISTRATION_ROLES = {"recruiter", "candidate"}


class AuthenticationError(Exception):
    pass


class EmailAlreadyExistsError(Exception):
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

    def register(
        self,
        db: Session,
        email: str,
        password: str,
        role: str = DEFAULT_REGISTRATION_ROLE,
    ) -> User:

        # Defense in depth: RegisterRequest.role is already a
        # closed Literal["recruiter", "candidate"], so a client
        # can never submit "admin" and have it reach this point.
        # This check guards direct callers of the service too.
        if role not in ALLOWED_REGISTRATION_ROLES:
            role = DEFAULT_REGISTRATION_ROLE

        existing = (
            db.query(User)
            .filter(
                User.email == email
            )
            .first()
        )

        if existing is not None:
            raise EmailAlreadyExistsError(
                "An account with this email already exists."
            )

        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )

        db.add(user)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()

            raise EmailAlreadyExistsError(
                "An account with this email already exists."
            ) from None

        db.refresh(user)

        return user

    def create_token(
        self,
        user: User,
    ) -> str:
        return create_access_token(
            user_id=user.id,
            role=user.role,
        )