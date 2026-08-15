from app.core.schemas import (
    CanonicalJob,
    CanonicalJobExperienceRequirement,
    CanonicalResume,
)
from app.ranking.experience_scorer import score_experience


def test_candidate_meets_experience_requirement():
    job = CanonicalJob(
        job_id="J1",
        experience=CanonicalJobExperienceRequirement(
            minimum_months=36,
        ),
    )

    resume = CanonicalResume(
        resume_id="R1",
        total_experience_months=48,
    )

    assert score_experience(
        job,
        resume,
    ) == 1.0


def test_candidate_partially_meets_experience_requirement():
    job = CanonicalJob(
        job_id="J1",
        experience=CanonicalJobExperienceRequirement(
            minimum_months=48,
        ),
    )

    resume = CanonicalResume(
        resume_id="R1",
        total_experience_months=24,
    )

    assert score_experience(
        job,
        resume,
    ) == 0.5


def test_zero_experience_requirement():
    job = CanonicalJob(
        job_id="J1",
        experience=CanonicalJobExperienceRequirement(
            minimum_months=0,
        ),
    )

    resume = CanonicalResume(
        resume_id="R1",
        total_experience_months=0,
    )

    assert score_experience(
        job,
        resume,
    ) == 1.0