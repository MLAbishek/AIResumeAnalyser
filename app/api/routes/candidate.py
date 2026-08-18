import tempfile
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas.applications import ApplicationResponse
from app.api.schemas.candidate import (
    ApplyRequest,
    CandidateJobDetail,
    CandidateJobSummary,
)
from app.api.schemas.resumes import ResumeResponse
from app.api.schemas.screenings import ScreeningResultResponse
from app.auth.dependencies import require_role
from app.auth.models import User
from app.database.crud.applications import (
    create_application,
    get_application_by_id,
    get_application_for_candidate_job,
    list_applications_for_candidate,
)
from app.database.crud.jobs import get_job_by_id, list_open_jobs
from app.database.crud.resumes import (
    create_resume,
    get_resume_by_id,
    list_resumes_for_owner,
)
from app.ingestion.document_validator import DocumentValidator
from app.ingestion.resume_loader import ResumeLoader
from app.parsing.resume_parse import ResumeParser
from app.services.candidate_match_service import (
    CandidateMatchService,
    screening_to_response,
)


router = APIRouter(
    prefix="/candidate",
    tags=["candidate"],
)


# ---------------------------------------------------------------
# Job browsing
# ---------------------------------------------------------------


@router.get(
    "/jobs",
    response_model=list[CandidateJobSummary],
    dependencies=[Depends(require_role("candidate"))],
)
def list_available_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("candidate")
    ),
):
    jobs = list_open_jobs(db)

    return [
        CandidateJobSummary.model_validate(job)
        for job in jobs
    ]


@router.get(
    "/jobs/{job_id}",
    response_model=CandidateJobDetail,
    dependencies=[Depends(require_role("candidate"))],
)
def get_available_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("candidate")
    ),
):
    job = get_job_by_id(db, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found.",
        )

    has_application = (
        get_application_for_candidate_job(
            db,
            job_id=job.id,
            candidate_user_id=current_user.id,
        )
        is not None
    )

    if job.status != "open" and not has_application:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found.",
        )

    return CandidateJobDetail.model_validate(job)


# ---------------------------------------------------------------
# Resume upload
# ---------------------------------------------------------------


@router.post(
    "/resumes/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("candidate"))],
)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("candidate")
    ),
):
    suffix = Path(file.filename or "").suffix.lower()

    if suffix not in DocumentValidator.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=(
                "Unsupported file type. Supported formats: "
                "PDF, DOCX, TXT."
            ),
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    max_bytes = 10 * 1024 * 1024

    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail="Resume file exceeds the 10 MB size limit.",
        )

    with tempfile.NamedTemporaryFile(
        suffix=suffix,
        delete=False,
    ) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        validation = DocumentValidator().validate(tmp_path)

        if not validation.is_valid:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Resume could not be validated: "
                    + "; ".join(validation.errors)
                ),
            )

        try:
            raw_document = ResumeLoader().load(tmp_path)
            parsed = ResumeParser().parse(raw_document)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Resume could not be parsed. Please upload "
                    "a valid PDF, DOCX, or TXT resume."
                ),
            ) from exc

        existing = get_resume_by_id(
            db,
            parsed.resume_id,
        )

        if (
            existing is not None
            and existing.owner_user_id == current_user.id
        ):
            return existing

        resume_id = parsed.resume_id

        if existing is not None:
            # Extremely unlikely hash collision across candidates -
            # disambiguate rather than fail the upload.
            resume_id = (
                f"{parsed.resume_id}-{current_user.id}"
            )

        try:
            resume = create_resume(
                db,
                resume_id=resume_id,
                name=parsed.name,
                summary=parsed.summary,
                skills=parsed.skills,
                job_titles=parsed.job_titles,
                organizations=[],
                technologies=[],
                total_experience_months=int(
                    round(
                        (parsed.total_experience_years or 0)
                        * 12
                    )
                ),
                raw_text=parsed.raw_text,
                owner_user_id=current_user.id,
            )
        except IntegrityError as exc:
            db.rollback()

            raise HTTPException(
                status_code=409,
                detail="Resume could not be saved.",
            ) from exc

        return resume

    finally:
        tmp_path.unlink(missing_ok=True)


