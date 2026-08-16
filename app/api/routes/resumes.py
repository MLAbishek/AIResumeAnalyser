from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from app.auth.dependencies import require_role
from app.api.dependencies import get_db
from app.api.schemas.resumes import (
    ResumeCreateRequest,
    ResumeResponse,
)
from app.database.crud.resumes import (
    create_resume,
    get_resume_by_id,
    list_resumes,
)
from app.database.models.resume import (
    Resume,
    ResumeEducation,
    ResumeExperience,
)


router = APIRouter(
    prefix="/resumes",
    tags=["resumes"],
)


@router.post(
    "",
    response_model=ResumeResponse,
    status_code=201,
    dependencies=[
        Depends(require_role("admin", "recruiter"))
    ],
)
def create_resume_endpoint(
    payload: ResumeCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role("admin", "recruiter")
    ),
):
    existing = get_resume_by_id(
        db,
        payload.resume_id,
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Resume '{payload.resume_id}' "
                "already exists."
            ),
        )

    try:
        resume = create_resume(
            db,
            resume_id=payload.resume_id,
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            summary=payload.summary,
            skills=payload.skills,
            job_titles=payload.job_titles,
            organizations=payload.organizations,
            technologies=payload.technologies,
            total_experience_months=(
                payload.total_experience_months
            ),
            raw_text=payload.raw_text,
        )

        for experience in payload.experiences:
            db.add(
                ResumeExperience(
                    resume_id=resume.id,
                    job_title=experience.job_title,
                    company=experience.company,
                    start_date=experience.start_date,
                    end_date=experience.end_date,
                    duration_months=(
                        experience.duration_months
                    ),
                )
            )

        for education in payload.education:
            db.add(
                ResumeEducation(
                    resume_id=resume.id,
                    degree=education.degree,
                    institution=education.institution,
                    field_of_study=(
                        education.field_of_study
                    ),
                    start_date=education.start_date,
                    end_date=education.end_date,
                )
            )

        db.commit()

        resume = (
            db.query(type(resume))
            .options(
                selectinload(
                    type(resume).experiences
                ),
                selectinload(
                    type(resume).education
                ),
            )
            .filter(
                type(resume).id == resume.id
            )
            .first()
        )

        return resume

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Resume could not be created.",
        ) from exc


@router.get(
    "",
    response_model=list[ResumeResponse],
    dependencies=[
        Depends(require_role("admin", "recruiter", "viewer"))
    ],
)
def list_resumes_endpoint(
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
    return (
        db.query(Resume)
        .options(
            selectinload(Resume.experiences),
            selectinload(Resume.education),
        )
        .order_by(Resume.id)
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    dependencies=[
        Depends(require_role("admin", "recruiter", "viewer"))
    ],
)
def get_resume_endpoint(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role("admin", "recruiter", "viewer")
    ),
):
    from app.database.models.resume import Resume

    resume = (
        db.query(Resume)
        .options(
            selectinload(Resume.experiences),
            selectinload(Resume.education),
        )
        .filter(
            Resume.resume_id == resume_id
        )
        .first()
    )

    if resume is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Resume '{resume_id}' "
                "not found."
            ),
        )

    return resume