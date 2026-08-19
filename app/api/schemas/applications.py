from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.api.schemas.resumes import ResumeResponse
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
    # The candidate's real account email (from their login, not the
    # resume parser's best-effort extraction) - reliable even when
    # resume text parsing produces a messy or missing name/email.
    candidate_email: str | None = None
    status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime
    screening: ScreeningResultResponse | None
    # Full candidate profile (skills, education, experience, resume
    # text) - present whenever the resume could be loaded, so the
    # recruiter/candidate detail view has everything without a
    # second request.
    resume: ResumeResponse | None = None


class RecruiterApplicationListItem(BaseModel):
    application_id: int
    resume_id: str
    candidate_name: str | None
    candidate_email: str | None = None
    status: ApplicationStatus
    applied_at: datetime
    rank: int | None
    score: float | None
    eligible: bool | None
    decision: str | None
    skills: list[str] = []


class RecruiterApplicationListResponse(BaseModel):
    job_id: str
    total_applications: int
    results: list[RecruiterApplicationListItem]
