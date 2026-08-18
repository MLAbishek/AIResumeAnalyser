from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.resume import (
    Resume,
    ResumeEducation,
    ResumeExperience,
)


def create_resume(
    db: Session,
    *,
    resume_id: str,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    summary: str | None = None,
    skills: list | None = None,
    job_titles: list | None = None,
    organizations: list | None = None,
    technologies: list | None = None,
    total_experience_months: int = 0,
    raw_text: str | None = None,
    owner_user_id: int | None = None,
) -> Resume:
    resume = Resume(
        resume_id=resume_id,
        name=name,
        email=email,
        phone=phone,
        summary=summary,
        skills=skills or [],
        job_titles=job_titles or [],
        organizations=organizations or [],
        technologies=technologies or [],
        total_experience_months=total_experience_months,
        raw_text=raw_text,
        owner_user_id=owner_user_id,
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    return resume


def list_resumes_for_owner(
    db: Session,
    *,
    owner_user_id: int,
) -> list[Resume]:
    statement = (
        select(Resume)
        .where(Resume.owner_user_id == owner_user_id)
        .order_by(Resume.created_at.desc())
    )

    return list(db.scalars(statement).all())


def get_resume_by_id(
    db: Session,
    resume_id: str,
) -> Resume | None:
    statement = select(Resume).where(
        Resume.resume_id == resume_id
    )

    return db.scalar(statement)


def get_resume_by_pk(
    db: Session,
    resume_pk: int,
) -> Resume | None:
    return db.get(Resume, resume_pk)


def list_resumes(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[Resume]:
    statement = (
        select(Resume)
        .order_by(
            Resume.created_at.desc(), Resume.id.desc()
        )
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def add_experience(
    db: Session,
    *,
    resume: Resume,
    job_title: str,
    company: str,
    start_date,
    end_date,
    duration_months: int,
) -> ResumeExperience:
    experience = ResumeExperience(
        resume_id=resume.id,
        job_title=job_title,
        company=company,
        start_date=start_date,
        end_date=end_date,
        duration_months=duration_months,
    )

    db.add(experience)
    db.commit()
    db.refresh(experience)

    return experience


def add_education(
    db: Session,
    *,
    resume: Resume,
    degree: str,
    institution: str,
    field_of_study: str | None = None,
    start_date=None,
    end_date=None,
) -> ResumeEducation:
    education = ResumeEducation(
        resume_id=resume.id,
        degree=degree,
        institution=institution,
        field_of_study=field_of_study,
        start_date=start_date,
        end_date=end_date,
    )

    db.add(education)
    db.commit()
    db.refresh(education)

    return education


def delete_resume(
    db: Session,
    resume: Resume,
) -> None:
    db.delete(resume)
    db.commit()