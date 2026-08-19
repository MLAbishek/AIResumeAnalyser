"""
End-to-end persistence verification using the actual, real fixture
documents (data/raw/resumes/resume_001.pdf and data/raw/jd/jd001.pdf)
- not synthetic text. These tests upload the real files through the
real API, hit the real parsing pipeline, and assert on the actual
extracted values (not just "a value exists") both directly against
the database and against the API response, to prove no field is
silently lost between the parser and the client.
"""

import io

from app.auth.models import User
from app.auth.password import hash_password
from app.database.models.job import Job
from app.database.models.resume import Resume


RESUME_PDF_FIXTURE = "data/raw/resumes/resume_001.pdf"
JD_PDF_FIXTURE = "data/raw/jd/jd001.pdf"


def _register_and_login(client, db, email, role):
    password = "StrongPassword123!"

    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )

    token = login.json()["access_token"]

    return user, {"Authorization": f"Bearer {token}"}


class TestRealResumePersistence:
    def test_resume_001_pdf_structured_fields_survive_parser_to_db_to_api(
        self, client, db
    ):
        _, headers = _register_and_login(
            client,
            db,
            "real-resume-candidate@example.com",
            "candidate",
        )

        with open(RESUME_PDF_FIXTURE, "rb") as fh:
            response = client.post(
                "/api/candidate/resumes/upload",
                files={
                    "file": (
                        "resume_001.pdf",
                        fh,
                        "application/pdf",
                    )
                },
                headers=headers,
            )

        assert response.status_code == 201, response.text
        body = response.json()

        # --- API response: correct, non-fabricated structured data ---
        assert body["name"] == "Abishek J"
        assert "Python" in body["skills"]
        assert "TensorFlow" in body["skills"]
        assert body["phone"] is None  # genuinely absent - not fabricated

        roles = {exp["job_title"] for exp in body["experiences"]}
        companies = {exp["company"] for exp in body["experiences"]}
        assert "Deep Learning Intern" in roles
        assert "Authenta AI" in companies
        assert "AI Research Intern" in roles
        assert "Foviatech" in companies

        degrees = {edu["degree"] for edu in body["education"]}
        institutions = {edu["institution"] for edu in body["education"]}
        assert "B.Tech" in degrees
        assert any(
            "St. Joseph" in institution
            for institution in institutions
        )

        project_names = {p["name"] for p in body["projects"]}
        assert (
            "AI-Based Workplace Behavior Monitoring System"
            in project_names
        )
        assert "Skin Disease Detector" in project_names

        # This resume genuinely has no certifications section - the
        # honest empty list, not a fabricated one.
        assert body["certifications"] == []

        # --- Database: the same data actually persisted, not just
        # returned transiently in the response ---
        resume = (
            db.query(Resume)
            .filter(Resume.resume_id == body["resume_id"])
            .first()
        )

        assert resume is not None
        assert resume.name == "Abishek J"
        assert "Python" in resume.skills
        assert len(resume.experiences) == 2
        assert len(resume.education) == 1
        assert len(resume.projects) == 2
        db_project_names = {p.name for p in resume.projects}
        assert (
            "AI-Based Workplace Behavior Monitoring System"
            in db_project_names
        )

        # --- Refetch via the recruiter-facing GET API to confirm the
        # persisted data (not just the upload response) round-trips
        # correctly all the way through a second, independent request ---
        _, recruiter_headers = _register_and_login(
            client,
            db,
            "real-resume-recruiter@example.com",
            "recruiter",
        )
        get_response = client.get(
            f"/api/resumes/{body['resume_id']}",
            headers=recruiter_headers,
        )

        assert get_response.status_code == 200
        refetched = get_response.json()
        assert refetched["name"] == "Abishek J"
        refetched_project_names = {
            p["name"] for p in refetched["projects"]
        }
        assert (
            "Skin Disease Detector" in refetched_project_names
        )


class TestRealJobDescriptionPersistence:
    def test_jd001_pdf_structured_fields_survive_parser_to_db_to_api(
        self, client, db
    ):
        _, headers = _register_and_login(
            client,
            db,
            "real-jd-recruiter@example.com",
            "recruiter",
        )

        with open(JD_PDF_FIXTURE, "rb") as fh:
            response = client.post(
                "/api/jobs/upload",
                data={"title": "Java Developer Intern"},
                files={
                    "file": (
                        "jd001.pdf",
                        fh,
                        "application/pdf",
                    )
                },
                headers=headers,
            )

        assert response.status_code == 201, response.text
        body = response.json()

        # --- API response: correct, non-fabricated structured data ---
        assert body["title"] == "Java Developer Intern"
        assert body["location"] == "Chennai, Work from Office"
        assert body["job_type"] is not None
        assert body["job_type"].lower() == "full-time"

        assert any(
            "Java fundamentals" in skill
            for skill in body["required_skills"]
        )
        assert not any(
            "●" in skill for skill in body["required_skills"]
        )

        assert len(body["responsibilities"]) > 0
        assert any(
            "Java code" in item
            for item in body["responsibilities"]
        )

        education_descriptions = [
            req.get("description", "")
            for req in body["education_requirements"]
        ]
        assert any(
            "B.E." in desc or "B.Tech" in desc
            for desc in education_descriptions
        )

        # --- Database: the same data actually persisted ---
        job = (
            db.query(Job)
            .filter(Job.job_id == body["job_id"])
            .first()
        )

        assert job is not None
        assert job.location == "Chennai, Work from Office"
        assert len(job.required_skills) > 0
        assert len(job.responsibilities) > 0
        assert len(job.education_requirements) > 0

        # --- Refetch via the GET API to confirm persisted data
        # round-trips correctly, not just the creation response ---
        get_response = client.get(
            f"/api/jobs/{body['job_id']}", headers=headers
        )

        assert get_response.status_code == 200
        refetched = get_response.json()
        assert refetched["location"] == "Chennai, Work from Office"
        assert len(refetched["responsibilities"]) > 0
