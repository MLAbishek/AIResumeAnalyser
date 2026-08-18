from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas.applications import (
    RECRUITER_SETTABLE_STATUSES,
    ApplicationResponse,
    ApplicationStatusUpdateRequest,
    RecruiterApplicationListItem,
    RecruiterApplicationListResponse,
)
from app.auth.dependencies import require_role
from app.auth.models import User
from app.database.crud.applications import (
    get_application_by_id,
    list_applications_for_job,
    update_application_status,
)
from app.database.crud.jobs import get_job_by_id
from app.services.candidate_match_service import (
    CandidateMatchService,
    screening_to_response,
)


router = APIRouter(tags=["applications"])


def _ensure_job_owner(job, current_user: User) -> None:
    if current_user.role == "admin":
        return

    if (
        job.created_by_user_id is not None
        and job.created_by_user_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have permission to manage "
                "this job."
            ),
        )


@router.get(
    "/jobs/{job_id}/applications",
    response_model=RecruiterApplicationListResponse,
    dependencies=[
        Depends(require_role("admin", "recruiter"))
    ],
)
def list_job_applications(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("admin", "recruiter")
    ),
):
    job = get_job_by_id(db, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found.",
        )

    _ensure_job_owner(job, current_user)

    applications = list_applications_for_job(db, job.id)

    items = []

    for application in applications:
        screening = application.screening

        items.append(
            RecruiterApplicationListItem(
                application_id=application.id,
                resume_id=application.resume.resume_id,
                candidate_name=application.resume.name,
                status=application.status,
                applied_at=application.applied_at,
                rank=(
                    screening.ranking.rank
                    if screening
                    and screening.ranking
                    else None
                ),
                score=(
                    screening.ranking.score
                    if screening
                    and screening.ranking
                    else None
                ),
                eligible=(
                    screening.eligible
                    if screening
                    else None
                ),
                decision=(
                    screening.decision
                    if screening
                    else None
                ),
            )
        )

    def _sort_key(
        item: RecruiterApplicationListItem,
    ) -> tuple:
        # A persisted `rank` (from a bulk /api/screen run across
        # multiple resumes at once) is the authoritative order.
        # Candidates who applied individually through the portal
        # are each screened alone, so they never get a `rank` -
        # for them, fall back to sorting by their AI match score
        # so "ranked by AI match score" reflects the actual score
        # rather than application submission order.
        if item.rank is not None:
            return (0, item.rank)

        if item.score is not None:
            return (1, -item.score)

        return (2, 0)

    items.sort(key=_sort_key)

    return RecruiterApplicationListResponse(
        job_id=job_id,
        total_applications=len(items),
        results=items,
    )


@router.get(
    "/jobs/{job_id}/applications/{application_id}",
    response_model=ApplicationResponse,
    dependencies=[
        Depends(require_role("admin", "recruiter"))
    ],
)
def get_job_application(
    job_id: str,
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("admin", "recruiter")
    ),
):
    job = get_job_by_id(db, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found.",
        )

    _ensure_job_owner(job, current_user)

    application = get_application_by_id(
        db, application_id
    )

    if application is None or application.job_id != job.id:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    screening_response = None

    if application.screening_id is not None:
        service = CandidateMatchService(db)
        screening = service.reload_screening(
            application.screening_id
        )
        screening_response = screening_to_response(
            screening
        )

    return ApplicationResponse(
        application_id=application.id,
        job_id=job.job_id,
        job_title=job.title,
        resume_id=application.resume.resume_id,
        candidate_name=application.resume.name,
        status=application.status,
        applied_at=application.applied_at,
        updated_at=application.updated_at,
        screening=screening_response,
    )


@router.patch(
    "/applications/{application_id}/status",
    response_model=ApplicationResponse,
    dependencies=[
        Depends(require_role("admin", "recruiter"))
    ],
)
def update_status(
    application_id: int,
    payload: ApplicationStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("admin", "recruiter")
    ),
):
    application = get_application_by_id(
        db, application_id
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    _ensure_job_owner(application.job, current_user)

    if payload.status not in RECRUITER_SETTABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Recruiters cannot set application status "
                f"to '{payload.status}'."
            ),
        )

    application = update_application_status(
        db,
        application,
        status=payload.status,
    )

    screening_response = None

    if application.screening_id is not None:
        service = CandidateMatchService(db)
        screening = service.reload_screening(
            application.screening_id
        )
        screening_response = screening_to_response(
            screening
        )

    return ApplicationResponse(
        application_id=application.id,
        job_id=application.job.job_id,
        job_title=application.job.title,
        resume_id=application.resume.resume_id,
        candidate_name=application.resume.name,
        status=application.status,
        applied_at=application.applied_at,
        updated_at=application.updated_at,
        screening=screening_response,
    )
