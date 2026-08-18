import io

from docx import Document

from app.auth.models import User
from app.auth.password import hash_password
from app.database.models.job import Job


PDF_FIXTURE = "data/raw/jd/jd001.pdf"


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


def _make_docx_bytes(paragraphs: list[str]) -> bytes:
    document = Document()

    for paragraph in paragraphs:
        document.add_paragraph(paragraph)

    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)

    return buffer.read()


class TestJobUploadHappyPath:
    def test_recruiter_can_create_job_with_txt_jd(
        self, client, db
    ):
        _, headers = _register_and_login(
            client, db, "jd-txt-recruiter@example.com", "recruiter"
        )

        jd_text = (
            "Backend Engineer\n\n"
            "SUMMARY\nBackend role using Python and FastAPI.\n\n"
            "REQUIRED SKILLS\nPython, FastAPI\n"
        )

        response = client.post(
            "/api/jobs/upload",
            data={"title": "Backend Engineer"},
            files={
                "file": (
                    "backend-jd.txt",
                    io.BytesIO(jd_text.encode("utf-8")),
                    "text/plain",
                )
            },
            headers=headers,
        )

        assert response.status_code == 201, response.text

        body = response.json()

        assert body["title"] == "Backend Engineer"
        assert body["status"] == "open"
        assert "Python and FastAPI" in body["raw_text"]

        job = (
            db.query(Job)
            .filter(Job.job_id == body["job_id"])
            .first()
        )

        assert job is not None
        assert job.raw_text == body["raw_text"]
        assert "Python and FastAPI" in job.raw_text

    def test_recruiter_can_create_job_with_pdf_jd(
        self, client, db
    ):
        _, headers = _register_and_login(
            client, db, "jd-pdf-recruiter@example.com", "recruiter"
        )

        with open(PDF_FIXTURE, "rb") as fh:
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

        assert body["title"] == "Java Developer Intern"
        assert len(body["raw_text"]) > 0

        job = (
            db.query(Job)
            .filter(Job.job_id == body["job_id"])
            .first()
        )

        assert job is not None
        assert job.raw_text == body["raw_text"]

    def test_recruiter_can_create_job_with_docx_jd(
        self, client, db
    ):
        _, headers = _register_and_login(
            client, db, "jd-docx-recruiter@example.com", "recruiter"
        )

        docx_bytes = _make_docx_bytes(
            [
                "Data Analyst",
                "SUMMARY",
                "Analyze large datasets using SQL and Python.",
                "REQUIRED SKILLS",
                "SQL, Python, Excel",
            ]
        )

        response = client.post(
            "/api/jobs/upload",
            data={"title": "Data Analyst"},
            files={
                "file": (
                    "data-analyst-jd.docx",
                    io.BytesIO(docx_bytes),
                    (
                        "application/vnd.openxmlformats-"
                        "officedocument.wordprocessingml.document"
                    ),
                )
            },
            headers=headers,
        )

        assert response.status_code == 201, response.text

        body = response.json()

        assert "Analyze large datasets" in body["raw_text"]
        assert "SQL, Python, Excel" in body["raw_text"]

    def test_uploaded_job_ownership_matches_authenticated_recruiter(
        self, client, db
    ):
        user, headers = _register_and_login(
            client,
            db,
            "jd-ownership-recruiter@example.com",
            "recruiter",
        )

        response = client.post(
            "/api/jobs/upload",
            data={"title": "Ownership Check"},
            files={
                "file": (
                    "jd.txt",
                    io.BytesIO(b"Some job description text."),
                    "text/plain",
                )
            },
            headers=headers,
        )

        job_id = response.json()["job_id"]

        job = (
            db.query(Job)
            .filter(Job.job_id == job_id)
            .first()
        )

        assert job.created_by_user_id == user.id

    def test_uploaded_job_appears_in_recruiter_job_list(
        self, client, db
    ):
        _, headers = _register_and_login(
            client, db, "jd-list-recruiter@example.com", "recruiter"
        )

        response = client.post(
            "/api/jobs/upload",
            data={"title": "Listed Job"},
            files={
                "file": (
                    "jd.txt",
                    io.BytesIO(b"Some job description text."),
                    "text/plain",
                )
            },
            headers=headers,
        )

        job_id = response.json()["job_id"]

        listing = client.get("/api/jobs", headers=headers)

        ids = {job["job_id"] for job in listing.json()}

        assert job_id in ids

    def test_uploaded_job_appears_in_candidate_open_jobs(
        self, client, db
    ):
        _, recruiter_headers = _register_and_login(
            client,
            db,
            "jd-candidate-visible-recruiter@example.com",
            "recruiter",
        )
        _, candidate_headers = _register_and_login(
            client,
            db,
            "jd-candidate-visible-candidate@example.com",
            "candidate",
        )

        response = client.post(
            "/api/jobs/upload",
            data={"title": "Visible To Candidates"},
            files={
                "file": (
                    "jd.txt",
                    io.BytesIO(b"Some job description text."),
                    "text/plain",
                )
            },
            headers=recruiter_headers,
        )

        job_id = response.json()["job_id"]

        candidate_jobs = client.get(
            "/api/candidate/jobs", headers=candidate_headers
        )

        ids = {
            job["job_id"] for job in candidate_jobs.json()
        }

        assert job_id in ids


