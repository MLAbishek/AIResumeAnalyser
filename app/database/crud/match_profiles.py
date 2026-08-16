from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.profile import MatchProfile


def create_match_profile(
    db: Session,
    *,
    screening_id: int,
    gap_analysis: dict,
    explanation: dict,
) -> MatchProfile:
    profile = MatchProfile(
        screening_id=screening_id,
        gap_analysis=gap_analysis,
        explanation=explanation,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


def get_match_profile(
    db: Session,
    screening_id: int,
) -> MatchProfile | None:
    statement = select(MatchProfile).where(
        MatchProfile.screening_id == screening_id
    )

    return db.scalar(statement)


def update_match_profile(
    db: Session,
    profile: MatchProfile,
    *,
    gap_analysis: dict | None = None,
    explanation: dict | None = None,
) -> MatchProfile:
    if gap_analysis is not None:
        profile.gap_analysis = gap_analysis

    if explanation is not None:
        profile.explanation = explanation

    db.commit()
    db.refresh(profile)

    return profile


def delete_match_profile(
    db: Session,
    profile: MatchProfile,
) -> None:
    db.delete(profile)
    db.commit()