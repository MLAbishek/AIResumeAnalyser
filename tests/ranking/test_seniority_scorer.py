from app.core.schemas import (
    CanonicalJob,
    CanonicalResume,
)
from app.ranking.seniority_scorer import score_seniority


def test_matching_seniority_and_role():
    job = CanonicalJob(
        job_id="J1",
        title="Senior Python Engineer",
    )

    resume = CanonicalResume(
        resume_id="R1",
        job_titles=[
            "Senior Python Engineer",
        ],
    )

    assert score_seniority(
        job,
        resume,
    ) == 1.0


def test_no_candidate_titles():
    job = CanonicalJob(
        job_id="J1",
        title="Senior Python Engineer",
    )

    resume = CanonicalResume(
        resume_id="R1",
    )

    assert score_seniority(
        job,
        resume,
    ) == 0.0