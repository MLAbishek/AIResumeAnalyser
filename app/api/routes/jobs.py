import tempfile
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from sqlalchemy.orm import Session
from app.auth.dependencies import require_role
from app.auth.models import User
from app.api.dependencies import get_db
from app.api.schemas.jobs import (
    JobCreateRequest,
    JobResponse,
)
from app.database.crud.applications import (
    list_applications_for_job,
)
from app.database.crud.jobs import (
    close_job,
    create_job,
    delete_job,
    get_job_by_id,
    list_jobs,
)
from app.ingestion.document_validator import DocumentValidator
from app.services.job_description_service import (
    JobDescriptionExtractionError,
    extract_job_description,
)


router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)


def _job_to_response(job) -> JobResponse:
    return JobResponse(
        job_id=job.job_id,
        title=job.title,
        description=job.description,
        location=job.location,
        job_type=job.job_type,
        raw_text=job.raw_text,
        required_skills=job.required_skills or [],
        preferred_skills=job.preferred_skills or [],
        required_technologies=(
            job.required_technologies or []
        ),
        preferred_technologies=(
            job.preferred_technologies or []
        ),
        education_requirements=(
            job.education_requirements or []
        ),
        required_certifications=(
            job.required_certifications or []
        ),
        required_experience_months=(
            job.required_experience_months
        ),
        status=job.status,
    )


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


@router.post(
    "",
    response_model=JobResponse,
    status_code=201,
    dependencies=[
        Depends(require_role("admin", "recruiter"))
    ],
)
def create_job_endpoint(
    request: JobCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(
        require_role("admin","recruiter")
    )
):
    existing = get_job_by_id(
        db,
        request.job_id,
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Job '{request.job_id}' already exists."
            ),
        )

    job = create_job(
        db,
        job_id=request.job_id,
        title=request.title,
        description=request.description,
        location=request.location,
        job_type=request.job_type,
        raw_text=request.raw_text,
        required_skills=request.required_skills,
        preferred_skills=request.preferred_skills,
        required_technologies=(
            request.required_technologies
        ),
        preferred_technologies=(
            request.preferred_technologies
        ),
        education_requirements=(
            request.education_requirements
        ),
        required_certifications=(
            request.required_certifications
        ),
        required_experience_months=(
            request.required_experience_months
        ),
        created_by_user_id=current_user.id,
    )

    return _job_to_response(job)


@router.post(
    "/upload",
    response_model=JobResponse,
    status_code=201,
    dependencies=[
        Depends(require_role("admin", "recruiter"))
    ],
)
async def create_job_from_file_endpoint(
    title: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("admin", "recruiter")
    ),
):
    suffix = Path(file.filename or "").suffix.lower()

    if suffix not in DocumentValidator.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=(
                "Unsupported job description file type. "
                "Allowed formats: PDF, DOCX, TXT."
            ),
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail=(
                "The uploaded job description does not "
                "contain readable text."
            ),
        )

    max_bytes = 10 * 1024 * 1024

    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=(
                "Job description file exceeds the maximum "
                "allowed size of 10 MB."
            ),
        )

    with tempfile.NamedTemporaryFile(
        suffix=suffix,
        delete=False,
    ) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        try:
            raw_text = extract_job_description(tmp_path)
        except JobDescriptionExtractionError as exc:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The uploaded job description does not "
                    "contain readable text."
                ),
            ) from exc

        job_id = f"recruiter-upload-{uuid.uuid4().hex[:12]}"

        job = create_job(
            db,
            job_id=job_id,
            title=title or None,
            raw_text=raw_text,
            required_skills=[],
            preferred_skills=[],
            required_technologies=[],
            preferred_technologies=[],
            created_by_user_id=current_user.id,
        )

        return _job_to_response(job)
    finally:
        tmp_path.unlink(missing_ok=True)


@router.get(
    "",
    response_model=list[JobResponse],
    dependencies=[
        Depends(require_role("admin", "recruiter", "viewer"))
    ],
)
def list_jobs_endpoint(
    offset: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role("admin", "recruiter", "viewer")
    ),
):
    jobs = list_jobs(
        db,
        offset=offset,
        limit=limit,
    )

    return [
        _job_to_response(job)
        for job in jobs
    ]


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    dependencies=[
        Depends(require_role("admin", "recruiter", "viewer"))
    ],
)
def get_job_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role("admin", "recruiter", "viewer")
    ),    
):
    job = get_job_by_id(
        db,
        job_id,
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found.",
        )

    return _job_to_response(job)


@router.post(
    "/{job_id}/close",
    response_model=JobResponse,
    dependencies=[
        Depends(require_role("admin", "recruiter"))
    ],
)
def close_job_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
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

    job = close_job(db, job)

    return _job_to_response(job)


@router.delete(
    "/{job_id}",
    status_code=204,
    dependencies=[
        Depends(require_role("admin", "recruiter"))
    ],
)
def delete_job_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
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

    if list_applications_for_job(db, job.id):
        raise HTTPException(
            status_code=409,
            detail=(
                "This job has applications and cannot be "
                "deleted. Close it instead to stop accepting "
                "new applications while preserving history."
            ),
        )

    delete_job(db, job)