from datetime import date

from app.database.crud.resumes import get_resume_by_id


def resume_payload(
    resume_id="RESUME-API-001",
):
    return {
        "resume_id": resume_id,
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "9876543210",
        "summary": "Python backend developer.",
        "skills": [
            "Python",
            "FastAPI",
            "PostgreSQL",
        ],
        "job_titles": [
            "Backend Developer",
        ],
        "organizations": [
            "ABC Technologies",
        ],
        "technologies": [
            "FastAPI",
            "PostgreSQL",
            "Docker",
        ],
        "total_experience_months": 36,
        "raw_text": (
            "Python backend developer with "
            "three years of experience."
        ),
        "experiences": [
            {
                "job_title": "Backend Developer",
                "company": "ABC Technologies",
                "start_date": "2021-01-01",
                "end_date": "2024-01-01",
                "duration_months": 36,
            }
        ],
        "education": [
            {
                "degree": "B.Tech",
                "institution": "XYZ University",
                "field_of_study": "Computer Science",
                "start_date": "2017-06-01",
                "end_date": "2021-05-01",
            }
        ],
    }


def test_create_resume(client, db):
    response = client.post(
        "/api/resumes",
        json=resume_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["resume_id"] == "RESUME-API-001"
    assert data["name"] == "John Doe"
    assert "Python" in data["skills"]
    assert data["total_experience_months"] == 36

    assert len(data["experiences"]) == 1
    assert data["experiences"][0]["company"] == (
        "ABC Technologies"
    )

    assert len(data["education"]) == 1
    assert data["education"][0]["degree"] == "B.Tech"

    resume = get_resume_by_id(
        db,
        "RESUME-API-001",
    )

    assert resume is not None
    assert resume.name == "John Doe"


def test_create_duplicate_resume_returns_409(client):
    payload = resume_payload(
        "RESUME-API-DUPLICATE"
    )

    first = client.post(
        "/api/resumes",
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        "/api/resumes",
        json=payload,
    )

    assert second.status_code == 409


def test_get_resume(client):
    response = client.post(
        "/api/resumes",
        json=resume_payload(
            "RESUME-API-GET"
        ),
    )

    assert response.status_code == 201

    response = client.get(
        "/api/resumes/RESUME-API-GET"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["resume_id"] == "RESUME-API-GET"
    assert data["email"] == "john@example.com"
    assert len(data["experiences"]) == 1
    assert len(data["education"]) == 1


def test_get_missing_resume_returns_404(client):
    response = client.get(
        "/api/resumes/RESUME-DOES-NOT-EXIST"
    )

    assert response.status_code == 404

    assert "not found" in (
        response.json()["detail"].lower()
    )


def test_list_resumes(client):
    client.post(
        "/api/resumes",
        json=resume_payload(
            "RESUME-API-LIST-001"
        ),
    )

    client.post(
        "/api/resumes",
        json=resume_payload(
            "RESUME-API-LIST-002"
        ),
    )

    response = client.get(
        "/api/resumes"
    )

    assert response.status_code == 200

    data = response.json()

    ids = {
        resume["resume_id"]
        for resume in data
    }

    assert "RESUME-API-LIST-001" in ids
    assert "RESUME-API-LIST-002" in ids