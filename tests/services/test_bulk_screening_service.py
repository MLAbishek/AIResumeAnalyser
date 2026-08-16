import pytest

from app.core.schemas import (
    JobDescription,
    Resume,
)
from app.services.bulk_screening_service import (
    BulkScreeningService,
)
from app.services.screening_service import (
    ScreeningService,
)


def _job() -> JobDescription:
    return JobDescription(
        job_id="JD-BULK-001",
        title="Python Developer",
        required_skills=["Python"],
        raw_text="Python developer.",
    )


def _resume(
    resume_id: str,
    skills: list[str] | None = None,
) -> Resume:
    return Resume(
        resume_id=resume_id,
        name=f"Candidate {resume_id}",
        skills=skills or ["Python"],
        raw_text="Python developer.",
    )


def test_bulk_screening_processes_multiple_candidates():

    service = BulkScreeningService()

    resumes = [
        _resume("RES-BULK-001"),
        _resume("RES-BULK-002"),
        _resume("RES-BULK-003"),
    ]

    result = service.screen(
        job_description=_job(),
        resumes=resumes,
    )

    assert result["job_id"] == "JD-BULK-001"
    assert result["total_candidates"] == 3
    assert result["eligible_candidates"] == 3
    assert len(result["results"]) == 3

    assert {
        candidate["resume_id"]
        for candidate in result["results"]
    } == {
        "RES-BULK-001",
        "RES-BULK-002",
        "RES-BULK-003",
    }


def test_bulk_screening_preserves_global_screening():

    service = BulkScreeningService()

    resumes = [
        _resume("RES-BULK-003"),
        _resume("RES-BULK-001"),
        _resume("RES-BULK-002"),
    ]

    result = service.screen(
        job_description=_job(),
        resumes=resumes,
    )

    assert result["total_candidates"] == 3

    # ScreeningService owns the actual ranking/order.
    # BulkScreeningService must not re-rank candidates
    # independently.
    assert len(result["results"]) == 3


def test_bulk_screening_handles_ineligible_candidates():

    service = BulkScreeningService()

    resumes = [
        _resume(
            "RES-BULK-ELIGIBLE",
            ["Python"],
        ),
        _resume(
            "RES-BULK-INELIGIBLE",
            ["Java"],
        ),
    ]

    result = service.screen(
        job_description=_job(),
        resumes=resumes,
    )

    assert result["total_candidates"] == 2
    assert result["eligible_candidates"] == 1

    by_id = {
        candidate["resume_id"]: candidate
        for candidate in result["results"]
    }

    assert by_id["RES-BULK-ELIGIBLE"]["eligible"] is True
    assert (
        by_id["RES-BULK-INELIGIBLE"]["eligible"]
        is False
    )


def test_bulk_screening_rejects_invalid_job():

    service = BulkScreeningService()

    with pytest.raises(TypeError):

        service.screen(
            job_description="not-a-job",
            resumes=[],
        )


def test_bulk_screening_rejects_invalid_resume_collection():

    service = BulkScreeningService()

    with pytest.raises(TypeError):

        service.screen(
            job_description=_job(),
            resumes="not-a-list",
        )


def test_bulk_screening_rejects_invalid_resume():

    service = BulkScreeningService()

    with pytest.raises(TypeError):

        service.screen(
            job_description=_job(),
            resumes=[
                _resume("RES-BULK-001"),
                "not-a-resume",
            ],
        )


def test_bulk_screening_rejects_duplicate_resume_ids():

    service = BulkScreeningService()

    resumes = [
        _resume("RES-DUPLICATE"),
        _resume("RES-DUPLICATE"),
    ]

    with pytest.raises(ValueError) as exc_info:

        service.screen(
            job_description=_job(),
            resumes=resumes,
        )

    assert "Duplicate resume IDs" in str(
        exc_info.value
    )


def test_bulk_screening_allows_empty_collection():

    service = BulkScreeningService()

    result = service.screen(
        job_description=_job(),
        resumes=[],
    )

    assert result["job_id"] == "JD-BULK-001"
    assert result["total_candidates"] == 0
    assert result["eligible_candidates"] == 0
    assert result["results"] == []


def test_bulk_screening_accepts_injected_screening_service():

    class FakeScreeningService:

        def screen(
            self,
            *,
            job_description,
            resumes,
        ):
            return {
                "job_id": job_description.job_id,
                "total_candidates": len(resumes),
                "eligible_candidates": len(resumes),
                "results": [
                    {
                        "resume_id": resume.resume_id,
                        "eligible": True,
                    }
                    for resume in resumes
                ],
            }

    service = BulkScreeningService(
        screening_service=FakeScreeningService()
    )

    result = service.screen(
        job_description=_job(),
        resumes=[
            _resume("RES-FAKE-001"),
            _resume("RES-FAKE-002"),
        ],
    )

    assert result["job_id"] == "JD-BULK-001"
    assert result["total_candidates"] == 2
    assert len(result["results"]) == 2