class TestJobUploadSecurity:
    def test_candidate_cannot_upload_a_job(self, client, db):
        _, headers = _register_and_login(
            client, db, "jd-sec-candidate@example.com", "candidate"
        )

        response = client.post(
            "/api/jobs/upload",
            data={"title": "Should Fail"},
            files={
                "file": (
                    "jd.txt",
                    io.BytesIO(b"Some job description text."),
                    "text/plain",
                )
            },
            headers=headers,
        )

        assert response.status_code == 403

    def test_unauthenticated_upload_rejected(self, client):
        del client.headers["Authorization"]

        response = client.post(
            "/api/jobs/upload",
            data={"title": "Should Fail"},
            files={
                "file": (
                    "jd.txt",
                    io.BytesIO(b"Some job description text."),
                    "text/plain",
                )
            },
        )

        assert response.status_code == 401

    def test_unsupported_extension_rejected_with_415(
        self, client, db
    ):
        _, headers = _register_and_login(
            client, db, "jd-ext-recruiter@example.com", "recruiter"
        )

        response = client.post(
            "/api/jobs/upload",
            data={"title": "Bad Extension"},
            files={
                "file": (
                    "jd.exe",
                    io.BytesIO(b"not a real jd"),
                    "application/octet-stream",
                )
            },
            headers=headers,
        )

        assert response.status_code == 415
        assert "PDF, DOCX, TXT" in response.json()["detail"]

    def test_oversized_file_rejected_with_413(
        self, client, db
    ):
        _, headers = _register_and_login(
            client, db, "jd-size-recruiter@example.com", "recruiter"
        )

        oversized = b"x" * (10 * 1024 * 1024 + 1)

        response = client.post(
            "/api/jobs/upload",
            data={"title": "Too Big"},
            files={
                "file": (
                    "jd.txt",
                    io.BytesIO(oversized),
                    "text/plain",
                )
            },
            headers=headers,
        )

        assert response.status_code == 413
        assert "10 MB" in response.json()["detail"]

    def test_empty_document_rejected_with_400(
        self, client, db
    ):
        _, headers = _register_and_login(
            client, db, "jd-empty-recruiter@example.com", "recruiter"
        )

        response = client.post(
            "/api/jobs/upload",
            data={"title": "Empty"},
            files={
                "file": (
                    "jd.txt",
                    io.BytesIO(b""),
                    "text/plain",
                )
            },
            headers=headers,
        )

        assert response.status_code == 400
        assert "readable text" in response.json()["detail"]

    def test_malformed_docx_handled_safely_with_400(
        self, client, db
    ):
        _, headers = _register_and_login(
            client,
            db,
            "jd-malformed-recruiter@example.com",
            "recruiter",
        )

        response = client.post(
            "/api/jobs/upload",
            data={"title": "Corrupted"},
            files={
                "file": (
                    "corrupted.docx",
                    io.BytesIO(
                        b"This is not a valid DOCX file at all."
                    ),
                    (
                        "application/vnd.openxmlformats-"
                        "officedocument.wordprocessingml.document"
                    ),
                )
            },
            headers=headers,
        )

        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "Traceback" not in detail
        assert "readable text" in detail

    def test_no_job_created_when_upload_fails(
        self, client, db
    ):
        _, headers = _register_and_login(
            client,
            db,
            "jd-no-orphan-recruiter@example.com",
            "recruiter",
        )

        before = db.query(Job).count()

        client.post(
            "/api/jobs/upload",
            data={"title": "Should Not Persist"},
            files={
                "file": (
                    "jd.txt",
                    io.BytesIO(b""),
                    "text/plain",
                )
            },
            headers=headers,
        )

        after = db.query(Job).count()

        assert after == before


class TestExistingJobCreationUnaffected:
    def test_existing_text_based_job_creation_still_works(
        self, client, db
    ):
        _, headers = _register_and_login(
            client,
            db,
            "jd-regression-recruiter@example.com",
            "recruiter",
        )

        response = client.post(
            "/api/jobs",
            json={
                "job_id": "jd-regression-job-1",
                "title": "Regression Check",
                "raw_text": "Existing JSON-based job creation.",
                "required_skills": ["Python"],
                "required_experience_months": 12,
            },
            headers=headers,
        )

        assert response.status_code == 201
        assert response.json()["job_id"] == (
            "jd-regression-job-1"
        )
