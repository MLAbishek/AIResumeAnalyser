from pydantic import BaseModel, Field

from app.core.schemas import (
    JobDescription,
    Resume,
)


class ScreeningRequest(BaseModel):
    job_description: JobDescription
    resumes: list[Resume] = Field(
        default_factory=list
    )


class ScreeningResponse(BaseModel):
    job_id: str
    total_candidates: int
    eligible_candidates: int
    results: list[dict]