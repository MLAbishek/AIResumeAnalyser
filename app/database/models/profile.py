from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class MatchProfile(Base):
    __tablename__ = "match_profiles"

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

    gap_analysis: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    explanation: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    screening: Mapped["ScreeningResult"] = relationship(
        back_populates="profile",
    )

    evidence: Mapped[list["EvidenceReference"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )