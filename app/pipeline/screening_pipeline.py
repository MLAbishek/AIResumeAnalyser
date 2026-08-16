from typing import Any

from app.core.schemas import JobDescription, Resume
from app.services.screening_service import ScreeningService


class ScreeningPipeline:
    """
    End-to-end deterministic screening pipeline.

    Current flow:

        Job + Resumes
            ↓
        Canonicalization
            ↓
        Eligibility
            ↓
        Ranking
            ↓
        Threshold decision
            ↓
        Gap analysis
            ↓
        Explanation
            ↓
        Evidence
    """

    def __init__(
        self,
        screening_service: ScreeningService | None = None,
    ):
        self.screening_service = (
            screening_service or ScreeningService()
        )

    def run(
        self,
        job_description: JobDescription,
        resumes: list[Resume],
    ) -> dict[str, Any]:

        result = self.screening_service.screen(
            job_description=job_description,
            resumes=resumes,
        )

        return {
            **result,
            "status": "completed",
        }