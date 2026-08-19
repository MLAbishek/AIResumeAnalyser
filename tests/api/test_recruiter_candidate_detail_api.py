import io

from app.auth.models import User
from app.auth.password import hash_password


PDF_RESUME_FIXTURE = "data/raw/resumes/resume_001.pdf"


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


def _create_job(client, headers, job_id, **overrides):
    payload = {
        "job_id": job_id,
        "title": "Backend Engineer",
        "raw_text": (
            "Backend Engineer with Python and SQL experience. "
            "12 months minimum."
        ),
        "required_skills": ["Python", "SQL"],
        "required_experience_months": 12,
    }
    payload.update(overrides)

    response = client.post(
        "/api/jobs", json=payload, headers=headers
    )

    assert response.status_code == 201, response.text

    return response.json()


def _upload_txt_resume(client, headers, text=None):
    resume_text = text or (
        b"Jamie Doe\n\n"
        b"SUMMARY\nBackend engineer.\n\n"
        b"SKILLS\nPython, SQL\n\n"
        b"EXPERIENCE\n"
        b"Backend Engineer at Acme\n"
        b"January 2022 - January 2024\n"
        b"Built Python services.\n\n"
        b"EDUCATION\nBSc Computer Science\nState University\n"
        b"2018 - 2022\n"
    )

    response = client.post(
        "/api/candidate/resumes/upload",
        files={
            "file": (
                "resume.txt",
                io.BytesIO(resume_text),
                "text/plain",
            )
        },
        headers=headers,
    )

    assert response.status_code == 201, response.text

    return response.json()


def _apply(client, headers, job_id, resume_id):
    response = client.post(
        f"/api/candidate/jobs/{job_id}/apply",
        json={"resume_id": resume_id},
        headers=headers,
    )

    assert response.status_code == 201, response.text

    return response.json()


