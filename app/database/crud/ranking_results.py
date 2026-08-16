from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.ranking import RankingResult


def create_ranking_result(
    db: Session,
    *,
    screening_id: int,
    rank: int | None,
    score: float,
    skill_score: float,
    experience_score: float,
    seniority_score: float,
    education_score: float,
    semantic_score: float,
) -> RankingResult:

    ranking = RankingResult(
        screening_id=screening_id,
        rank=rank,
        score=score,
        skill_score=skill_score,
        experience_score=experience_score,
        seniority_score=seniority_score,
        education_score=education_score,
        semantic_score=semantic_score,
    )

    db.add(ranking)
    db.flush()
    db.refresh(ranking)

    return ranking


def get_ranking_by_id(
    db: Session,
    ranking_id: int,
) -> RankingResult | None:
    return db.get(
        RankingResult,
        ranking_id,
    )


def get_ranking_by_screening_id(
    db: Session,
    screening_id: int,
) -> RankingResult | None:

    statement = select(RankingResult).where(
        RankingResult.screening_id == screening_id
    )

    return db.scalar(statement)


def update_ranking_result(
    db: Session,
    ranking: RankingResult,
    *,
    rank: int | None = None,
    score: float | None = None,
    skill_score: float | None = None,
    experience_score: float | None = None,
    seniority_score: float | None = None,
    education_score: float | None = None,
    semantic_score: float | None = None,
) -> RankingResult:

    if rank is not None:
        ranking.rank = rank

    if score is not None:
        ranking.score = score

    if skill_score is not None:
        ranking.skill_score = skill_score

    if experience_score is not None:
        ranking.experience_score = experience_score

    if seniority_score is not None:
        ranking.seniority_score = seniority_score

    if education_score is not None:
        ranking.education_score = education_score

    if semantic_score is not None:
        ranking.semantic_score = semantic_score

    db.flush()
    db.refresh(ranking)

    return ranking


def delete_ranking_result(
    db: Session,
    ranking: RankingResult,
) -> None:
    db.delete(ranking)
    db.flush()

def update_rank(
    db: Session,
    ranking: RankingResult,
    *,
    rank: int,
) -> RankingResult:
    ranking.rank = rank

    db.flush()
    db.refresh(ranking)

    return ranking