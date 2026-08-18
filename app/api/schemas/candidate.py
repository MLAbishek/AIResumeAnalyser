from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CandidateJobSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    title: str | None
    location: str | None
    job_type: str | None
    required_skills: list[str]
    required_experience_months: int
    status: str
    created_at: datetime


class CandidateJobDetail(CandidateJobSummary):
    description: str | None
    raw_text: str
    preferred_skills: list[str]
    required_technologies: list[str]


class ApplyRequest(BaseModel):
    resume_id: str