class TestRecruiterCandidateDetail:
    def test_recruiter_can_access_candidate_who_applied_to_their_job(
        self, client, db
    ):
        _, recruiter_headers = _register_and_login(
            client, db, "detail-recruiter-1@example.com", "recruiter"
        )
        _, candidate_headers = _register_and_login(
            client, db, "detail-candidate-1@example.com", "candidate"
        )

        job = _create_job(client, recruiter_headers, "detail-job-1")
        resume = _upload_txt_resume(client, candidate_headers)
        application = _apply(
            client, candidate_headers, job["job_id"], resume["resume_id"]
        )

        response = client.get(
            f"/api/jobs/{job['job_id']}/applications/"
            f"{application['application_id']}",
            headers=recruiter_headers,
        )

        assert response.status_code == 200, response.text
        body = response.json()

        assert body["candidate_name"] == "Jamie Doe"
        assert (
            body["candidate_email"]
            == "detail-candidate-1@example.com"
        )
        assert body["resume"] is not None
        assert body["resume"]["skills"] == ["Python", "SQL"]
        # The candidate free-text upload path parses summary/skills
        # into the Resume row directly; structured per-role
        # ResumeExperience/ResumeEducation rows are only populated
        # via the recruiter JSON resume-creation endpoint, so these
        # stay empty lists here - still real, not fabricated, data.
        assert body["resume"]["experiences"] == []
        assert body["resume"]["education"] == []
        assert body["screening"] is not None
        assert body["screening"]["ranking"] is not None
        assert body["screening"]["gap_analysis"] is not None
        assert body["screening"]["explanation"] is not None
        assert isinstance(body["screening"]["evidence"], list)

    def test_recruiter_applicant_list_includes_skills_and_email(
        self, client, db
    ):
        _, recruiter_headers = _register_and_login(
            client, db, "detail-recruiter-2@example.com", "recruiter"
        )
        _, candidate_headers = _register_and_login(
            client, db, "detail-candidate-2@example.com", "candidate"
        )

        job = _create_job(client, recruiter_headers, "detail-job-2")
        resume = _upload_txt_resume(client, candidate_headers)
        _apply(
            client, candidate_headers, job["job_id"], resume["resume_id"]
        )

        response = client.get(
            f"/api/jobs/{job['job_id']}/applications",
            headers=recruiter_headers,
        )

        assert response.status_code == 200
        item = response.json()["results"][0]

        assert item["candidate_email"] == (
            "detail-candidate-2@example.com"
        )
        assert item["skills"] == ["Python", "SQL"]

    def test_recruiter_can_retrieve_candidates_actual_resume_file(
        self, client, db
    ):
        _, recruiter_headers = _register_and_login(
            client, db, "detail-recruiter-3@example.com", "recruiter"
        )
        _, candidate_headers = _register_and_login(
            client, db, "detail-candidate-3@example.com", "candidate"
        )

        job = _create_job(client, recruiter_headers, "detail-job-3")

        with open(PDF_RESUME_FIXTURE, "rb") as fh:
            pdf_bytes = fh.read()

        upload = client.post(
            "/api/candidate/resumes/upload",
            files={
                "file": (
                    "resume_001.pdf",
                    io.BytesIO(pdf_bytes),
                    "application/pdf",
                )
            },
            headers=candidate_headers,
        )
        assert upload.status_code == 201, upload.text
        resume = upload.json()

        application = _apply(
            client, candidate_headers, job["job_id"], resume["resume_id"]
        )

        response = client.get(
            f"/api/jobs/{job['job_id']}/applications/"
            f"{application['application_id']}/resume",
            headers=recruiter_headers,
        )

        assert response.status_code == 200, response.text
        assert response.headers["content-type"] == "application/pdf"
        # The actual uploaded bytes, byte-for-byte - not a
        # fabricated/generated document.
        assert response.content == pdf_bytes

        # No server filesystem path is ever exposed to the client -
        # only the resume_id + extension appear in the header.
        disposition = response.headers.get(
            "content-disposition", ""
        )
        assert resume["resume_id"] in disposition
        assert "C:" not in disposition
        assert "data" not in disposition
        assert "storage" not in disposition

    def test_resume_file_missing_returns_clean_404(self, client, db):
        # A resume created before this feature existed (or via the
        # legacy JSON path) has no stored raw file.
        _, recruiter_headers = _register_and_login(
            client, db, "detail-recruiter-4@example.com", "recruiter"
        )
        _, candidate_headers = _register_and_login(
            client, db, "detail-candidate-4@example.com", "candidate"
        )

        job = _create_job(client, recruiter_headers, "detail-job-4")
        resume = _upload_txt_resume(client, candidate_headers)
        application = _apply(
            client, candidate_headers, job["job_id"], resume["resume_id"]
        )

        # Simulate a resume with no stored raw file by pointing at a
        # resume_id that was never uploaded through the storage-aware
        # endpoint - use the delete-cleanup path instead: directly
        # remove the file the upload just wrote, then request it.
        from app.services.resume_document_storage import (
            get_resume_storage,
        )

        storage = get_resume_storage()
        storage.delete(resume["resume_id"])

        response = client.get(
            f"/api/jobs/{job['job_id']}/applications/"
            f"{application['application_id']}/resume",
            headers=recruiter_headers,
        )

        assert response.status_code == 404
        assert "not available" in response.json()["detail"]


