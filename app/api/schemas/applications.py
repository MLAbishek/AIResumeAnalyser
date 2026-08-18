from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.api.schemas.screenings import ScreeningResultResponse


ApplicationStatus = Literal[
    "applied",
    "shortlisted",
    "rejected",
    "withdrawn",
]

# Statuses a recruiter is allowed to move an application to.
# Candidates can only ever reach "withdrawn" (via a separate,
# explicit withdraw action) - never shortlisted/rejected.
RECRUITER_SETTABLE_STATUSES = {
    "applied",
    "shortlisted",
    "rejected",
}


class ApplicationStatusUpdateRequest(BaseModel):
    status: ApplicationStatus


class ApplicationResponse(BaseModel):
    application_id: int
    job_id: str
    job_title: str | None
    resume_id: str
    candidate_name: str | None
    status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime
    screening: ScreeningResultResponse | None


class RecruiterApplicationListItem(BaseModel):
    application_id: int
    resume_id: str
    candidate_name: str | None
    status: ApplicationStatus
    applied_at: datetime
    rank: int | None
    score: float | None
    eligible: bool | None
    decision: str | None


class RecruiterApplicationListResponse(BaseModel):
    job_id: str
    total_applications: int
    results: list[RecruiterApplicationListItem]
