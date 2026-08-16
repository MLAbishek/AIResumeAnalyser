from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.screening import ScreeningResult


def create_screening_result(
    db: Session,
    *,
    job_id: int,
    resume_id: int,
    eligible: bool,
    eligibility_details: dict,
    decision: str | None = None,
    final_score: float | None = None,
    decision_reason: str | None = None,
) -> ScreeningResult:
    result = ScreeningResult(
        job_id=job_id,
        resume_id=resume_id,
        eligible=eligible,
        eligibility_details=eligibility_details,
        decision=decision,
        final_score=final_score,
        decision_reason=decision_reason,
    )

    db.add(result)
    db.flush()
    db.refresh(result)

    return result


def get_screening_result(
    db: Session,
    *,
    job_id: int,
    resume_id: int,
) -> ScreeningResult | None:
    statement = select(ScreeningResult).where(
        ScreeningResult.job_id == job_id,
        ScreeningResult.resume_id == resume_id,
    )

    return db.scalar(statement)


def get_screening_by_id(
    db: Session,
    screening_id: int,
) -> ScreeningResult | None:
    return db.get(ScreeningResult, screening_id)


def list_screening_results_for_job(
    db: Session,
    job_id: int,
) -> list[ScreeningResult]:
    statement = (
        select(ScreeningResult)
        .where(ScreeningResult.job_id == job_id)
        .order_by(
            ScreeningResult.final_score.desc().nullslast(),
            ScreeningResult.resume_id,
        )
    )

    return list(db.scalars(statement).all())


def update_screening_result(
    db: Session,
    screening: ScreeningResult,
    *,
    eligible: bool | None = None,
    eligibility_details: dict | None = None,
    decision: str | None = None,
    final_score: float | None = None,
    decision_reason: str | None = None,
) -> ScreeningResult:
    if eligible is not None:
        screening.eligible = eligible

    if eligibility_details is not None:
        screening.eligibility_details = eligibility_details

    if decision is not None:
        screening.decision = decision

    if final_score is not None:
        screening.final_score = final_score

    if decision_reason is not None:
        screening.decision_reason = decision_reason

    db.commit()
    db.refresh(screening)

    return screening


def delete_screening_result(
    db: Session,
    screening: ScreeningResult,
) -> None:
    db.delete(screening)
    db.commit()