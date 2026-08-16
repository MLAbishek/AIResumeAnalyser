from app.core.schemas import (
    JobDescription,
    Resume,
)
from app.infrastructure.orchestrator import (
    PipelineOrchestrator,
    PipelineStatus,
    TaskDefinition,
)
from app.infrastructure.queue import (
    InMemoryTaskQueue,
    QueueTask,
    QueueTaskStatus,
    TaskWorker,
)
from app.services.bulk_screening_service import (
    BulkScreeningService,
)


def test_queue_worker_executes_bulk_screening():

    job = JobDescription(
        job_id="JD-QUEUE-001",
        title="Python Developer",
        required_skills=["Python"],
        raw_text="Python developer.",
    )

    resumes = [
        Resume(
            resume_id="RES-QUEUE-001",
            name="Candidate One",
            skills=["Python"],
            raw_text="Python developer.",
        ),
        Resume(
            resume_id="RES-QUEUE-002",
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

    queue = InMemoryTaskQueue()

    task = QueueTask(
        handler=screening_task,
        payload={
            "job_description": job,
            "resumes": resumes,
        },
    )

    task_id = queue.enqueue(task)

    worker = TaskWorker(queue)

    processed = worker.process_next()

    assert processed is task
    assert processed.task_id == task_id

    assert processed.status == (
        QueueTaskStatus.COMPLETED
    )

    result = processed.result

    assert result["job_id"] == "JD-QUEUE-001"
    assert result["total_candidates"] == 2
    assert result["eligible_candidates"] == 2

    assert {
        candidate["resume_id"]
        for candidate in result["results"]
    } == {
        "RES-QUEUE-001",
        "RES-QUEUE-002",
    }


def test_orchestrator_result_can_be_queued():

    job = JobDescription(
        job_id="JD-QUEUE-002",
        title="Python Developer",
        required_skills=["Python"],
        raw_text="Python developer.",
    )

    resumes = [
        Resume(
            resume_id="RES-QUEUE-003",
            skills=["Python"],
            raw_text="Python developer.",
        )
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
        pipeline_id="PIPE-QUEUE-001",
        context={
            "job_description": job,
            "resumes": resumes,
        },
    )

    assert state.status == PipelineStatus.COMPLETED

    screening_result = state.results[
        "bulk_screening"
    ]

    queue = InMemoryTaskQueue()

    task = QueueTask(
        handler=lambda context: context["result"],
        payload={
            "result": screening_result,
        },
    )

    queue.enqueue(task)

    worker = TaskWorker(queue)

    processed = worker.process_next()

    assert processed.status == (
        QueueTaskStatus.COMPLETED
    )

    assert processed.result["job_id"] == (
        "JD-QUEUE-002"
    )