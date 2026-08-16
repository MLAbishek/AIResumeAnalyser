from typing import Any

from app.core.schemas import JobDescription, Resume
from app.services.screening_service import ScreeningService


class BulkScreeningService:
    """
    Application service for screening a collection of
    resumes against one job description.

    The complete candidate collection is passed to the
    underlying ScreeningService in one operation so that
    eligibility filtering and candidate ranking remain
    globally consistent.

    This service does not persist results and does not
    perform asynchronous execution. Those responsibilities
    belong to other infrastructure modules.
    """

    def __init__(
        self,
        screening_service: ScreeningService | None = None,
    ):
        self.screening_service = (
            screening_service or ScreeningService()
        )

    def screen(
        self,
        *,
        job_description: JobDescription,
        resumes: list[Resume],
    ) -> dict[str, Any]:
        """
        Screen an entire candidate collection against one JD.

        The complete collection is deliberately passed to
        ScreeningService so ranking is performed globally
        rather than independently per batch.
        """

        self._validate_inputs(
            job_description=job_description,
            resumes=resumes,
        )

        result = self.screening_service.screen(
            job_description=job_description,
            resumes=resumes,
        )

        return self._build_bulk_result(
            result=result,
            submitted_count=len(resumes),
        )

    @staticmethod
    def _validate_inputs(
        *,
        job_description: JobDescription,
        resumes: list[Resume],
    ) -> None:
        if not isinstance(
            job_description,
            JobDescription,
        ):
            raise TypeError(
                "job_description must be a JobDescription"
            )

        if not isinstance(resumes, list):
            raise TypeError(
                "resumes must be a list"
            )

        if any(
            not isinstance(resume, Resume)
            for resume in resumes
        ):
            raise TypeError(
                "Every resume must be a Resume instance"
            )

        resume_ids = [
            resume.resume_id
            for resume in resumes
        ]

        if len(resume_ids) != len(set(resume_ids)):
            duplicates = sorted(
                {
                    resume_id
                    for resume_id in resume_ids
                    if resume_ids.count(resume_id) > 1
                }
            )

            raise ValueError(
                "Duplicate resume IDs are not allowed: "
                + ", ".join(duplicates)
            )

    @staticmethod
    def _build_bulk_result(
        *,
        result: dict[str, Any],
        submitted_count: int,
    ) -> dict[str, Any]:
        """
        Normalize the result returned by ScreeningService
        into the explicit bulk-screening contract.
        """

        results = result.get(
            "results",
            [],
        )

        return {
            "job_id": result["job_id"],
            "total_candidates": submitted_count,
            "eligible_candidates": result.get(
                "eligible_candidates",
                0,
            ),
            "results": results,
        }