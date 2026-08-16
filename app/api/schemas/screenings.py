from typing import Any

from pydantic import BaseModel,Field


class ScreeningResultResponse(BaseModel):
    screening_id: int
    job_id: str
    resume_id: str
    candidate_name: str | None = None

    eligible: bool
    decision: str | None
    final_score: float | None
    decision_reason: str | None

    ranking: dict[str, Any] | None = None
    gap_analysis: dict[str, Any] | None = None
    explanation: dict[str, Any] | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list)


class ScreeningListResponse(BaseModel):
    job_id: str
    total_candidates: int
    results: list[ScreeningResultResponse]