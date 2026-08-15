from pydantic import BaseModel, Field

from app.core.schemas import CanonicalJob, CanonicalResume
from app.ranking.feature_extraction import (
    MatchFeatureVector,
    extract_features,
)


class CandidateScore(BaseModel):
    """
    Final deterministic score for one candidate.
    """

    resume_id: str
    score: float = Field(ge=0.0, le=1.0)
    features: MatchFeatureVector


DEFAULT_WEIGHTS = {
    "skill": 0.35,
    "experience": 0.20,
    "seniority": 0.15,
    "education": 0.10,
    "semantic": 0.20,
}


def validate_weights(weights: dict[str, float]) -> None:
    """
    Validate that all ranking weights are present,
    non-negative, and sum to 1.
    """

    required = set(DEFAULT_WEIGHTS)

    if set(weights) != required:
        raise ValueError(
            f"Weights must contain exactly: {sorted(required)}"
        )

    if any(weight < 0 for weight in weights.values()):
        raise ValueError(
            "Weights cannot be negative."
        )

    total = sum(weights.values())

    if abs(total - 1.0) > 1e-6:
        raise ValueError(
            f"Weights must sum to 1.0, got {total}."
        )


def calculate_candidate_score(
    job: CanonicalJob,
    resume: CanonicalResume,
    weights: dict[str, float] | None = None,
) -> CandidateScore:
    """
    Combine all matching features into one deterministic score.
    """

    weights = weights or DEFAULT_WEIGHTS

    validate_weights(weights)

    features = extract_features(
        job,
        resume,
    )

    score = (
        weights["skill"] * features.skill_score
        + weights["experience"] * features.experience_score
        + weights["seniority"] * features.seniority_score
        + weights["education"] * features.education_score
        + weights["semantic"] * features.semantic_score
    )

    return CandidateScore(
        resume_id=resume.resume_id,
        score=round(score, 4),
        features=features,
    )


def rank_candidates(
    job: CanonicalJob,
    resumes: list[CanonicalResume],
    weights: dict[str, float] | None = None,
) -> list[CandidateScore]:
    """
    Rank candidates from highest score to lowest score.

    resume_id is used as a deterministic tie-breaker.
    """

    results = [
        calculate_candidate_score(
            job,
            resume,
            weights,
        )
        for resume in resumes
    ]

    return sorted(
        results,
        key=lambda result: (
            -result.score,
            result.resume_id,
        ),
    )