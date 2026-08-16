from app.core.schemas import (
    JobDescription,
    Resume,
)
from app.infrastructure.orchestrator import (
    PipelineOrchestrator,
    PipelineStatus,
    TaskDefinition,
    TaskStatus,
)
from app.services.bulk_screening_service import (
    BulkScreeningService,
)


def test_orchestrator_executes_real_bulk_screening():

    job = JobDescription(
        job_id="JD-ORCH-001",
        title="Python Developer",
        required_skills=["Python"],
        raw_text="Python developer.",
    )

    resumes = [
        Resume(
            resume_id="RES-ORCH-001",
            name="Candidate One",
            skills=["Python"],
            raw_text="Python developer.",
        ),
        Resume(
            resume_id="RES-ORCH-002",
            name="Candidate Two",
            skills=["Python"],
            raw_text="Python developer.",
        ),
    ]

    bulk_service = BulkScreeningService()

    def screening_task(context):
        return bulk_service.screen(
            job_description=context["job_description"],
            resumes=context["resumes"],
        )

    orchestrator = PipelineOrchestrator(
        tasks=[
            TaskDefinition(
                name="bulk_screening",
                handler=screening_task,
            )
        ]
    )

    state = orchestrator.run(
        pipeline_id="SCREENING-001",
        context={
            "job_description": job,
            "resumes": resumes,
        },
    )

    assert state.status == PipelineStatus.COMPLETED

    task = state.task("bulk_screening")

    assert task.status == TaskStatus.COMPLETED

    result = state.results["bulk_screening"]

    assert result["job_id"] == "JD-ORCH-001"
    assert result["total_candidates"] == 2
    assert len(result["results"]) == 2

    assert {
        candidate["resume_id"]
        for candidate in result["results"]
    } == {
        "RES-ORCH-001",
        "RES-ORCH-002",
    }