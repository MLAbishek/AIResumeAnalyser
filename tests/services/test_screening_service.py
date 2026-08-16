from app.core.schemas import (
    Education,
    Experience,
    JobDescription,
    Resume,
)
from app.services.screening_service import (
    ScreeningService,
)


def test_screening_service_shortlists_matching_candidate():
    job = JobDescription(
        job_id="JD-SERVICE-001",
        title="Python Developer",
        required_skills=[
            "Python",
        ],
        required_experience_years=2,
        raw_text=(
            "Python developer with 2 years experience."
        ),
    )

    resume = Resume(
        resume_id="RES-SERVICE-001",
        name="Candidate One",
        skills=[
            "Python",
        ],
        experience=[
            Experience(
                company="ABC",
                role="Python Developer",
                start_date="01/2022",
                end_date="01/2024",
            ),
        ],
        raw_text=(
            "Python developer with two years experience."
        ),
    )

    service = ScreeningService()

    result = service.screen(
        job_description=job,
        resumes=[resume],
    )

    assert result["job_id"] == "JD-SERVICE-001"
    assert result["total_candidates"] == 1
    assert result["eligible_candidates"] == 1

    candidate = result["results"][0]

    assert candidate["resume_id"] == "RES-SERVICE-001"
    assert candidate["eligible"] is True
    assert candidate["ranking_score"] is not None
    assert candidate["decision"] in {
        "shortlist",
        "review",
        "reject",
    }


def test_screening_service_rejects_missing_required_skill():
    job = JobDescription(
        job_id="JD-SERVICE-002",
        title="Python Developer",
        required_skills=[
            "Python",
            "Docker",
        ],
        raw_text="Python and Docker developer.",
    )

    resume = Resume(
        resume_id="RES-SERVICE-002",
        skills=[
            "Python",
        ],
        raw_text="Python developer.",
    )

    service = ScreeningService()

    result = service.screen(
        job_description=job,
        resumes=[resume],
    )

    candidate = result["results"][0]

    assert candidate["eligible"] is False
    assert candidate["ranking_score"] is None
    assert candidate["decision"] == "reject"


def test_screening_service_handles_multiple_candidates():
    job = JobDescription(
        job_id="JD-SERVICE-003",
        title="Developer",
        required_skills=["Python"],
        raw_text="Python developer.",
    )

    resumes = [
        Resume(
            resume_id="RES-SERVICE-003-B",
            skills=["Python"],
            raw_text="Python developer.",
        ),
        Resume(
            resume_id="RES-SERVICE-003-A",
            skills=["Python"],
            raw_text="Python developer.",
        ),
    ]

    service = ScreeningService()

    result = service.screen(
        job_description=job,
        resumes=resumes,
    )

    assert result["total_candidates"] == 2
    assert result["eligible_candidates"] == 2
    assert len(result["results"]) == 2

    assert {
        candidate["resume_id"]
        for candidate in result["results"]
    } == {
        "RES-SERVICE-003-A",
        "RES-SERVICE-003-B",
    }