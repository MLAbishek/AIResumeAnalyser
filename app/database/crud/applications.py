from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.models.application import Application


def create_application(
    db: Session,
    *,
    job_id: int,
    candidate_user_id: int,
    resume_id: int,
    screening_id: int | None,
) -> Application:
    application = Application(
        job_id=job_id,
        candidate_user_id=candidate_user_id,
        resume_id=resume_id,
        screening_id=screening_id,
        status="applied",
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return application


def get_application_by_id(
    db: Session,
    application_id: int,
) -> Application | None:
    return db.get(
        Application,
        application_id,
        options=[
            selectinload(Application.job),
            selectinload(Application.resume),
            selectinload(Application.screening),
        ],
    )


def get_application_for_candidate_job(
    db: Session,
    *,
    job_id: int,
    candidate_user_id: int,
) -> Application | None:
    statement = select(Application).where(
        Application.job_id == job_id,
        Application.candidate_user_id == candidate_user_id,
    )

    return db.scalar(statement)


def list_applications_for_job(
    db: Session,
    job_id: int,
) -> list[Application]:
    statement = (
        select(Application)
        .where(Application.job_id == job_id)
        .options(
            selectinload(Application.resume),
            selectinload(Application.screening),
        )
        .order_by(Application.applied_at.asc())
    )

    return list(db.scalars(statement).all())


def list_applications_for_candidate(
    db: Session,
    candidate_user_id: int,
) -> list[Application]:
    statement = (
        select(Application)
        .where(
            Application.candidate_user_id
            == candidate_user_id
        )
        .options(
            selectinload(Application.job),
            selectinload(Application.resume),
            selectinload(Application.screening),
        )
        .order_by(Application.applied_at.desc())
    )

    return list(db.scalars(statement).all())


def update_application_status(
    db: Session,
    application: Application,
    *,
    status: str,
) -> Application:
    application.status = status

    db.commit()
    db.refresh(application)

    return application
