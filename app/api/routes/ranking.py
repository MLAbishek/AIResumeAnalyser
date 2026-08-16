from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.ranking.ranking_service import rank_job_candidates
from app.auth.dependencies import require_role

router = APIRouter(
    prefix="/ranking",
    tags=["ranking"],
)


@router.post(
    "/{job_id}",dependencies=[
        Depends(require_role("admin", "recruiter"))
    ],)
def rank_candidates_for_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(
        require_role("admin","recruiter")
    )
):
    try:
        results = rank_job_candidates(
            db,
            job_id=job_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return {
        "job_id": job_id,
        "count": len(results),
        "results": [
            {
                "screening_id": result.screening_id,
                "rank": result.rank,
                "score": result.score,
                "skill_score": result.skill_score,
                "experience_score": (
                    result.experience_score
                ),
                "seniority_score": (
                    result.seniority_score
                ),
                "education_score": (
                    result.education_score
                ),
                "semantic_score": (
                    result.semantic_score
                ),
            }
            for result in results
        ],
    }