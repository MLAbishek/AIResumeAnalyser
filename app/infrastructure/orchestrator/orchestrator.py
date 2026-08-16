from typing import Any

from app.infrastructure.orchestrator.exceptions import (
    PipelineConfigurationError,
)
from app.infrastructure.orchestrator.models import (
    PipelineExecutionState,
    PipelineStatus,
    TaskDefinition,
    TaskExecutionState,
    TaskStatus,
)


class PipelineOrchestrator:
    """
    Dependency-aware execution controller.

    Responsibilities:
    - validate pipeline configuration
    - resolve task dependencies
    - execute tasks in dependency order
    - maintain execution state
    - retry failed tasks
    - block downstream tasks after dependency failure
    """

    def __init__(
        self,
        tasks: list[TaskDefinition],
    ):
        self.tasks = self._validate_tasks(tasks)
        self._task_map = {
            task.name: task
            for task in self.tasks
        }

    def create_state(
        self,
        pipeline_id: str,
    ) -> PipelineExecutionState:
        return PipelineExecutionState(
            pipeline_id=pipeline_id,
            tasks={
                task.name: TaskExecutionState(
                    name=task.name
                )
                for task in self.tasks
            },
        )

    def run(
        self,
        *,
        pipeline_id: str,
        context: dict[str, Any] | None = None,
    ) -> PipelineExecutionState:

        state = self.create_state(pipeline_id)

        execution_context = dict(context or {})

        state.status = PipelineStatus.RUNNING

        execution_order = self._resolve_execution_order()

        for task_name in execution_order:
            task = self._task_map[task_name]
            task_state = state.tasks[task_name]

            if self._has_failed_dependency(
                task,
                state,
            ):
                task_state.status = TaskStatus.BLOCKED
                task_state.error = (
                    "A dependency failed or was blocked."
                )
                continue

            self._execute_task(
                task=task,
                task_state=task_state,
                context=execution_context,
            )

            if task_state.status == TaskStatus.FAILED:
                continue

            execution_context[task.name] = task_state.result
            state.results[task.name] = task_state.result

        failed = any(
            task.status == TaskStatus.FAILED
            for task in state.tasks.values()
        )

        blocked = any(
            task.status == TaskStatus.BLOCKED
            for task in state.tasks.values()
        )

        if failed or blocked:
            state.status = PipelineStatus.FAILED
            state.error = (
                "One or more pipeline tasks failed."
                if failed
                else "One or more pipeline tasks were blocked."
            )
        else:
            state.status = PipelineStatus.COMPLETED

        return state

    def _execute_task(
        self,
        *,
        task: TaskDefinition,
        task_state: TaskExecutionState,
        context: dict[str, Any],
    ) -> None:

        max_attempts = task.max_retries + 1

        for attempt in range(1, max_attempts + 1):
            task_state.attempts = attempt
            task_state.status = TaskStatus.RUNNING
            task_state.error = None

            try:
                task_state.result = task.handler(
                    dict(context)
                )
                task_state.status = TaskStatus.COMPLETED
                return

            except Exception as exc:
                task_state.error = str(exc)

                if attempt < max_attempts:
                    task_state.status = TaskStatus.RETRYING
                else:
                    task_state.status = TaskStatus.FAILED

    def _has_failed_dependency(
        self,
        task: TaskDefinition,
        state: PipelineExecutionState,
    ) -> bool:

        return any(
            state.tasks[dependency].status
            in {
                TaskStatus.FAILED,
                TaskStatus.BLOCKED,
                TaskStatus.CANCELLED,
            }
            for dependency in task.dependencies
        )

    def _resolve_execution_order(self) -> list[str]:

        visited: set[str] = set()
        visiting: set[str] = set()
        order: list[str] = []

        def visit(task_name: str) -> None:
            if task_name in visited:
                return

            if task_name in visiting:
                raise PipelineConfigurationError(
                    "Circular task dependency detected."
                )

            visiting.add(task_name)

            task = self._task_map[task_name]

            for dependency in task.dependencies:
                visit(dependency)

            visiting.remove(task_name)
            visited.add(task_name)
            order.append(task_name)

        for task in self.tasks:
            visit(task.name)

        return order

    @staticmethod
    def _validate_tasks(
        tasks: list[TaskDefinition],
    ) -> list[TaskDefinition]:

        if not tasks:
            raise PipelineConfigurationError(
                "Pipeline must contain at least one task."
            )

        names = [task.name for task in tasks]

        if len(names) != len(set(names)):
            raise PipelineConfigurationError(
                "Task names must be unique."
            )

        task_names = set(names)

        for task in tasks:
            if not task.name.strip():
                raise PipelineConfigurationError(
                    "Task names cannot be empty."
                )

            if task.max_retries < 0:
                raise PipelineConfigurationError(
                    f"Task '{task.name}' has a negative retry count."
                )

            missing = (
                set(task.dependencies) - task_names
            )

            if missing:
                raise PipelineConfigurationError(
                    f"Task '{task.name}' has unknown "
                    f"dependencies: {sorted(missing)}"
                )

            if task.name in task.dependencies:
                raise PipelineConfigurationError(
                    f"Task '{task.name}' cannot depend on itself."
                )

        return list(tasks)