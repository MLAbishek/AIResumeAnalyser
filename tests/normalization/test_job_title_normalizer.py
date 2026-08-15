import pytest

from app.normalization.job_title_normalizer import JobTitleNormalizer


@pytest.fixture
def normalizer():
    return JobTitleNormalizer()


def test_software_engineer_variants(normalizer):
    assert normalizer.normalize("SWE") == "software engineer"
    assert normalizer.normalize("Software Engineer") == "software engineer"
    assert normalizer.normalize("Software Developer") == "software engineer"


def test_senior_software_engineer(normalizer):
    assert (
        normalizer.normalize("Senior Software Developer")
        == "senior software engineer"
    )

    assert (
        normalizer.normalize("Senior SWE")
        == "senior software engineer"
    )


def test_full_stack_variants(normalizer):
    assert (
        normalizer.normalize("Full Stack Developer")
        == "full stack developer"
    )

    assert (
        normalizer.normalize("Full-Stack Engineer")
        == "full stack developer"
    )


def test_frontend_variants(normalizer):
    assert (
        normalizer.normalize("Frontend Developer")
        == "frontend developer"
    )

    assert (
        normalizer.normalize("Front End Engineer")
        == "frontend developer"
    )


def test_backend_variants(normalizer):
    assert (
        normalizer.normalize("Backend Engineer")
        == "backend developer"
    )


def test_ml_variants(normalizer):
    assert (
        normalizer.normalize("ML Engineer")
        == "machine learning engineer"
    )

    assert (
        normalizer.normalize("Machine Learning Developer")
        == "machine learning engineer"
    )


def test_unknown_title_is_preserved(normalizer):
    assert normalizer.normalize("Robotics Researcher") == "robotics researcher"


def test_multiple_titles(normalizer):
    titles = [
        "SWE",
        "Software Engineer",
        "Software Developer",
        "ML Engineer",
    ]

    result = normalizer.normalize_many(titles)

    assert result == [
        "software engineer",
        "machine learning engineer",
    ]


def test_case_normalization(normalizer):
    assert normalizer.normalize("SOFTWARE ENGINEER") == "software engineer"


def test_whitespace(normalizer):
    assert normalizer.normalize("  SWE  ") == "software engineer"