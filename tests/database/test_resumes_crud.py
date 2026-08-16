from datetime import date

from app.database.crud.resumes import (
    add_education,
    add_experience,
    create_resume,
    delete_resume,
    get_resume_by_id,
    get_resume_by_pk,
    list_resumes,
)


def test_create_and_get_resume(db):
    resume = create_resume(
        db,
        resume_id="RESUME-CRUD-001",
        name="Test Candidate",
        email="candidate@example.com",
        skills=["Python", "FastAPI"],
        job_titles=["Backend Developer"],
        organizations=["Example Corp"],
        technologies=["PostgreSQL"],
        total_experience_months=36,
        raw_text="Python backend developer",
    )

    assert resume.id is not None
    assert resume.resume_id == "RESUME-CRUD-001"

    fetched = get_resume_by_id(
        db,
        "RESUME-CRUD-001",
    )

    assert fetched is not None
    assert fetched.name == "Test Candidate"


def test_get_resume_by_primary_key(db):
    resume = create_resume(
        db,
        resume_id="RESUME-CRUD-002",
        raw_text="Test resume",
    )

    fetched = get_resume_by_pk(
        db,
        resume.id,
    )

    assert fetched is not None
    assert fetched.resume_id == "RESUME-CRUD-002"


def test_list_resumes(db):
    create_resume(
        db,
        resume_id="RESUME-CRUD-003",
        raw_text="Resume 1",
    )

    create_resume(
        db,
        resume_id="RESUME-CRUD-004",
        raw_text="Resume 2",
    )

    resumes = list_resumes(db)

    ids = {
        resume.resume_id
        for resume in resumes
    }

    assert "RESUME-CRUD-003" in ids
    assert "RESUME-CRUD-004" in ids


def test_add_experience(db):
    resume = create_resume(
        db,
        resume_id="RESUME-CRUD-005",
        raw_text="Experienced developer",
    )

    experience = add_experience(
        db,
        resume=resume,
        job_title="Backend Developer",
        company="Example Corp",
        start_date=date(2022, 1, 1),
        end_date=date(2025, 1, 1),
        duration_months=36,
    )

    assert experience.id is not None
    assert experience.resume_id == resume.id
    assert experience.job_title == "Backend Developer"


def test_add_education(db):
    resume = create_resume(
        db,
        resume_id="RESUME-CRUD-006",
        raw_text="Graduate",
    )

    education = add_education(
        db,
        resume=resume,
        degree="B.Tech",
        institution="Example University",
        field_of_study="Computer Science",
        start_date=date(2018, 1, 1),
        end_date=date(2022, 5, 1),
    )

    assert education.id is not None
    assert education.resume_id == resume.id
    assert education.degree == "B.Tech"


def test_delete_resume(db):
    resume = create_resume(
        db,
        resume_id="RESUME-CRUD-007",
        raw_text="Delete me",
    )

    delete_resume(db, resume)

    assert get_resume_by_id(
        db,
        "RESUME-CRUD-007",
    ) is None