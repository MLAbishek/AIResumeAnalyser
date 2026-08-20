"""
Focused test for LLM explanation propagation through the full stack:

    ScreeningService (LLM narrative attached)
        -> ScreeningPersistenceService (persisted verbatim)
        -> GET /api/jobs/{job_id}/applications/{application_id}
        -> API response's screening.explanation field

This is "Test 5 - API propagation" from the LLM explanation
integration task: confirms the LLM-generated narrative is not lost
between being generated and reaching the API response the frontend
reads (FeedbackPanel's "AI Match Feedback" section).

The OpenRouter network call itself is mocked here (no live API key
required) - app/services/test_screening_service_llm_integration.py
already covers the LLM integration point in isolation; this test
covers the persistence/serialization boundary that file does not
exercise.
"""

import io

from app.auth.models import User
from app.auth.password import hash_password
from app.core.config import settings
from app.services.llm_service import LLMExplanationService


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


def _create_job(client, headers, job_id):
    response = client.post(
        "/api/jobs",
        json={
            "job_id": job_id,
            "title": "Backend Engineer",
            "raw_text": (
                "Backend Engineer with Python and SQL experience."
            ),
            "required_skills": ["Python", "SQL"],
        },
        headers=headers,
    )

    assert response.status_code == 201, response.text
    return response.json()


def _upload_txt_resume(client, headers):
    resume_text = (
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


def test_llm_narrative_reaches_the_api_response(
    client, db, monkeypatch
):
    # Override the test-suite-wide "LLM disabled" default for this
    # one test, and stub the network call itself so no live request
    # is made - this isolates the persistence/serialization
    # plumbing (the thing this test targets) from the LLM provider
    # integration itself (already covered by
    # test_screening_service_llm_integration.py).
    monkeypatch.setattr(settings, "enable_llm_explanations", True)
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")

    monkeypatch.setattr(
        LLMExplanationService,
        "generate_explanation",
        lambda self, context: (
            "The candidate's Python and SQL skills directly match "
            "the job's required skills."
        ),
    )

    _, recruiter_headers = _register_and_login(
        client, db, "llm-propagation-recruiter@example.com", "recruiter"
    )
    _, candidate_headers = _register_and_login(
        client, db, "llm-propagation-candidate@example.com", "candidate"
    )

    job = _create_job(client, recruiter_headers, "llm-propagation-job-1")
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
    screening = response.json()["screening"]

    assert screening is not None
    assert screening["explanation"] is not None
    assert screening["explanation"]["narrative_source"] == "llm"
    assert screening["explanation"]["narrative"] == (
        "The candidate's Python and SQL skills directly match "
        "the job's required skills."
    )

    # The LLM only supplied the narrative text - it must not have
    # touched the canonical deterministic result.
    assert screening["eligible"] is True
    assert screening["final_score"] is not None
