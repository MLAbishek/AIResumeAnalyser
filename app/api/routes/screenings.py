from typing import Any

from pydantic import BaseModel
from app.auth.dependencies import require_role
from fastapi import APIRouter, Depends, HTTPException

class ScreeningResultResponse(BaseModel):
    screening_id: int
    job_id: str
    resume_id: str
    candidate_name: str | None = None

    eligible: bool
    decision: str | None
    final_score: float | None
    decision_reason: str | None

    ranking: dict[str, Any] | None = None
    gap_analysis: dict[str, Any] | None = None
    explanation: dict[str, Any] | None = None
    evidence: list[dict[str, Any]] = []


class ScreeningListResponse(BaseModel):
    job_id: str
    total_candidates: int
    results: list[ScreeningResultResponse]


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.api.dependencies import get_db
from app.api.schemas.screenings import (
    ScreeningListResponse,
    ScreeningResultResponse,
)
from app.database.crud.jobs import get_job_by_id
from app.database.models.profile import MatchProfile
from app.database.models.screening import ScreeningResult


router = APIRouter(
    prefix="/screenings",
    tags=["screenings"],
)


def _to_response(
    screening: ScreeningResult,
) -> ScreeningResultResponse:

    ranking = None

    if screening.ranking is not None:
        ranking = {
            "rank": screening.ranking.rank,
            "score": screening.ranking.score,
            "skill_score": screening.ranking.skill_score,
            "experience_score": (
                screening.ranking.experience_score
            ),
            "seniority_score": (
                screening.ranking.seniority_score
            ),
            "education_score": (
                screening.ranking.education_score
            ),
            "semantic_score": (
                screening.ranking.semantic_score
            ),
        }

    profile = screening.profile

    evidence = []

    if profile is not None:
        evidence = [
            {
                "id": reference.id,
                "claim": reference.claim,
                "source": reference.source,
                "section": reference.section,
                "evidence": reference.evidence,
            }
            for reference in profile.evidence
        ]

    return ScreeningResultResponse(
        screening_id=screening.id,
        job_id=screening.job.job_id,
        resume_id=screening.resume.resume_id,
        candidate_name=screening.resume.name,
        eligible=screening.eligible,
        decision=screening.decision,
        final_score=screening.final_score,
        decision_reason=screening.decision_reason,
        ranking=ranking,
        gap_analysis=(
            profile.gap_analysis
            if profile is not None
            else None
        ),
        explanation=(
            profile.explanation
            if profile is not None
            else None
        ),
        evidence=evidence,
    )

@router.get(
    "/{job_id}/{resume_id}",
    response_model=ScreeningResultResponse,
    dependencies=[
        Depends(require_role("admin", "recruiter", "viewer"))
    ],
)
def get_screening(
    job_id: str,
    resume_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(
        require_role("admin","recruiter","viewer")
    ),
):
    job = get_job_by_id(
        db,
        job_id,
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found.",
        )

    screening = (
        db.query(ScreeningResult)
        .options(
            selectinload(ScreeningResult.job),
            selectinload(ScreeningResult.resume),
            selectinload(ScreeningResult.ranking),
            selectinload(
                ScreeningResult.profile
            ).selectinload(
                MatchProfile.evidence
            ),
        )
        .filter(
            ScreeningResult.job_id == job.id,
            ScreeningResult.resume.has(
                resume_id=resume_id
            ),
        )
        .first()
    )

    if screening is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Screening result not found for "
                f"job '{job_id}' and resume '{resume_id}'."
            ),
        )

    return _to_response(screening)

@router.get(
    "/{job_id}",
    response_model=ScreeningListResponse,
    dependencies=[
        Depends(require_role("admin", "recruiter", "viewer"))
    ],
)
def list_screenings(
    job_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(
        require_role("admin","recruiter","viewer")
    ),
):
    job = get_job_by_id(
        db,
        job_id,
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found.",
        )

    screenings = (
        db.query(ScreeningResult)
        .options(
            selectinload(ScreeningResult.job),
            selectinload(ScreeningResult.resume),
            selectinload(ScreeningResult.ranking),
            selectinload(
                ScreeningResult.profile
            ).selectinload(
                MatchProfile.evidence
            ),
        )
        .filter(
            ScreeningResult.job_id == job.id
        )
        .order_by(
            ScreeningResult.final_score.desc().nullslast(),
            ScreeningResult.resume_id,
        )
        .all()
    )

    return ScreeningListResponse(
        job_id=job_id,
        total_candidates=len(screenings),
        results=[
            _to_response(screening)
            for screening in screenings
        ],
    )