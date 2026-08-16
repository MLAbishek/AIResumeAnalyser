from app.infrastructure.queue import (
    InMemoryTaskQueue,
    QueueTask,
    QueueTaskStatus,
    TaskWorker,
)


def test_worker_executes_task():

    queue = InMemoryTaskQueue()

    task = QueueTask(
        handler=lambda context: "completed"
    )

    task_id = queue.enqueue(task)

    worker = TaskWorker(queue)

    processed = worker.process_next()

    assert processed is task
    assert processed.task_id == task_id
    assert processed.status == (
        QueueTaskStatus.COMPLETED
    )
    assert processed.result == "completed"
    assert processed.attempts == 1


def test_worker_passes_payload_to_handler():

    queue = InMemoryTaskQueue()

    task = QueueTask(
        handler=lambda context: (
            context["value"] * 2
        ),
        payload={
            "value": 21
        },
    )

    queue.enqueue(task)

    worker = TaskWorker(queue)

    worker.process_next()

    assert task.result == 42


def test_worker_returns_none_when_queue_empty():

    queue = InMemoryTaskQueue()

    worker = TaskWorker(queue)

    assert worker.process_next() is None


def test_worker_processes_all_tasks():

    queue = InMemoryTaskQueue()

    for value in range(3):
        queue.enqueue(
            QueueTask(
                handler=lambda context: context["value"],
                payload={"value": value},
            )
        )

    worker = TaskWorker(queue)

    processed = worker.process_all()

    assert len(processed) == 3

    assert [
        task.result
        for task in processed
    ] == [0, 1, 2]

    assert queue.size() == 0


def test_worker_marks_failed_task():

    def failing(context):
        raise RuntimeError("worker failure")

    queue = InMemoryTaskQueue()

    task = QueueTask(
        handler=failing
    )

    queue.enqueue(task)

    worker = TaskWorker(queue)

    processed = worker.process_next()

    assert processed is task
    assert processed.status == (
        QueueTaskStatus.FAILED
    )
    assert processed.attempts == 1
    assert processed.error == "worker failure"


def test_worker_retries_failed_task():

    attempts = []

    def flaky(context):
        attempts.append(1)

        if len(attempts) < 3:
            raise RuntimeError("temporary failure")

        return "success"

    queue = InMemoryTaskQueue()

    task = QueueTask(
        handler=flaky,
        max_retries=2,
    )

    queue.enqueue(task)

    worker = TaskWorker(queue)

    processed = worker.process_next()

    assert processed.status == (
        QueueTaskStatus.COMPLETED
    )
    assert processed.attempts == 3
    assert processed.result == "success"


def test_worker_respects_retry_limit():

    attempts = []

    def always_fails(context):
        attempts.append(1)
        raise RuntimeError("permanent failure")

    queue = InMemoryTaskQueue()

    task = QueueTask(
        handler=always_fails,
        max_retries=2,
    )

    queue.enqueue(task)

    worker = TaskWorker(queue)

    processed = worker.process_next()

    assert processed.status == (
        QueueTaskStatus.FAILED
    )
    assert processed.attempts == 3
    assert len(attempts) == 3