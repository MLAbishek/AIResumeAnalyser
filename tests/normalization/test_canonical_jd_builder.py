import pytest

from app.core.schemas import CanonicalJob
from app.normalization.canonical_jd_builder import (
    CanonicalJobBuilder,
)


@pytest.fixture
def builder():
    return CanonicalJobBuilder()


def test_build_canonical_job(builder):
    parsed_jd = {
        "job_id": "jd_001",
        "title": "Software Developer",
        "description": "Build machine learning systems.",
        "required_skills": [
            "Python",
            "PyTorch",
            "Py Torch",
            "ReactJS",
        ],
        "preferred_skills": [
            "Docker",
            "K8s",
        ],
        "required_technologies": [
            "Postgres",
            "AWS",
        ],
        "preferred_technologies": [
            "Kubernetes",
        ],
        "organizations": [
            "Google Inc",
            "Google",
        ],
        "experience": {
            "minimum_months": 36,
        },
        "education": [
            {
                "degree": "B.Tech",
                "field_of_study": "Computer Science",
                "required": True,
            }
        ],
    }

    result = builder.build(parsed_jd)

    assert isinstance(result, CanonicalJob)

    assert result.job_id == "jd_001"

    assert result.title == "software engineer"

    assert result.required_skills == [
        "python",
        "pytorch",
        "react",
    ]

    assert result.preferred_skills == [
        "docker",
        "kubernetes",
    ]

    assert result.required_technologies == [
        "postgresql",
        "aws",
    ]

    assert result.preferred_technologies == [
        "kubernetes",
    ]

    assert result.organizations == [
        "google",
    ]


def test_experience_requirement(builder):
    parsed_jd = {
        "job_id": "jd_002",
        "title": "SWE",
        "experience": {
            "minimum_months": 36,
            "maximum_months": 60,
        },
    }

    result = builder.build(parsed_jd)

    assert result.experience.minimum_months == 36
    assert result.experience.maximum_months == 60


def test_default_experience_requirement(builder):
    parsed_jd = {
        "job_id": "jd_003",
        "title": "Software Engineer",
    }

    result = builder.build(parsed_jd)

    assert result.experience.minimum_months == 0
    assert result.experience.maximum_months is None


def test_education_requirement(builder):
    parsed_jd = {
        "job_id": "jd_004",
        "education": [
            {
                "degree": "B.Tech",
                "field_of_study": "Computer Science",
                "required": True,
            },
            {
                "degree": "M.Tech",
                "field_of_study": "Artificial Intelligence",
                "required": False,
            },
        ],
    }

    result = builder.build(parsed_jd)

    assert len(result.education) == 2

    assert result.education[0].degree == "b.tech"
    assert result.education[0].field_of_study == (
        "computer science"
    )
    assert result.education[0].required is True

    assert result.education[1].degree == "m.tech"
    assert result.education[1].field_of_study == (
        "artificial intelligence"
    )
    assert result.education[1].required is False


def test_duplicate_requirements_are_removed(builder):
    parsed_jd = {
        "job_id": "jd_005",
        "required_skills": [
            "Python",
            "python",
            "PYTHON",
            "PyTorch",
            "Py Torch",
        ],
        "required_technologies": [
            "AWS",
            "Amazon Web Services",
            "K8s",
            "Kubernetes",
        ],
    }

    result = builder.build(parsed_jd)

    assert result.required_skills == [
        "python",
        "pytorch",
    ]

    assert result.required_technologies == [
        "aws",
        "kubernetes",
    ]


def test_empty_optional_fields(builder):
    parsed_jd = {
        "job_id": "jd_006",
    }

    result = builder.build(parsed_jd)

    assert result.title is None
    assert result.description is None

    assert result.required_skills == []
    assert result.preferred_skills == []

    assert result.required_technologies == []
    assert result.preferred_technologies == []

    assert result.organizations == []

    assert result.experience.minimum_months == 0
    assert result.experience.maximum_months is None

    assert result.education == []


def test_missing_job_id_is_rejected(builder):
    with pytest.raises(ValueError):
        builder.build({
            "title": "Software Engineer",
        })


def test_invalid_experience_range_is_rejected(builder):
    with pytest.raises(ValueError):
        builder.build({
            "job_id": "jd_007",
            "experience": {
                "minimum_months": 60,
                "maximum_months": 36,
            },
        })


def test_negative_experience_is_rejected(builder):
    with pytest.raises(ValueError):
        builder.build({
            "job_id": "jd_008",
            "experience": {
                "minimum_months": -1,
            },
        })


def test_builder_is_deterministic(builder):
    parsed_jd = {
        "job_id": "jd_009",
        "title": "SWE",
        "required_skills": [
            "Python",
            "PyTorch",
        ],
        "required_technologies": [
            "AWS",
        ],
    }

    first = builder.build(parsed_jd)
    second = builder.build(parsed_jd)

    assert first == second