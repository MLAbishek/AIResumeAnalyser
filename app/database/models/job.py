from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    job_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    job_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    raw_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    required_skills: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    preferred_skills: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    required_technologies: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    preferred_technologies: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    education_requirements: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    required_certifications: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    responsibilities: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    required_experience_months: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Nullable for backward compatibility with jobs created before
    # recruiter ownership existed. A NULL owner is treated as a
    # legacy/shared job manageable by any recruiter.
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
        server_default="open",
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

    screening_results: Mapped[list["ScreeningResult"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )

    applications: Mapped[list["Application"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )