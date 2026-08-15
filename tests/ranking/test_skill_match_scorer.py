from app.core.schemas import (
    CanonicalJob,
    CanonicalResume,
)
from app.ranking.skill_match_scorer import score_skills


def test_required_skill_match():
    job = CanonicalJob(
        job_id="J1",
        required_skills=[
            "Python",
            "SQL",
        ],
    )

    resume = CanonicalResume(
        resume_id="R1",
        skills=[
            "Python",
            "SQL",
        ],
    )

    assert score_skills(job, resume) == 1.0


def test_partial_required_skill_match():
    job = CanonicalJob(
        job_id="J1",
        required_skills=[
            "Python",
            "SQL",
        ],
    )

    resume = CanonicalResume(
        resume_id="R1",
        skills=["Python"],
    )

    assert score_skills(job, resume) == 0.5


def test_no_skill_requirements():
    job = CanonicalJob(
        job_id="J1",
    )

    resume = CanonicalResume(
        resume_id="R1",
        skills=["Python"],
    )

    assert score_skills(job, resume) == 1.0