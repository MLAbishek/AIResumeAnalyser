import pytest

from app.core.schemas import (
    CanonicalJob,
    CanonicalResume,
)
from app.ranking.semantic_scorer import (
    score_semantic,
    score_vector_similarity,
)


def test_semantic_score_is_normalized():
    job = CanonicalJob(
        job_id="J1",
        title="Python Machine Learning Engineer",
        description="Build machine learning systems",
    )

    resume = CanonicalResume(
        resume_id="R1",
        summary="Python machine learning engineer",
        skills=[
            "Python",
            "Machine Learning",
        ],
    )

    score = score_semantic(
        job,
        resume,
    )

    assert 0.0 <= score <= 1.0


def test_identical_vectors():
    assert score_vector_similarity(
        [1.0, 0.0, 1.0],
        [1.0, 0.0, 1.0],
    ) == 1.0


def test_opposite_vectors():
    assert score_vector_similarity(
        [1.0, 0.0],
        [-1.0, 0.0],
    ) == 0.0


def test_vector_dimension_mismatch():
    with pytest.raises(ValueError):
        score_vector_similarity(
            [1.0, 0.0],
            [1.0],
        )