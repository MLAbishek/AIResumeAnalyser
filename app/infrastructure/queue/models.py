from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
from uuid import uuid4


class QueueTaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    RETRYING = "retrying"
    FAILED = "failed"


TaskHandler = Callable[[dict[str, Any]], Any]


@dataclass
class QueueTask:
    handler: TaskHandler
    payload: dict[str, Any] = field(default_factory=dict)
    max_retries: int = 0
    task_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    status: QueueTaskStatus = QueueTaskStatus.QUEUED
    attempts: int = 0
    result: Any = None
    error: str | None = None