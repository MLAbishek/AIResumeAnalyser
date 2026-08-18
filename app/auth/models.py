from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # Nullable: Google-only accounts (auth_provider="google") never
    # get a local password. Password accounts always set this.
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Stable external identity for Google Sign-In - Google's `sub`
    # claim, never the email, per Google's own guidance that `sub`
    # (not email) is the durable identifier for an account. NULL for
    # password-only accounts.
    google_sub: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    auth_provider: Mapped[str] = mapped_column(
        String(20),
        default="password",
        server_default="password",
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )