import pytest

from app.infrastructure.queue import (
    InMemoryTaskQueue,
    QueueTask,
    QueueTaskStatus,
)


def test_enqueue_returns_task_id():

    queue = InMemoryTaskQueue()

    task = QueueTask(
        handler=lambda context: "result"
    )

    task_id = queue.enqueue(task)

    assert task_id == task.task_id
    assert queue.size() == 1
    assert queue.get_task(task_id) is task


def test_dequeue_returns_fifo_order():

    queue = InMemoryTaskQueue()

    first = QueueTask(
        handler=lambda context: "first"
    )

    second = QueueTask(
        handler=lambda context: "second"
    )

    queue.enqueue(first)
    queue.enqueue(second)

    assert queue.dequeue() is first
    assert queue.dequeue() is second
    assert queue.dequeue() is None


def test_new_task_is_queued():

    task = QueueTask(
        handler=lambda context: None
    )

    assert task.status == QueueTaskStatus.QUEUED


def test_queue_size_changes_after_dequeue():

    queue = InMemoryTaskQueue()

    queue.enqueue(
        QueueTask(
            handler=lambda context: None
        )
    )

    queue.enqueue(
        QueueTask(
            handler=lambda context: None
        )
    )

    assert queue.size() == 2

    queue.dequeue()

    assert queue.size() == 1


def test_duplicate_task_id_is_rejected():

    queue = InMemoryTaskQueue()

    task = QueueTask(
        handler=lambda context: None,
        task_id="TASK-001",
    )

    queue.enqueue(task)

    duplicate = QueueTask(
        handler=lambda context: None,
        task_id="TASK-001",
    )

    with pytest.raises(ValueError):
        queue.enqueue(duplicate)