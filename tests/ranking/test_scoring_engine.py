import pytest

from app.core.schemas import (
    CanonicalJob,
    CanonicalResume,
)
from app.ranking.scoring_engine import (
    calculate_candidate_score,
    rank_candidates,
)


def test_candidate_score_is_between_zero_and_one():
    job = CanonicalJob(
        job_id="J1",
        title="Python Engineer",
        required_skills=["Python"],
    )

    resume = CanonicalResume(
        resume_id="R1",
        skills=["Python"],
        job_titles=["Python Engineer"],
    )

    result = calculate_candidate_score(
        job,
        resume,
    )

    assert 0.0 <= result.score <= 1.0
    assert result.resume_id == "R1"


def test_invalid_weights_are_rejected():
    job = CanonicalJob(
        job_id="J1",
    )

    resume = CanonicalResume(
        resume_id="R1",
    )

    with pytest.raises(ValueError):
        calculate_candidate_score(
            job,
            resume,
            weights={
                "skill": 0.5,
                "experience": 0.5,
                "seniority": 0.0,
                "education": 0.0,
                "semantic": 0.5,
            },
        )


def test_candidates_are_ranked_highest_first():
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

    results = rank_candidates(
        job,
        [weak, strong],
    )

    assert results[0].resume_id == "R1"
    assert results[1].resume_id == "R2"


def test_ranking_is_deterministic_for_ties():
    job = CanonicalJob(
        job_id="J1",
    )

    resume_b = CanonicalResume(
        resume_id="B",
    )

    resume_a = CanonicalResume(
        resume_id="A",
    )

    results = rank_candidates(
        job,
        [resume_b, resume_a],
    )

    assert [
        result.resume_id
        for result in results
    ] == ["A", "B"]