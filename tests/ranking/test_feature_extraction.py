from app.core.schemas import (
    CanonicalJob,
    CanonicalResume,
)
from app.ranking.feature_extraction import extract_features


def test_feature_extraction_returns_all_features():
    job = CanonicalJob(
        job_id="J1",
        title="Senior Python Engineer",
        required_skills=["Python"],
        preferred_skills=["Docker"],
    )

    resume = CanonicalResume(
        resume_id="R1",
        skills=["Python", "Docker"],
        job_titles=["Senior Python Engineer"],
    )

    features = extract_features(
        job,
        resume,
    )

    assert 0.0 <= features.skill_score <= 1.0
    assert 0.0 <= features.experience_score <= 1.0
    assert 0.0 <= features.seniority_score <= 1.0
    assert 0.0 <= features.education_score <= 1.0
    assert 0.0 <= features.semantic_score <= 1.0