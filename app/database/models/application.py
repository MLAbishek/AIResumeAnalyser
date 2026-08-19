from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Application(Base):
    """
    The business relationship between a candidate and a job.

    This is distinct from ScreeningResult (the AI evaluation) and
    RankingResult/MatchProfile (scoring/explanation) - those represent
    the AI's assessment of a resume against a job. Application
    represents the candidate's decision to formally apply, and
    references the persisted screening produced for that resume/job
    pair.
    """

    __tablename__ = "applications"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "candidate_user_id",
            name="uq_application_job_candidate",
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

    candidate_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Nullable: a screening should always exist by the time an
    # application is created, but the column stays optional so an
    # application row is never blocked by a missing AI evaluation.
    screening_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "screening_results.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="applied",
        server_default="applied",
        nullable=False,
    )

    applied_at: Mapped[datetime] = mapped_column(
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

    job: Mapped["Job"] = relationship(
        back_populates="applications",
    )

    resume: Mapped["Resume"] = relationship()

    screening: Mapped["ScreeningResult | None"] = relationship()

    # The candidate's account - lets recruiter-facing views show the
    # real login email as a reliable identifier, independent of
    # whatever name/email the resume parser (imperfectly) extracted
    # from the uploaded document itself.
    candidate: Mapped["User"] = relationship(
        foreign_keys=[candidate_user_id],
    )
