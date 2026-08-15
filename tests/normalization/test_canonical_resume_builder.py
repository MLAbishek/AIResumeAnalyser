from datetime import date

import pytest

from app.core.schemas import CanonicalResume
from app.normalization.canonical_resume_builder import (
    CanonicalResumeBuilder,
)


@pytest.fixture
def builder():
    return CanonicalResumeBuilder()


def test_build_canonical_resume(builder):
    parsed_resume = {
        "resume_id": "resume_001",
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "summary": "Software developer with ML experience.",
        "skills": [
            "Python",
            "PyTorch",
            "Py Torch",
            "ReactJS",
            "AWS",
        ],
        "job_titles": [
            "SWE",
            "Software Developer",
        ],
        "organizations": [
            "Google Inc",
            "Google",
        ],
        "technologies": [
            "ReactJS",
            "Postgres",
            "K8s",
        ],
        "experiences": [
            {
                "job_title": "Software Developer",
                "company": "Google Inc",
                "start_date": "January 2020",
                "end_date": "March 2022",
            }
        ],
        "education": [
            {
                "degree": "B.Tech",
                "institution": "ABC University",
                "field_of_study": "Computer Science",
                "start_date": "2016",
                "end_date": "2020",
            }
        ],
    }

    result = builder.build(parsed_resume)

    assert isinstance(result, CanonicalResume)

    assert result.resume_id == "resume_001"

    assert result.skills == [
        "python",
        "pytorch",
        "react",
        "aws",
    ]

    assert result.job_titles == [
        "software engineer",
    ]

    assert result.organizations == [
        "google",
    ]

    assert result.technologies == [
        "react",
        "postgresql",
        "kubernetes",
    ]


def test_experience_is_normalized(builder):
    parsed_resume = {
        "resume_id": "resume_002",
        "experiences": [
            {
                "job_title": "SWE",
                "company": "Microsoft Corporation",
                "start_date": "January 2020",
                "end_date": "March 2022",
            }
        ],
    }

    result = builder.build(parsed_resume)

    experience = result.experiences[0]

    assert experience.job_title == "software engineer"
    assert experience.company == "microsoft"

    assert experience.start_date == date(
        2020,
        1,
        1,
    )

    assert experience.end_date == date(
        2022,
        3,
        1,
    )

    assert experience.duration_months == 26


def test_total_experience_is_calculated(builder):
    parsed_resume = {
        "resume_id": "resume_003",
        "experiences": [
            {
                "job_title": "SWE",
                "company": "Google",
                "start_date": "January 2020",
                "end_date": "January 2022",
            },
            {
                "job_title": "ML Engineer",
                "company": "Microsoft",
                "start_date": "February 2022",
                "end_date": "February 2024",
            },
        ],
    }

    result = builder.build(parsed_resume)

    assert result.total_experience_months == 48


def test_duplicate_skills_are_removed(builder):
    parsed_resume = {
        "resume_id": "resume_004",
        "skills": [
            "Python",
            "python",
            "PYTHON",
            "PyTorch",
            "Py Torch",
        ],
    }

    result = builder.build(parsed_resume)

    assert result.skills == [
        "python",
        "pytorch",
    ]


def test_empty_optional_fields(builder):
    parsed_resume = {
        "resume_id": "resume_005",
    }

    result = builder.build(parsed_resume)

    assert result.name is None
    assert result.email is None
    assert result.skills == []
    assert result.job_titles == []
    assert result.organizations == []
    assert result.technologies == []
    assert result.experiences == []
    assert result.education == []
    assert result.total_experience_months == 0


def test_missing_resume_id_is_rejected(builder):
    with pytest.raises(ValueError):
        builder.build({
            "skills": ["Python"],
        })


def test_builder_is_deterministic(builder):
    parsed_resume = {
        "resume_id": "resume_006",
        "skills": [
            "PyTorch",
            "Python",
            "ReactJS",
        ],
        "job_titles": [
            "SWE",
        ],
    }

    first = builder.build(parsed_resume)
    second = builder.build(parsed_resume)

    assert first == second