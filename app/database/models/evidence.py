from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class EvidenceReference(Base):
    __tablename__ = "evidence_references"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    profile_id: Mapped[int] = mapped_column(
        ForeignKey(
            "match_profiles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    claim: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    section: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    evidence: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    profile: Mapped["MatchProfile"] = relationship(
        back_populates="evidence",
    )