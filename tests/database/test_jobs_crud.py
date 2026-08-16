from app.database.crud.jobs import (
    create_job,
    delete_job,
    get_job_by_id,
    get_job_by_pk,
    list_jobs,
)


def test_create_and_get_job(db):
    job = create_job(
        db,
        job_id="JOB-CRUD-001",
        title="Python Developer",
        description="Backend Python developer",
        location="Chennai",
        job_type="Full-time",
        raw_text="Python developer with FastAPI experience",
        required_skills=["Python", "FastAPI"],
        preferred_skills=["Docker"],
        required_technologies=["PostgreSQL"],
        preferred_technologies=["Redis"],
        education_requirements=[],
        required_certifications=[],
        required_experience_months=24,
    )

    assert job.id is not None
    assert job.job_id == "JOB-CRUD-001"

    fetched = get_job_by_id(
        db,
        "JOB-CRUD-001",
    )

    assert fetched is not None
    assert fetched.id == job.id
    assert fetched.title == "Python Developer"


def test_get_job_by_primary_key(db):
    job = create_job(
        db,
        job_id="JOB-CRUD-002",
        raw_text="Test JD",
    )

    fetched = get_job_by_pk(
        db,
        job.id,
    )

    assert fetched is not None
    assert fetched.job_id == "JOB-CRUD-002"


def test_list_jobs(db):
    create_job(
        db,
        job_id="JOB-CRUD-003",
        raw_text="JD 1",
    )

    create_job(
        db,
        job_id="JOB-CRUD-004",
        raw_text="JD 2",
    )

    jobs = list_jobs(db)

    ids = {
        job.job_id
        for job in jobs
    }

    assert "JOB-CRUD-003" in ids
    assert "JOB-CRUD-004" in ids


def test_delete_job(db):
    job = create_job(
        db,
        job_id="JOB-CRUD-005",
        raw_text="Delete me",
    )

    delete_job(db, job)

    assert get_job_by_id(
        db,
        "JOB-CRUD-005",
    ) is None