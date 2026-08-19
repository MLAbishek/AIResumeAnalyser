import mimetypes

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas.applications import (
    RECRUITER_SETTABLE_STATUSES,
    ApplicationResponse,
    ApplicationStatusUpdateRequest,
    RecruiterApplicationListItem,
    RecruiterApplicationListResponse,
)
from app.api.schemas.resumes import ResumeResponse
from app.auth.dependencies import require_role
from app.auth.models import User
from app.database.crud.applications import (
    get_application_by_id,
    list_applications_for_job,
    update_application_status,
)
from app.database.crud.jobs import get_job_by_id
from app.database.models.application import Application
from app.services.candidate_match_service import (
    CandidateMatchService,
    screening_to_response,
)
from app.services.resume_document_storage import (
    get_resume_storage,
)
from app.storage.exceptions import DocumentNotFoundError


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


def _load_authorized_application(
    db: Session,
    job_id: str,
    application_id: int,
    current_user: User,
):
    """
    Resolve (job, application) for a recruiter request, enforcing the
    full authorization chain: the recruiter must own the job, and
    the application must actually belong to that job - a recruiter
    can never reach an unrelated candidate's application merely by
    guessing an application_id.
    """

    job = get_job_by_id(db, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found.",
        )

    _ensure_job_owner(job, current_user)

    application = get_application_by_id(db, application_id)

    if application is None or application.job_id != job.id:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    return job, application


def _application_to_response(
    application: Application,
    *,
    job_id: str,
    job_title: str | None,
    screening_response,
) -> ApplicationResponse:
    return ApplicationResponse(
        application_id=application.id,
        job_id=job_id,
        job_title=job_title,
        resume_id=application.resume.resume_id,
        candidate_name=application.resume.name,
        candidate_email=application.candidate.email,
        status=application.status,
        applied_at=application.applied_at,
        updated_at=application.updated_at,
        screening=screening_response,
        resume=ResumeResponse.model_validate(
            application.resume
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
                candidate_email=application.candidate.email,
                status=application.status,
                applied_at=application.applied_at,
                skills=application.resume.skills or [],
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
    job, application = _load_authorized_application(
        db, job_id, application_id, current_user
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

    return _application_to_response(
        application,
        job_id=job.job_id,
        job_title=job.title,
        screening_response=screening_response,
    )


@router.get(
    "/jobs/{job_id}/applications/{application_id}/resume",
    dependencies=[
        Depends(require_role("admin", "recruiter"))
    ],
)
def download_application_resume(
    job_id: str,
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("admin", "recruiter")
    ),
):
    """
    Stream the candidate's actual uploaded resume file to an
    authorized recruiter.

    Authorization mirrors get_job_application: the recruiter must
    own the job, and the application must belong to that job - the
    candidate's resume is only reachable through that chain, never
    by an application_id alone.
    """

    _job, application = _load_authorized_application(
        db, job_id, application_id, current_user
    )

    try:
        path = get_resume_storage().get_raw_path(
            application.resume.resume_id
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "The original resume file is not available "
                "for this application."
            ),
        ) from exc

    content_type = (
        mimetypes.guess_type(path.name)[0]
        or "application/octet-stream"
    )

    return Response(
        content=path.read_bytes(),
        media_type=content_type,
        headers={
            "Content-Disposition": (
                f'inline; filename="{application.resume.resume_id}'
                f'{path.suffix}"'
            ),
        },
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

    return _application_to_response(
        application,
        job_id=application.job.job_id,
        job_title=application.job.title,
        screening_response=screening_response,
    )
