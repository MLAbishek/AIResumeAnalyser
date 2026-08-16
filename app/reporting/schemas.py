from pydantic import BaseModel, Field


class CandidateReport(BaseModel):
    resume_id: str
    candidate_name: str | None = None

    decision: str
    decision_reason: str

    eligible: bool

    ranking_score: float = Field(
        ge=0.0,
        le=100.0,
    )

    summary: str

    strengths: list[str] = Field(
        default_factory=list
    )

    gaps: list[str] = Field(
        default_factory=list
    )

    matched_skills: list[str] = Field(
        default_factory=list
    )

    missing_skills: list[str] = Field(
        default_factory=list
    )

    evidence: list[dict] = Field(
        default_factory=list
    )


class ScreeningReport(BaseModel):
    job_id: str

    total_candidates: int = Field(
        ge=0
    )

    eligible_candidates: int = Field(
        ge=0
    )

    shortlisted_candidates: int = Field(
        ge=0
    )

    review_candidates: int = Field(
        ge=0
    )

    rejected_candidates: int = Field(
        ge=0
    )

    candidates: list[CandidateReport] = Field(
        default_factory=list
    )

    markdown: str