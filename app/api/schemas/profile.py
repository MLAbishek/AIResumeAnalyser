from typing import Any

from pydantic import BaseModel, Field


class CandidateProfileResponse(BaseModel):
    candidate_id: str
    jd_id: str

    ranking_score: float

    feature_scores: dict[str, float] = Field(
        default_factory=dict
    )

    matched_skills: list[str] = Field(
        default_factory=list
    )

    missing_skills: list[str] = Field(
        default_factory=list
    )

    experience_gap: dict[str, Any] = Field(
        default_factory=dict
    )

    education_gap: dict[str, Any] = Field(
        default_factory=dict
    )

    certification_gap: dict[str, Any] = Field(
        default_factory=dict
    )

    evidence: list[dict[str, Any]] = Field(
        default_factory=list
    )

    decision: str

    explanation: dict[str, Any] = Field(
        default_factory=dict
    )