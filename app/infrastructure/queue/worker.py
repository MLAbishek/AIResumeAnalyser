from app.infrastructure.queue.base import TaskQueue
from app.infrastructure.queue.models import (
    QueueTask,
    QueueTaskStatus,
)


class TaskWorker:
    """
    Executes tasks obtained from a TaskQueue.

    The worker is deliberately unaware of application-specific
    operations such as parsing, screening, ranking, embeddings,
    or LLM calls.
    """

    def __init__(
        self,
        queue: TaskQueue,
    ):
        self.queue = queue

    def process_next(self) -> QueueTask | None:
        """
        Process one queued task.

        Returns:
            The processed task, or None when the queue is empty.
        """

        task = self.queue.dequeue()

        if task is None:
            return None

        self._execute(task)

        return task

    def process_all(self) -> list[QueueTask]:
        """
        Process all currently queued tasks.
        """

        processed: list[QueueTask] = []

        while True:
            task = self.process_next()

            if task is None:
                break

            processed.append(task)

        return processed

    def _execute(
        self,
        task: QueueTask,
    ) -> None:

        max_attempts = task.max_retries + 1

        for attempt in range(
            1,
            max_attempts + 1,
        ):
            task.attempts = attempt
            task.status = QueueTaskStatus.RUNNING
            task.error = None

            try:
                task.result = task.handler(
                    dict(task.payload)
                )

                task.status = (
                    QueueTaskStatus.COMPLETED
                )

                return

            except Exception as exc:
                task.error = str(exc)

                if attempt < max_attempts:
                    task.status = (
                        QueueTaskStatus.RETRYING
                    )
                else:
                    task.status = (
                        QueueTaskStatus.FAILED
                    )