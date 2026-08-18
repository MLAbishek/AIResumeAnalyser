from typing import Literal

from pydantic import BaseModel, EmailStr, Field


Role = Literal[
    "admin",
    "recruiter",
    "viewer",
    "candidate",
]

RegistrationRole = Literal[
    "recruiter",
    "candidate",
]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
    )
    role: RegistrationRole = "recruiter"


class GoogleAuthRequest(BaseModel):
    # The Google ID token (JWT) returned by Google Identity Services
    # in the browser - verified server-side, never trusted as-is.
    credential: str = Field(min_length=1)

    # Only meaningful the first time this Google account signs in:
    # it becomes the new local user's role. Ignored for an existing
    # Google-linked account, whose stored role is always used
    # instead. Reuses the same closed enum as password registration,
    # so "admin" is rejected by validation before any handler code
    # runs.
    role: RegistrationRole | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: Role
    is_active: bool