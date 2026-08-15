from app.core.schemas import (
    CanonicalEducation,
    CanonicalJob,
    CanonicalJobEducationRequirement,
    CanonicalResume,
)
from app.ranking.education_scorer import score_education


def test_matching_education():
    job = CanonicalJob(
        job_id="J1",
        education=[
            CanonicalJobEducationRequirement(
                degree="B.Tech",
                field_of_study="Computer Science",
                required=True,
            )
        ],
    )

    resume = CanonicalResume(
        resume_id="R1",
        education=[
            CanonicalEducation(
                degree="B.Tech",
                institution="ABC University",
                field_of_study="Computer Science",
            )
        ],
    )

    assert score_education(
        job,
        resume,
    ) == 1.0


def test_missing_required_education():
    job = CanonicalJob(
        job_id="J1",
        education=[
            CanonicalJobEducationRequirement(
                degree="B.Tech",
                field_of_study="Computer Science",
                required=True,
            )
        ],
    )

    resume = CanonicalResume(
        resume_id="R1",
    )

    assert score_education(
        job,
        resume,
    ) == 0.0


def test_no_education_requirement():
    job = CanonicalJob(
        job_id="J1",
    )

    resume = CanonicalResume(
        resume_id="R1",
    )

    assert score_education(
        job,
        resume,
    ) == 1.0