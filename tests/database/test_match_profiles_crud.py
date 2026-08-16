from app.database.crud.jobs import create_job
from app.database.crud.resumes import create_resume
from app.database.crud.screening_results import (
    create_screening_result,
)
from app.database.crud.match_profiles import (
    create_match_profile,
    delete_match_profile,
    get_match_profile,
    update_match_profile,
)


def create_test_screening(db):
    job = create_job(
        db,
        job_id="JOB-PROFILE-001",
        raw_text="Backend developer",
    )

    resume = create_resume(
        db,
        resume_id="RESUME-PROFILE-001",
        raw_text="Python backend developer",
    )

    return create_screening_result(
        db,
        job_id=job.id,
        resume_id=resume.id,
        eligible=True,
        eligibility_details={
            "eligible": True,
        },
    )


def test_create_and_get_match_profile(db):
    screening = create_test_screening(db)

    profile = create_match_profile(
        db,
        screening_id=screening.id,
        gap_analysis={
            "missing_skills": ["Docker"],
            "experience_gap": {
                "has_gap": False,
            },
        },
        explanation={
            "decision": "review",
            "strengths": ["Python"],
            "gaps": ["Docker"],
        },
    )

    assert profile.id is not None
    assert profile.screening_id == screening.id

    fetched = get_match_profile(
        db,
        screening.id,
    )

    assert fetched is not None
    assert fetched.id == profile.id
    assert fetched.gap_analysis["missing_skills"] == ["Docker"]


def test_update_match_profile(db):
    screening = create_test_screening(db)

    profile = create_match_profile(
        db,
        screening_id=screening.id,
        gap_analysis={
            "missing_skills": ["Docker"],
        },
        explanation={
            "decision": "review",
        },
    )

    updated = update_match_profile(
        db,
        profile,
        gap_analysis={
            "missing_skills": [],
        },
        explanation={
            "decision": "shortlist",
            "strengths": ["Python", "FastAPI"],
        },
    )

    assert updated.gap_analysis["missing_skills"] == []
    assert updated.explanation["decision"] == "shortlist"


def test_update_only_gap_analysis(db):
    screening = create_test_screening(db)

    profile = create_match_profile(
        db,
        screening_id=screening.id,
        gap_analysis={
            "missing_skills": ["Docker"],
        },
        explanation={
            "decision": "review",
        },
    )

    updated = update_match_profile(
        db,
        profile,
        gap_analysis={
            "missing_skills": ["Docker", "Redis"],
        },
    )

    assert updated.gap_analysis["missing_skills"] == [
        "Docker",
        "Redis",
    ]

    assert updated.explanation["decision"] == "review"


def test_delete_match_profile(db):
    screening = create_test_screening(db)

    profile = create_match_profile(
        db,
        screening_id=screening.id,
        gap_analysis={},
        explanation={},
    )

    profile_id = profile.id

    delete_match_profile(
        db,
        profile,
    )

    assert get_match_profile(
        db,
        screening.id,
    ) is None

    assert profile_id is not None