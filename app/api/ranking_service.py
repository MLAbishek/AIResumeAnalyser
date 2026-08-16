from app.api.repository import InMemoryRepository
from app.api.schemas import (
    CandidateRankingResponse,
    RankedCandidateResponse,
)
from app.ranking.scoring_engine import rank_candidates


class CandidateRankingService:
    """
    Module 46.

    Returns deterministic candidate rankings using the
    existing ranking engine.
    """

    def __init__(
        self,
        repository: InMemoryRepository,
    ):
        self.repository = repository

    def rank(
        self,
        jd_id: str,
        candidate_ids: list[str],
    ) -> CandidateRankingResponse:

        if not candidate_ids:
            return CandidateRankingResponse(
                jd_id=jd_id,
                total_candidates=0,
                ranked_candidates=[],
            )

        job = self.repository.get_job(jd_id)

        candidates = self.repository.get_resumes(
            candidate_ids
        )

        scores = rank_candidates(
            job,
            candidates,
        )

        ranked_candidates = []

        for rank, result in enumerate(scores, start=1):
            ranked_candidates.append(
                RankedCandidateResponse(
                    candidate_id=result.resume_id,
                    rank=rank,
                    score=result.score,
                    skill_score=result.features.skill_score,
                    experience_score=result.features.experience_score,
                    seniority_score=result.features.seniority_score,
                    education_score=result.features.education_score,
                    semantic_score=result.features.semantic_score,
                )
            )

        return CandidateRankingResponse(
            jd_id=jd_id,
            total_candidates=len(ranked_candidates),
            ranked_candidates=ranked_candidates,
        )