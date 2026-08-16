from collections import deque

from app.infrastructure.queue.base import TaskQueue
from app.infrastructure.queue.models import QueueTask


class InMemoryTaskQueue(TaskQueue):
    """
    Simple FIFO in-memory queue.

    Intended as the initial implementation and test backend.
    A production broker can later implement TaskQueue without
    changing worker/task contracts.
    """

    def __init__(self):
        self._queue: deque[str] = deque()
        self._tasks: dict[str, QueueTask] = {}

    def enqueue(
        self,
        task: QueueTask,
    ) -> str:

        if task.task_id in self._tasks:
            raise ValueError(
                f"Task '{task.task_id}' already exists."
            )

        self._tasks[task.task_id] = task
        self._queue.append(task.task_id)

        return task.task_id

    def dequeue(self) -> QueueTask | None:

        if not self._queue:
            return None

        task_id = self._queue.popleft()

        return self._tasks[task_id]

    def get_task(
        self,
        task_id: str,
    ) -> QueueTask | None:

        return self._tasks.get(task_id)

    def size(self) -> int:
        return len(self._queue)