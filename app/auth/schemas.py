from typing import Literal

from pydantic import BaseModel, EmailStr


Role = Literal[
    "admin",
    "recruiter",
    "viewer",
]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: Role
    is_active: bool