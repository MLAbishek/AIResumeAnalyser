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


class GoogleAccountConflictError(Exception):
    """
    The Google account's email already belongs to an existing,
    non-Google (password) account. We never silently take over an
    existing account just because the email matches - that would let
    anyone who controls a Google account with the same address as a
    victim's password account gain access to it. The caller must sign
    in with their password instead.
    """

    pass


class GoogleRoleRequiredError(Exception):
    """
    Raised when a brand-new Google account is signing in for the
    first time without a role selection. Only relevant for account
    creation - an existing Google-linked account never hits this,
    since its stored role is always used.
    """

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

        if user.password_hash is None:
            # Google-only account: there is no password to check.
            # Naming the auth method isn't a security leak (it
            # reveals nothing about password validity), and it stops
            # a real user from getting stuck on a login form their
            # account can never satisfy.
            raise AuthenticationError(
                "This account uses Google Sign-In. "
                "Please continue with Google."
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

    def authenticate_or_register_google(
        self,
        db: Session,
        *,
        google_sub: str,
        email: str | None,
        role: str | None = None,
    ) -> User:
        """
        Resolve a verified Google identity to a local User, creating
        one if this is the account's first sign-in.

        `google_sub` (Google's `sub` claim) is the sole external
        identity key - never the email - so this always looks the
        account up by `google_sub` first.
        """

        existing = (
            db.query(User)
            .filter(User.google_sub == google_sub)
            .first()
        )

        if existing is not None:
            # The role stored at first sign-in is authoritative
            # forever; a later Google login can never change it.
            if not existing.is_active:
                raise AuthenticationError(
                    "User account is inactive."
                )

            return existing

        if email:
            email_conflict = (
                db.query(User)
                .filter(User.email == email)
                .first()
            )

            if email_conflict is not None:
                # A different, non-Google account already owns this
                # email. Do not link automatically - require the
                # account's existing authentication method instead.
                raise GoogleAccountConflictError(
                    "An account with this email already exists. "
                    "Please sign in with your password instead."
                )

        if role not in ALLOWED_REGISTRATION_ROLES:
            raise GoogleRoleRequiredError(
                "A role (recruiter or candidate) is required "
                "to create a new account."
            )

        if not email:
            raise AuthenticationError(
                "Google did not provide an email for this "
                "account."
            )

        user = User(
            email=email,
            password_hash=None,
            google_sub=google_sub,
            auth_provider="google",
            role=role,
            is_active=True,
        )

        db.add(user)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()

            raise GoogleAccountConflictError(
                "An account with this email or Google identity "
                "already exists."
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