class TestRecruiterCandidateDetailSecurity:
    def test_recruiter_cannot_access_candidate_through_unrelated_job(
        self, client, db
    ):
        _, recruiter_a_headers = _register_and_login(
            client, db, "sec-detail-recruiter-a@example.com", "recruiter"
        )
        _, recruiter_b_headers = _register_and_login(
            client, db, "sec-detail-recruiter-b@example.com", "recruiter"
        )
        _, candidate_headers = _register_and_login(
            client, db, "sec-detail-candidate-a@example.com", "candidate"
        )

        job_a = _create_job(
            client, recruiter_a_headers, "sec-detail-job-a"
        )
        job_b = _create_job(
            client, recruiter_b_headers, "sec-detail-job-b"
        )

        resume = _upload_txt_resume(client, candidate_headers)
        application = _apply(
            client, candidate_headers, job_a["job_id"], resume["resume_id"]
        )

        # Recruiter B tries to view the application by nesting it
        # under a job they DO own, but the application actually
        # belongs to job A.
        response = client.get(
            f"/api/jobs/{job_b['job_id']}/applications/"
            f"{application['application_id']}",
            headers=recruiter_b_headers,
        )
        assert response.status_code == 404

        resume_response = client.get(
            f"/api/jobs/{job_b['job_id']}/applications/"
            f"{application['application_id']}/resume",
            headers=recruiter_b_headers,
        )
        assert resume_response.status_code == 404

        # Recruiter B also can't reach it by (correctly) using job A's
        # id, because they don't own job A.
        wrong_owner_response = client.get(
            f"/api/jobs/{job_a['job_id']}/applications/"
            f"{application['application_id']}",
            headers=recruiter_b_headers,
        )
        assert wrong_owner_response.status_code == 403

    def test_recruiter_cannot_access_unrelated_candidates_resume_via_valid_job(
        self, client, db
    ):
        _, recruiter_headers = _register_and_login(
            client, db, "sec-detail-recruiter-c@example.com", "recruiter"
        )
        _, candidate_a_headers = _register_and_login(
            client, db, "sec-detail-candidate-b@example.com", "candidate"
        )
        _, candidate_b_headers = _register_and_login(
            client, db, "sec-detail-candidate-c@example.com", "candidate"
        )

        job = _create_job(
            client, recruiter_headers, "sec-detail-job-c"
        )
        other_job = _create_job(
            client, recruiter_headers, "sec-detail-job-d"
        )

        resume_a = _upload_txt_resume(client, candidate_a_headers)
        _apply(
            client, candidate_a_headers, job["job_id"], resume_a["resume_id"]
        )

        resume_b = _upload_txt_resume(client, candidate_b_headers)
        other_application = _apply(
            client,
            candidate_b_headers,
            other_job["job_id"],
            resume_b["resume_id"],
        )

        # Candidate B applied to a DIFFERENT job the same recruiter
        # owns - the recruiter must still only reach that application
        # through the job it actually belongs to.
        response = client.get(
            f"/api/jobs/{job['job_id']}/applications/"
            f"{other_application['application_id']}",
            headers=recruiter_headers,
        )
        assert response.status_code == 404

    def test_candidate_cannot_access_recruiter_resume_endpoint(
        self, client, db
    ):
        _, recruiter_headers = _register_and_login(
            client, db, "sec-detail-recruiter-e@example.com", "recruiter"
        )
        _, candidate_headers = _register_and_login(
            client, db, "sec-detail-candidate-e@example.com", "candidate"
        )

        job = _create_job(
            client, recruiter_headers, "sec-detail-job-e"
        )
        resume = _upload_txt_resume(client, candidate_headers)
        application = _apply(
            client, candidate_headers, job["job_id"], resume["resume_id"]
        )

        response = client.get(
            f"/api/jobs/{job['job_id']}/applications/"
            f"{application['application_id']}/resume",
            headers=candidate_headers,
        )

        assert response.status_code == 403

    def test_unauthenticated_access_to_candidate_detail_rejected(
        self, client, db
    ):
        _, recruiter_headers = _register_and_login(
            client, db, "sec-detail-recruiter-f@example.com", "recruiter"
        )
        job = _create_job(
            client, recruiter_headers, "sec-detail-job-f"
        )

        del client.headers["Authorization"]

        response = client.get(
            f"/api/jobs/{job['job_id']}/applications/1"
        )
        assert response.status_code == 401

        resume_response = client.get(
            f"/api/jobs/{job['job_id']}/applications/1/resume"
        )
        assert resume_response.status_code == 401
