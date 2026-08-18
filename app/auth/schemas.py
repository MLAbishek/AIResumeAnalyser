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


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: Role
    is_active: bool