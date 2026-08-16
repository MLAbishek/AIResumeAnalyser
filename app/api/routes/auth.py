from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.auth.schemas import (
    LoginRequest,
    TokenResponse,
)
from app.auth.service import (
    AuthenticationError,
    AuthService,
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