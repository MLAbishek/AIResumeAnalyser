import io

from app.auth.models import User
from app.auth.password import hash_password
from app.database.crud.applications import (
    get_application_for_candidate_job,
)
from app.database.models.job import Job


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
        "title": "Frontend Engineer",
        "raw_text": (
            "Frontend Engineer with React and TypeScript "
            "experience. 12 months minimum."
        ),
        "required_skills": ["React", "TypeScript"],
        "required_experience_months": 12,
    }
    payload.update(overrides)

    response = client.post(
        "/api/jobs", json=payload, headers=headers
    )

    assert response.status_code == 201, response.text

    return response.json()


def _upload_resume(client, headers):
    resume_text = (
        b"Jamie Doe\n\n"
        b"SUMMARY\nFrontend engineer.\n\n"
        b"SKILLS\nReact, TypeScript\n\n"
        b"EXPERIENCE\n"
        b"Frontend Engineer at Acme\n"
        b"January 2022 - January 2024\n"
        b"Built React apps.\n\n"
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


class TestAuthRoles:
    def test_recruiter_registration_gets_recruiter_role(
        self, client
    ):
        response = client.post(
            "/api/auth/register",
            json={
                "email": "role-recruiter@example.com",
                "password": "StrongPassword123!",
                "role": "recruiter",
            },
        )

        assert response.status_code == 201
        assert response.json()["role"] == "recruiter"

    def test_candidate_registration_gets_candidate_role(
        self, client
    ):
        response = client.post(
            "/api/auth/register",
            json={
                "email": "role-candidate@example.com",
                "password": "StrongPassword123!",
                "role": "candidate",
            },
        )

        assert response.status_code == 201
        assert response.json()["role"] == "candidate"

    def test_admin_self_registration_is_rejected(
        self, client
    ):
        response = client.post(
            "/api/auth/register",
            json={
                "email": "role-admin-attempt@example.com",
                "password": "StrongPassword123!",
                "role": "admin",
            },
        )

        # RegisterRequest.role is a closed Literal that does not
        # include "admin" - Pydantic rejects it outright.
        assert response.status_code == 422


class TestCandidateJourney:
    def test_full_candidate_journey(self, client, db):
        _, recruiter_headers = _register_and_login(
            client, db, "journey-recruiter@example.com", "recruiter"
        )
        candidate_user, candidate_headers = (
            _register_and_login(
                client,
                db,
                "journey-candidate@example.com",
                "candidate",
            )
        )

        job = _create_job(
            client, recruiter_headers, "journey-job-1"
        )
        assert job["status"] == "open"

        # Candidate sees only open jobs.
        available = client.get(
            "/api/candidate/jobs", headers=candidate_headers
        )
        assert available.status_code == 200
        assert any(
            j["job_id"] == "journey-job-1"
            for j in available.json()
        )

        resume = _upload_resume(
            client, candidate_headers
        )
        assert resume["total_experience_months"] == 24

        preview = client.post(
            "/api/candidate/jobs/journey-job-1/preview",
            json={"resume_id": resume["resume_id"]},
            headers=candidate_headers,
        )
        assert preview.status_code == 200
        preview_data = preview.json()

        # Real pipeline output - not a random/fabricated score.
        assert preview_data["eligible"] is True
        assert preview_data["ranking"] is not None
        assert 0 <= preview_data["final_score"] <= 100

        apply_response = client.post(
            "/api/candidate/jobs/journey-job-1/apply",
            json={"resume_id": resume["resume_id"]},
            headers=candidate_headers,
        )
        assert apply_response.status_code == 201
        application = apply_response.json()
        assert application["status"] == "applied"
        assert application["screening"]["screening_id"] == (
            preview_data["screening_id"]
        )

        # Duplicate application rejected.
        duplicate = client.post(
            "/api/candidate/jobs/journey-job-1/apply",
            json={"resume_id": resume["resume_id"]},
            headers=candidate_headers,
        )
        assert duplicate.status_code == 409

        # Recruiter sees exactly one application, ranked.
        job_apps = client.get(
            "/api/jobs/journey-job-1/applications",
            headers=recruiter_headers,
        )
        assert job_apps.status_code == 200
        job_apps_data = job_apps.json()
        assert job_apps_data["total_applications"] == 1
        assert (
            job_apps_data["results"][0]["candidate_name"]
            == "Jamie Doe"
        )

        application_id = application["application_id"]

        detail = client.get(
            f"/api/jobs/journey-job-1/applications/{application_id}",
            headers=recruiter_headers,
        )
        assert detail.status_code == 200
        assert detail.json()["screening"]["ranking"][
            "skill_score"
        ] == 1.0

        # Recruiter shortlists the candidate.
        status_update = client.patch(
            f"/api/applications/{application_id}/status",
            json={"status": "shortlisted"},
            headers=recruiter_headers,
        )
        assert status_update.status_code == 200
        assert status_update.json()["status"] == "shortlisted"

        # Candidate sees the updated status and feedback.
        my_apps = client.get(
            "/api/candidate/applications",
            headers=candidate_headers,
        )
        assert my_apps.status_code == 200
        assert my_apps.json()[0]["status"] == "shortlisted"

        my_app_detail = client.get(
            f"/api/candidate/applications/{application_id}",
            headers=candidate_headers,
        )
        assert my_app_detail.status_code == 200
        assert (
            my_app_detail.json()["screening"]["explanation"]
            is not None
        )

        # Recruiter closes the job.
        close = client.post(
            "/api/jobs/journey-job-1/close",
            headers=recruiter_headers,
        )
        assert close.status_code == 200
        assert close.json()["status"] == "closed"

        # Candidate can no longer apply (already applied anyway,
        # but a second candidate must also be rejected).
        _, other_candidate_headers = _register_and_login(
            client,
            db,
            "journey-candidate-2@example.com",
            "candidate",
        )
        other_resume = _upload_resume(
            client, other_candidate_headers
        )

        rejected = client.post(
            "/api/candidate/jobs/journey-job-1/apply",
            json={"resume_id": other_resume["resume_id"]},
            headers=other_candidate_headers,
        )
        assert rejected.status_code == 409

        # Existing application/feedback remains visible.
        still_visible = client.get(
            f"/api/candidate/applications/{application_id}",
            headers=candidate_headers,
        )
        assert still_visible.status_code == 200
        assert still_visible.json()["status"] == "shortlisted"


class TestSecurity:
    def test_candidate_cannot_access_recruiter_endpoint(
        self, client, db
    ):
        _, recruiter_headers = _register_and_login(
            client, db, "sec-recruiter@example.com", "recruiter"
        )
        _, candidate_headers = _register_and_login(
            client, db, "sec-candidate@example.com", "candidate"
        )

        _create_job(client, recruiter_headers, "sec-job-1")

        response = client.get(
            "/api/jobs/sec-job-1/applications",
            headers=candidate_headers,
        )

        assert response.status_code == 403

    def test_recruiter_b_cannot_manage_recruiter_a_job(
        self, client, db
    ):
        _, headers_a = _register_and_login(
            client, db, "sec-recruiter-a@example.com", "recruiter"
        )
        _, headers_b = _register_and_login(
            client, db, "sec-recruiter-b@example.com", "recruiter"
        )

        _create_job(client, headers_a, "sec-job-2")

        close_attempt = client.post(
            "/api/jobs/sec-job-2/close", headers=headers_b
        )
        assert close_attempt.status_code == 403

        list_attempt = client.get(
            "/api/jobs/sec-job-2/applications",
            headers=headers_b,
        )
        assert list_attempt.status_code == 403

    def test_candidate_cannot_access_another_candidates_application(
        self, client, db
    ):
        _, recruiter_headers = _register_and_login(
            client, db, "sec-recruiter-c@example.com", "recruiter"
        )
        _, candidate_a_headers = _register_and_login(
            client, db, "sec-candidate-a@example.com", "candidate"
        )
        _, candidate_b_headers = _register_and_login(
            client, db, "sec-candidate-b@example.com", "candidate"
        )

        _create_job(client, recruiter_headers, "sec-job-3")
        resume = _upload_resume(client, candidate_a_headers)

        apply_response = client.post(
            "/api/candidate/jobs/sec-job-3/apply",
            json={"resume_id": resume["resume_id"]},
            headers=candidate_a_headers,
        )
        application_id = apply_response.json()[
            "application_id"
        ]

        response = client.get(
            f"/api/candidate/applications/{application_id}",
            headers=candidate_b_headers,
        )

        assert response.status_code == 404

    def test_candidate_cannot_apply_to_closed_job(
        self, client, db
    ):
        _, recruiter_headers = _register_and_login(
            client, db, "sec-recruiter-d@example.com", "recruiter"
        )
        _, candidate_headers = _register_and_login(
            client, db, "sec-candidate-d@example.com", "candidate"
        )

        _create_job(client, recruiter_headers, "sec-job-4")
        client.post(
            "/api/jobs/sec-job-4/close",
            headers=recruiter_headers,
        )

        resume = _upload_resume(client, candidate_headers)

        response = client.post(
            "/api/candidate/jobs/sec-job-4/apply",
            json={"resume_id": resume["resume_id"]},
            headers=candidate_headers,
        )

        assert response.status_code == 409

    def test_candidate_cannot_set_own_status_to_shortlisted(
        self, client, db
    ):
        _, recruiter_headers = _register_and_login(
            client, db, "sec-recruiter-e@example.com", "recruiter"
        )
        _, candidate_headers = _register_and_login(
            client, db, "sec-candidate-e@example.com", "candidate"
        )

        _create_job(client, recruiter_headers, "sec-job-5")
        resume = _upload_resume(client, candidate_headers)

        apply_response = client.post(
            "/api/candidate/jobs/sec-job-5/apply",
            json={"resume_id": resume["resume_id"]},
            headers=candidate_headers,
        )
        application_id = apply_response.json()[
            "application_id"
        ]

        response = client.patch(
            f"/api/applications/{application_id}/status",
            json={"status": "shortlisted"},
            headers=candidate_headers,
        )

        assert response.status_code == 403

    def test_unauthenticated_apply_is_rejected(
        self, client, db
    ):
        _, recruiter_headers = _register_and_login(
            client, db, "sec-recruiter-f@example.com", "recruiter"
        )
        _create_job(client, recruiter_headers, "sec-job-6")

        # The `client` fixture pre-authenticates as an admin test
        # user by default - remove that to genuinely simulate an
        # unauthenticated caller.
        del client.headers["Authorization"]

        response = client.post(
            "/api/candidate/jobs/sec-job-6/apply",
            json={"resume_id": "does-not-matter"},
        )

        assert response.status_code == 401

    def test_invalid_file_type_is_rejected(self, client, db):
        _, candidate_headers = _register_and_login(
            client, db, "sec-candidate-g@example.com", "candidate"
        )

        response = client.post(
            "/api/candidate/resumes/upload",
            files={
                "file": (
                    "resume.exe",
                    io.BytesIO(b"not a resume"),
                    "application/octet-stream",
                )
            },
            headers=candidate_headers,
        )

        assert response.status_code == 415

    def test_candidate_cannot_upload_using_another_candidates_resume(
        self, client, db
    ):
        _, recruiter_headers = _register_and_login(
            client, db, "sec-recruiter-h@example.com", "recruiter"
        )
        _, candidate_a_headers = _register_and_login(
            client, db, "sec-candidate-h1@example.com", "candidate"
        )
        _, candidate_b_headers = _register_and_login(
            client, db, "sec-candidate-h2@example.com", "candidate"
        )

        _create_job(client, recruiter_headers, "sec-job-7")
        resume = _upload_resume(client, candidate_a_headers)

        response = client.post(
            "/api/candidate/jobs/sec-job-7/preview",
            json={"resume_id": resume["resume_id"]},
            headers=candidate_b_headers,
        )

        assert response.status_code == 403

    def test_job_deletion_blocked_when_applications_exist(
        self, client, db
    ):
        _, recruiter_headers = _register_and_login(
            client, db, "sec-recruiter-i@example.com", "recruiter"
        )
        _, candidate_headers = _register_and_login(
            client, db, "sec-candidate-i@example.com", "candidate"
        )

        _create_job(client, recruiter_headers, "sec-job-8")
        resume = _upload_resume(client, candidate_headers)

        client.post(
            "/api/candidate/jobs/sec-job-8/apply",
            json={"resume_id": resume["resume_id"]},
            headers=candidate_headers,
        )

        response = client.delete(
            "/api/jobs/sec-job-8", headers=recruiter_headers
        )

        assert response.status_code == 409

    def test_legacy_job_without_owner_is_manageable_by_any_recruiter(
        self, client, db
    ):
        job = Job(
            job_id="legacy-job-no-owner",
            raw_text="Legacy job created before ownership existed.",
            required_skills=[],
            preferred_skills=[],
            required_technologies=[],
            preferred_technologies=[],
            education_requirements=[],
            required_certifications=[],
            required_experience_months=0,
            created_by_user_id=None,
        )
        db.add(job)
        db.commit()

        _, recruiter_headers = _register_and_login(
            client, db, "sec-recruiter-j@example.com", "recruiter"
        )

        response = client.post(
            "/api/jobs/legacy-job-no-owner/close",
            headers=recruiter_headers,
        )

        assert response.status_code == 200


class TestApplicationRankingOrder:
    def test_recruiter_list_is_ordered_by_match_score_not_application_order(
        self, client, db
    ):
        """
        Each candidate is screened individually when they apply
        through the portal, so `RankingResult.rank` is never
        populated for these applications. The recruiter-facing
        list must still reflect true match quality (score,
        descending) rather than silently falling back to
        insertion/application order.
        """

        _, recruiter_headers = _register_and_login(
            client,
            db,
            "rank-order-recruiter@example.com",
            "recruiter",
        )
        _, weak_headers = _register_and_login(
            client,
            db,
            "rank-order-weak@example.com",
            "candidate",
        )
        _, strong_headers = _register_and_login(
            client,
            db,
            "rank-order-strong@example.com",
            "candidate",
        )

        _create_job(
            client,
            recruiter_headers,
            "rank-order-job-1",
            raw_text=(
                "Backend Engineer role requiring React and "
                "TypeScript. 12 months minimum."
            ),
            required_skills=["React", "TypeScript"],
            required_experience_months=12,
        )

        weak_resume_text = (
            b"Sam Weak\n\n"
            b"SUMMARY\nJunior marketing assistant.\n\n"
            b"SKILLS\nExcel, PowerPoint\n\n"
            b"EXPERIENCE\n"
            b"Marketing Intern at SmallCo\n"
            b"January 2023 - June 2023\n"
            b"Assisted with campaigns.\n\n"
            b"EDUCATION\nBA Marketing\nCity College\n"
            b"2019 - 2023\n"
        )
        strong_resume_text = (
            b"Alex Strong\n\n"
            b"SUMMARY\nSenior frontend engineer.\n\n"
            b"SKILLS\nReact, TypeScript, JavaScript\n\n"
            b"EXPERIENCE\n"
            b"Senior Frontend Engineer at BigCo\n"
            b"January 2018 - January 2024\n"
            b"Built large scale React applications.\n\n"
            b"EDUCATION\nMSc Computer Science\n"
            b"State University\n2014 - 2018\n"
        )

        # The weaker/ineligible candidate applies FIRST, so a
        # sort that fell back to application order would rank
        # them ahead of the stronger candidate.
        weak_resume = client.post(
            "/api/candidate/resumes/upload",
            files={
                "file": (
                    "weak.txt",
                    io.BytesIO(weak_resume_text),
                    "text/plain",
                )
            },
            headers=weak_headers,
        ).json()

        strong_resume = client.post(
            "/api/candidate/resumes/upload",
            files={
                "file": (
                    "strong.txt",
                    io.BytesIO(strong_resume_text),
                    "text/plain",
                )
            },
            headers=strong_headers,
        ).json()

        weak_apply = client.post(
            "/api/candidate/jobs/rank-order-job-1/apply",
            json={"resume_id": weak_resume["resume_id"]},
            headers=weak_headers,
        )
        assert weak_apply.status_code == 201

        strong_apply = client.post(
            "/api/candidate/jobs/rank-order-job-1/apply",
            json={"resume_id": strong_resume["resume_id"]},
            headers=strong_headers,
        )
        assert strong_apply.status_code == 201

        weak_score = weak_apply.json()["screening"][
            "final_score"
        ]
        strong_score = strong_apply.json()["screening"][
            "final_score"
        ]
        assert strong_score > weak_score

        listing = client.get(
            "/api/jobs/rank-order-job-1/applications",
            headers=recruiter_headers,
        )
        assert listing.status_code == 200

        results = listing.json()["results"]
        assert [r["candidate_name"] for r in results] == [
            "Alex Strong",
            "Sam Weak",
        ]
