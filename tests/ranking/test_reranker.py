from app.core.schemas import (
    CanonicalJob,
    CanonicalResume,
)
from app.ranking.reranker import rerank_candidates


def test_empty_candidates():
    job = CanonicalJob(
        job_id="J1",
    )

    assert rerank_candidates(
        job,
        [],
    ) == []


def test_deterministic_fallback():
    job = CanonicalJob(
        job_id="J1",
        required_skills=["Python"],
    )

    strong = CanonicalResume(
        resume_id="R1",
        skills=["Python"],
    )

    weak = CanonicalResume(
        resume_id="R2",
        skills=["Java"],
    )

    result = rerank_candidates(
        job,
        [weak, strong],
    )

    assert result[0].resume_id == "R1"
    assert result[1].resume_id == "R2"


def test_top_n_limits_candidates():
    job = CanonicalJob(
        job_id="J1",
    )

    candidates = [
        CanonicalResume(resume_id="R1"),
        CanonicalResume(resume_id="R2"),
        CanonicalResume(resume_id="R3"),
    ]

    result = rerank_candidates(
        job,
        candidates,
        top_n=2,
    )

    assert len(result) == 2


def test_custom_reranker_is_used():
    job = CanonicalJob(
        job_id="J1",
    )

    candidates = [
        CanonicalResume(resume_id="R1"),
        CanonicalResume(resume_id="R2"),
    ]

    def custom_reranker(job, candidates):
        return list(reversed(candidates))

    result = rerank_candidates(
        job,
        candidates,
        reranker=custom_reranker,
    )

    assert result[0].resume_id == "R2"
    assert result[1].resume_id == "R1"