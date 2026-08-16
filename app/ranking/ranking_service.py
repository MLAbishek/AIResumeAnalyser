from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.crud.ranking_results import (
    create_ranking_result,
    get_ranking_by_screening_id,
    update_ranking_result,
)
from app.database.models.job import Job
from app.database.models.screening import ScreeningResult
from app.ranking.database_adapter import (
    job_to_canonical,
    resume_to_canonical,
)
from app.ranking.scoring_engine import rank_candidates


def rank_job_candidates(
    db: Session,
    *,
    job_id: str,
):
    """
    Rank all eligible candidates for a job.

    Database transaction is owned by this service.
    """

    job = db.scalar(
        select(Job).where(
            Job.job_id == job_id
        )
    )

    if job is None:
        raise ValueError(
            f"Job '{job_id}' not found."
        )

    screenings = db.scalars(
        select(ScreeningResult)
        .where(
            ScreeningResult.job_id == job.id,
            ScreeningResult.eligible.is_(True),
        )
        .options(
            selectinload(ScreeningResult.resume)
        )
    ).all()

    if not screenings:
        return []

    canonical_job = job_to_canonical(job)

    candidates = [
        resume_to_canonical(
            screening.resume
        )
        for screening in screenings
    ]

    scores = rank_candidates(
        canonical_job,
        candidates,
    )

    screening_by_resume_id = {
        screening.resume.resume_id: screening
        for screening in screenings
    }

    results = []

    try:
        for rank, candidate_score in enumerate(
            scores,
            start=1,
        ):
            screening = screening_by_resume_id[
                candidate_score.resume_id
            ]

            features = candidate_score.features

            ranking = get_ranking_by_screening_id(
                db,
                screening.id,
            )

            if ranking is None:
                ranking = create_ranking_result(
                    db,
                    screening_id=screening.id,
                    rank=rank,
                    score=candidate_score.score,
                    skill_score=features.skill_score,
                    experience_score=(
                        features.experience_score
                    ),
                    seniority_score=(
                        features.seniority_score
                    ),
                    education_score=(
                        features.education_score
                    ),
                    semantic_score=(
                        features.semantic_score
                    ),
                )
            else:
                ranking = update_ranking_result(
                    db,
                    ranking,
                    rank=rank,
                    score=candidate_score.score,
                    skill_score=features.skill_score,
                    experience_score=(
                        features.experience_score
                    ),
                    seniority_score=(
                        features.seniority_score
                    ),
                    education_score=(
                        features.education_score
                    ),
                    semantic_score=(
                        features.semantic_score
                    ),
                )

            results.append(ranking)

        db.commit()

        for ranking in results:
            db.refresh(ranking)

        return results

    except Exception:
        db.rollback()
        raise