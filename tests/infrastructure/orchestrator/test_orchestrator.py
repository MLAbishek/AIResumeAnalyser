import pytest

from app.infrastructure.orchestrator import (
    PipelineOrchestrator,
    PipelineStatus,
    TaskDefinition,
    TaskStatus,
)
from app.infrastructure.orchestrator.exceptions import (
    PipelineConfigurationError,
)


def test_dependency_order():

    executed = []

    def first(context):
        executed.append("first")
        return "A"

    def second(context):
        executed.append("second")
        assert context["first"] == "A"
        return "B"

    def third(context):
        executed.append("third")
        assert context["second"] == "B"
        return "C"

    orchestrator = PipelineOrchestrator(
        [
            TaskDefinition(
                name="third",
                handler=third,
                dependencies=("second",),
            ),
            TaskDefinition(
                name="first",
                handler=first,
            ),
            TaskDefinition(
                name="second",
                handler=second,
                dependencies=("first",),
            ),
        ]
    )

    state = orchestrator.run(
        pipeline_id="PIPE-001"
    )

    assert state.status == PipelineStatus.COMPLETED
    assert executed == [
        "first",
        "second",
        "third",
    ]


def test_task_result_is_stored():

    orchestrator = PipelineOrchestrator(
        [
            TaskDefinition(
                name="task",
                handler=lambda context: 42,
            )
        ]
    )

    state = orchestrator.run(
        pipeline_id="PIPE-002"
    )

    assert state.results["task"] == 42
    assert state.task("task").result == 42
    assert (
        state.task("task").status
        == TaskStatus.COMPLETED
    )


def test_failure_is_recorded():

    def failing(context):
        raise RuntimeError("boom")

    orchestrator = PipelineOrchestrator(
        [
            TaskDefinition(
                name="failing",
                handler=failing,
            )
        ]
    )

    state = orchestrator.run(
        pipeline_id="PIPE-003"
    )

    assert state.status == PipelineStatus.FAILED
    assert (
        state.task("failing").status
        == TaskStatus.FAILED
    )
    assert state.task("failing").attempts == 1
    assert state.task("failing").error == "boom"


def test_downstream_task_is_blocked():

    executed = []

    def failing(context):
        raise RuntimeError("failure")

    def downstream(context):
        executed.append("downstream")

    orchestrator = PipelineOrchestrator(
        [
            TaskDefinition(
                name="first",
                handler=failing,
            ),
            TaskDefinition(
                name="second",
                handler=downstream,
                dependencies=("first",),
            ),
        ]
    )

    state = orchestrator.run(
        pipeline_id="PIPE-004"
    )

    assert state.status == PipelineStatus.FAILED
    assert (
        state.task("second").status
        == TaskStatus.BLOCKED
    )
    assert executed == []


def test_retry_succeeds():

    attempts = []

    def flaky(context):
        attempts.append(1)

        if len(attempts) < 3:
            raise RuntimeError("temporary")

        return "success"

    orchestrator = PipelineOrchestrator(
        [
            TaskDefinition(
                name="flaky",
                handler=flaky,
                max_retries=2,
            )
        ]
    )

    state = orchestrator.run(
        pipeline_id="PIPE-005"
    )

    assert state.status == PipelineStatus.COMPLETED
    assert state.task("flaky").attempts == 3
    assert state.task("flaky").result == "success"


def test_retry_limit_is_respected():

    attempts = []

    def always_fails(context):
        attempts.append(1)
        raise RuntimeError("permanent")

    orchestrator = PipelineOrchestrator(
        [
            TaskDefinition(
                name="failing",
                handler=always_fails,
                max_retries=2,
            )
        ]
    )

    state = orchestrator.run(
        pipeline_id="PIPE-006"
    )

    assert state.status == PipelineStatus.FAILED
    assert state.task("failing").attempts == 3
    assert len(attempts) == 3


def test_duplicate_task_names_are_rejected():

    with pytest.raises(PipelineConfigurationError):

        PipelineOrchestrator(
            [
                TaskDefinition(
                    name="same",
                    handler=lambda context: None,
                ),
                TaskDefinition(
                    name="same",
                    handler=lambda context: None,
                ),
            ]
        )


def test_unknown_dependency_is_rejected():

    with pytest.raises(PipelineConfigurationError):

        PipelineOrchestrator(
            [
                TaskDefinition(
                    name="task",
                    handler=lambda context: None,
                    dependencies=("missing",),
                )
            ]
        )


def test_circular_dependency_is_rejected():

    orchestrator = PipelineOrchestrator(
        [
            TaskDefinition(
                name="a",
                handler=lambda context: None,
                dependencies=("b",),
            ),
            TaskDefinition(
                name="b",
                handler=lambda context: None,
                dependencies=("a",),
            ),
        ]
    )

    with pytest.raises(PipelineConfigurationError):
        orchestrator.run(
            pipeline_id="PIPE-007"
        )


def test_initial_context_is_available():

    def task(context):
        return context["job_id"]

    orchestrator = PipelineOrchestrator(
        [
            TaskDefinition(
                name="task",
                handler=task,
            )
        ]
    )

    state = orchestrator.run(
        pipeline_id="PIPE-008",
        context={
            "job_id": "JD-001"
        },
    )

    assert state.results["task"] == "JD-001"


def test_empty_pipeline_is_rejected():

    with pytest.raises(PipelineConfigurationError):
        PipelineOrchestrator([])