@router.get(
    "/resumes",
    response_model=list[ResumeResponse],
    dependencies=[Depends(require_role("candidate"))],
)
def list_my_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("candidate")
    ),
):
    return list_resumes_for_owner(
        db,
        owner_user_id=current_user.id,
    )


# ---------------------------------------------------------------
# Match preview
# ---------------------------------------------------------------


def _load_owned_resume(
    db: Session,
    resume_id: str,
    current_user: User,
):
    resume = get_resume_by_id(db, resume_id)

    if resume is None:
        raise HTTPException(
            status_code=404,
            detail=f"Resume '{resume_id}' not found.",
        )

    if resume.owner_user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this resume.",
        )

    return resume


def _load_open_job(db: Session, job_id: str):
    job = get_job_by_id(db, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found.",
        )

    return job


@router.post(
    "/jobs/{job_id}/preview",
    response_model=ScreeningResultResponse,
    dependencies=[Depends(require_role("candidate"))],
)
def preview_match(
    job_id: str,
    payload: ApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("candidate")
    ),
):
    job = _load_open_job(db, job_id)
    resume = _load_owned_resume(
        db, payload.resume_id, current_user
    )

    if job.status != "open":
        raise HTTPException(
            status_code=409,
            detail="This job is no longer accepting applications.",
        )

    service = CandidateMatchService(db)

    screening = service.get_or_create_preview(
        job=job,
        resume=resume,
        candidate_user_id=current_user.id,
    )

    return screening_to_response(screening)


# ---------------------------------------------------------------
# Apply
# ---------------------------------------------------------------


@router.post(
    "/jobs/{job_id}/apply",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("candidate"))],
)
def apply_to_job(
    job_id: str,
    payload: ApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("candidate")
    ),
):
    job = _load_open_job(db, job_id)
    resume = _load_owned_resume(
        db, payload.resume_id, current_user
    )

    if job.status != "open":
        raise HTTPException(
            status_code=409,
            detail="This job is no longer accepting applications.",
        )

    if (
        get_application_for_candidate_job(
            db,
            job_id=job.id,
            candidate_user_id=current_user.id,
        )
        is not None
    ):
        raise HTTPException(
            status_code=409,
            detail="You have already applied to this job.",
        )

    service = CandidateMatchService(db)

    screening = service.get_or_create_preview(
        job=job,
        resume=resume,
        candidate_user_id=current_user.id,
    )

    try:
        application = create_application(
            db,
            job_id=job.id,
            candidate_user_id=current_user.id,
            resume_id=resume.id,
            screening_id=screening.id,
        )
    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="You have already applied to this job.",
        ) from exc

    return ApplicationResponse(
        application_id=application.id,
        job_id=job.job_id,
        job_title=job.title,
        resume_id=resume.resume_id,
        candidate_name=resume.name,
        status=application.status,
        applied_at=application.applied_at,
        updated_at=application.updated_at,
        screening=screening_to_response(screening),
    )


# ---------------------------------------------------------------
# Candidate's own applications
# ---------------------------------------------------------------


@router.get(
    "/applications",
    response_model=list[ApplicationResponse],
    dependencies=[Depends(require_role("candidate"))],
)
def list_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("candidate")
    ),
):
    applications = list_applications_for_candidate(
        db,
        candidate_user_id=current_user.id,
    )

    responses = []

    for application in applications:
        screening_response = None

        if application.screening_id is not None:
            service = CandidateMatchService(db)
            screening = service.reload_screening(
                application.screening_id
            )
            screening_response = screening_to_response(
                screening
            )

        responses.append(
            ApplicationResponse(
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
        )

    return responses


@router.get(
    "/applications/{application_id}",
    response_model=ApplicationResponse,
    dependencies=[Depends(require_role("candidate"))],
)
def get_my_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("candidate")
    ),
):
    application = get_application_by_id(
        db, application_id
    )

    if (
        application is None
        or application.candidate_user_id
        != current_user.id
    ):
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
        job_id=application.job.job_id,
        job_title=application.job.title,
        resume_id=application.resume.resume_id,
        candidate_name=application.resume.name,
        status=application.status,
        applied_at=application.applied_at,
        updated_at=application.updated_at,
        screening=screening_response,
    )
