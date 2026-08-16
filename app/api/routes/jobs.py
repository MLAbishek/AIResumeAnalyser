from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.auth.dependencies import require_role
from app.api.dependencies import get_db
from app.api.schemas.jobs import (
    JobCreateRequest,
    JobResponse,
)
from app.database.crud.jobs import (
    create_job,
    get_job_by_id,
    list_jobs,
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
    )

    return _job_to_response(job)


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