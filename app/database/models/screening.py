from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ScreeningResult(Base):
    __tablename__ = "screening_results"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "resume_id",
            name="uq_screening_job_resume",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    eligible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    eligibility_details: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    decision: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    final_score: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    decision_reason: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    job: Mapped["Job"] = relationship(
        back_populates="screening_results",
    )

    resume: Mapped["Resume"] = relationship(
        back_populates="screening_results",
    )

    ranking: Mapped["RankingResult | None"] = relationship(
        back_populates="screening",
        uselist=False,
        cascade="all, delete-orphan",
    )

    profile: Mapped["MatchProfile | None"] = relationship(
        back_populates="screening",
        uselist=False,
        cascade="all, delete-orphan",
    )