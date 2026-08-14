from app.core.schemas import JobDescription, Resume


class ScreeningPipeline:

    def run(
        self,
        job_description: JobDescription,
        resumes: list[Resume]
    ):
        return {
            "job_id": job_description.job_id,
            "total_candidates": len(resumes),
            "status": "pipeline_initialized"
        }