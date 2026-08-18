from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RankingResult(Base):
    __tablename__ = "ranking_results"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    screening_id: Mapped[int] = mapped_column(
        ForeignKey(
            "screening_results.id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
        index=True,
    )

    rank: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    skill_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    experience_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    seniority_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    education_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    semantic_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    screening: Mapped["ScreeningResult"] = relationship(
        back_populates="ranking",
    )