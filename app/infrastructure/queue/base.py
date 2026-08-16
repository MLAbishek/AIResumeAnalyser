from abc import ABC, abstractmethod

from app.infrastructure.queue.models import QueueTask


class TaskQueue(ABC):
    """
    Backend-independent task queue contract.
    """

    @abstractmethod
    def enqueue(
        self,
        task: QueueTask,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def dequeue(self) -> QueueTask | None:
        raise NotImplementedError

    @abstractmethod
    def get_task(
        self,
        task_id: str,
    ) -> QueueTask | None:
        raise NotImplementedError

    @abstractmethod
    def size(self) -> int:
        raise NotImplementedError