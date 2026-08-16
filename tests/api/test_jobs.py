from app.database.crud.jobs import get_job_by_id


def job_payload(
    job_id="JOB-API-001",
):
    return {
        "job_id": job_id,
        "title": "Python Backend Developer",
        "description": "Backend development using Python.",
        "location": "Bangalore",
        "job_type": "Full-time",
        "raw_text": (
            "Python Backend Developer with FastAPI "
            "and PostgreSQL experience."
        ),
        "required_skills": [
            "Python",
            "FastAPI",
        ],
        "preferred_skills": [
            "Docker",
        ],
        "required_technologies": [
            "PostgreSQL",
        ],
        "preferred_technologies": [
            "Redis",
        ],
        "education_requirements": [
            {
                "degree": "B.Tech",
                "field_of_study": "Computer Science",
                "required": True,
            }
        ],
        "required_certifications": [],
        "required_experience_months": 24,
    }


def test_create_job(client, db):
    response = client.post(
        "/api/jobs",
        json=job_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["job_id"] == "JOB-API-001"
    assert data["title"] == "Python Backend Developer"
    assert data["required_skills"] == [
        "Python",
        "FastAPI",
    ]
    assert data["required_experience_months"] == 24

    job = get_job_by_id(
        db,
        "JOB-API-001",
    )

    assert job is not None
    assert job.title == "Python Backend Developer"


def test_create_duplicate_job_returns_409(client):
    payload = job_payload(
        "JOB-API-DUPLICATE"
    )

    first = client.post(
        "/api/jobs",
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        "/api/jobs",
        json=payload,
    )

    assert second.status_code == 409


def test_get_job(client):
    payload = job_payload(
        "JOB-API-GET"
    )

    create_response = client.post(
        "/api/jobs",
        json=payload,
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/jobs/JOB-API-GET"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == "JOB-API-GET"
    assert data["required_skills"] == [
        "Python",
        "FastAPI",
    ]


def test_get_missing_job_returns_404(client):
    response = client.get(
        "/api/jobs/JOB-DOES-NOT-EXIST"
    )

    assert response.status_code == 404

    assert "not found" in (
        response.json()["detail"].lower()
    )


def test_list_jobs(client):
    client.post(
        "/api/jobs",
        json=job_payload("JOB-API-LIST-001"),
    )

    client.post(
        "/api/jobs",
        json=job_payload("JOB-API-LIST-002"),
    )

    response = client.get(
        "/api/jobs"
    )

    assert response.status_code == 200

    data = response.json()

    ids = {
        job["job_id"]
        for job in data
    }

    assert "JOB-API-LIST-001" in ids
    assert "JOB-API-LIST-002" in ids