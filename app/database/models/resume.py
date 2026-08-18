from datetime import date,datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    resume_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    skills: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    job_titles: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    organizations: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    technologies: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    total_experience_months: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    raw_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Set for resumes a candidate uploads themselves through the
    # candidate portal. NULL for resumes created via the recruiter
    # JSON endpoint (no individual candidate owner).
    owner_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
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

    experiences: Mapped[list["ResumeExperience"]] = relationship(
        back_populates="resume",
        cascade="all, delete-orphan",
    )

    education: Mapped[list["ResumeEducation"]] = relationship(
        back_populates="resume",
        cascade="all, delete-orphan",
    )

    screening_results: Mapped[list["ScreeningResult"]] = relationship(
        back_populates="resume",
        cascade="all, delete-orphan",
    )


class ResumeExperience(Base):
    __tablename__ = "resume_experiences"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    resume_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    company: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    duration_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    resume: Mapped["Resume"] = relationship(
        back_populates="experiences",
    )


class ResumeEducation(Base):
    __tablename__ = "resume_education"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    resume_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    degree: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    institution: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    field_of_study: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    resume: Mapped["Resume"] = relationship(
        back_populates="education",
    )