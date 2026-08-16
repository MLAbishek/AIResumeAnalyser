from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    RETRYING = "retrying"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


TaskHandler = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class TaskDefinition:
    name: str
    handler: TaskHandler
    dependencies: tuple[str, ...] = ()
    max_retries: int = 0


@dataclass
class TaskExecutionState:
    name: str
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    result: Any = None
    error: str | None = None


@dataclass
class PipelineExecutionState:
    pipeline_id: str
    status: PipelineStatus = PipelineStatus.PENDING
    tasks: dict[str, TaskExecutionState] = field(
        default_factory=dict
    )
    results: dict[str, Any] = field(
        default_factory=dict
    )
    error: str | None = None

    def task(self, name: str) -> TaskExecutionState:
        return self.tasks[name]