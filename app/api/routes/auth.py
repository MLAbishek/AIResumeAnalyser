from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.auth.google_oauth import (
    GoogleTokenError,
    verify_google_id_token,
)
from app.auth.schemas import (
    GoogleAuthRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.auth.service import (
    AuthenticationError,
    AuthService,
    EmailAlreadyExistsError,
    GoogleAccountConflictError,
    GoogleRoleRequiredError,
)


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    service = AuthService()

    try:
        user = service.authenticate(
            db=db,
            email=request.email,
            password=request.password,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        ) from exc

    token = service.create_token(user)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    service = AuthService()

    try:
        user = service.register(
            db=db,
            email=request.email,
            password=request.password,
            role=request.role,
        )
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )


@router.post(
    "/google",
    response_model=TokenResponse,
)
def google_auth(
    request: GoogleAuthRequest,
    db: Session = Depends(get_db),
):
    """
    Exchange a verified Google ID token for the application's own
    JWT - the same token type/shape issued by password login. The
    Google credential itself is never used as, or returned as, an
    application access token.
    """

    try:
        identity = verify_google_id_token(request.credential)
    except GoogleTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    service = AuthService()

    try:
        user = service.authenticate_or_register_google(
            db=db,
            google_sub=identity.sub,
            email=identity.email,
            role=request.role,
        )
    except GoogleRoleRequiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except GoogleAccountConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    token = service.create_token(user)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )