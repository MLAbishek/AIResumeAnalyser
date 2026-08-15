import pytest

from app.normalization.skill_normalizer import SkillNormalizer


@pytest.fixture
def normalizer():
    return SkillNormalizer()


def test_pytorch_variants(normalizer):
    assert normalizer.normalize("PyTorch") == "pytorch"
    assert normalizer.normalize("Py Torch") == "pytorch"
    assert normalizer.normalize("py-torch") == "pytorch"


def test_python_variants(normalizer):
    assert normalizer.normalize("Python") == "python"
    assert normalizer.normalize("PYTHON") == "python"
    assert normalizer.normalize("python3") == "python"


def test_react_variants(normalizer):
    assert normalizer.normalize("React") == "react"
    assert normalizer.normalize("ReactJS") == "react"
    assert normalizer.normalize("React.js") == "react"


def test_database_variants(normalizer):
    assert normalizer.normalize("Postgres") == "postgresql"
    assert normalizer.normalize("PostgreSQL") == "postgresql"
    assert normalizer.normalize("Mongo DB") == "mongodb"


def test_cloud_variants(normalizer):
    assert normalizer.normalize("Amazon Web Services") == "aws"
    assert normalizer.normalize("AWS") == "aws"
    assert normalizer.normalize("Google Cloud Platform") == "gcp"


def test_unknown_skill_is_preserved(normalizer):
    assert normalizer.normalize("LangChain") == "langchain"


def test_multiple_skills(normalizer):
    skills = [
        "Python",
        "PYTHON",
        "PyTorch",
        "Py Torch",
        "ReactJS",
    ]

    result = normalizer.normalize_many(skills)

    assert result == [
        "python",
        "pytorch",
        "react",
    ]


def test_empty_skill(normalizer):
    assert normalizer.normalize("") == ""


def test_whitespace(normalizer):
    assert normalizer.normalize("  PyTorch  ") == "pytorch"