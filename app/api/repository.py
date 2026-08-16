from app.core.schemas import CanonicalJob, CanonicalResume


class InMemoryRepository:
    """
    Simple repository used by the API layer.

    This is intentionally in-memory for now.
    A database-backed repository can replace it later
    without changing the API service contracts.
    """

    def __init__(self):
        self._jobs: dict[str, CanonicalJob] = {}
        self._resumes: dict[str, CanonicalResume] = {}

    def add_job(self, job: CanonicalJob) -> None:
        self._jobs[job.job_id] = job

    def add_resume(self, resume: CanonicalResume) -> None:
        self._resumes[resume.resume_id] = resume

    def get_job(self, job_id: str) -> CanonicalJob:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise KeyError(
                f"Job not found: {job_id}"
            ) from exc

    def get_resume(self, resume_id: str) -> CanonicalResume:
        try:
            return self._resumes[resume_id]
        except KeyError as exc:
            raise KeyError(
                f"Candidate not found: {resume_id}"
            ) from exc

    def get_resumes(
        self,
        resume_ids: list[str],
    ) -> list[CanonicalResume]:
        return [
            self.get_resume(resume_id)
            for resume_id in resume_ids
        ]