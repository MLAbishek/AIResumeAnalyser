from app.pipeline.screening_pipeline import ScreeningPipeline
from app.core.schemas import JobDescription, Resume


def test_pipeline_initialization():

    jd = JobDescription(
        job_id="JD_001",
        title="Machine Learning Engineer",
        raw_text="Machine Learning Engineer with Python experience."
    )

    resume = Resume(
        resume_id="RES_001",
        name="Test Candidate",
        raw_text="Python developer with machine learning experience."
    )

    pipeline = ScreeningPipeline()

    result = pipeline.run(
        job_description=jd,
        resumes=[resume]
    )

    assert result["job_id"] == "JD_001"
    assert result["total_candidates"] == 1
    assert result["status"] == "pipeline_initialized"