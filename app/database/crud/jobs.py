from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.job import Job


def create_job(
    db: Session,
    *,
    job_id: str,
    title: str | None = None,
    description: str | None = None,
    location: str | None = None,
    job_type: str | None = None,
    raw_text: str,
    required_skills: list | None = None,
    preferred_skills: list | None = None,
    required_technologies: list | None = None,
    preferred_technologies: list | None = None,
    education_requirements: list | None = None,
    required_certifications: list | None = None,
    required_experience_months: int = 0,
) -> Job:
    job = Job(
        job_id=job_id,
        title=title,
        description=description,
        location=location,
        job_type=job_type,
        raw_text=raw_text,
        required_skills=required_skills or [],
        preferred_skills=preferred_skills or [],
        required_technologies=required_technologies or [],
        preferred_technologies=preferred_technologies or [],
        education_requirements=education_requirements or [],
        required_certifications=required_certifications or [],
        required_experience_months=required_experience_months,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


def get_job_by_id(
    db: Session,
    job_id: str,
) -> Job | None:
    statement = select(Job).where(Job.job_id == job_id)

    return db.scalar(statement)


def get_job_by_pk(
    db: Session,
    job_pk: int,
) -> Job | None:
    return db.get(Job, job_pk)


def list_jobs(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[Job]:
    statement = (
        select(Job)
        .order_by(Job.id)
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def delete_job(
    db: Session,
    job: Job,
) -> None:
    db.delete(job)
    db.commit()