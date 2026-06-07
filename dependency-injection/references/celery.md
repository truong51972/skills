# Celery Integration

Use this reference for Celery worker processes, task entry points, worker signals,
and fork-safe container lifecycle.

## Runtime Model

For Celery prefork workers, create external resources in the child process. Do not
create fork-unsafe clients, sockets, database pools, or async event-loop resources in
the parent process before workers fork.

Signal handlers should accept `**kwargs` so newer Celery versions can add arguments
without breaking the handler.

## Worker Bootstrap

```python
import logging
import threading

from celery.signals import (
    worker_before_create_process,
    worker_process_init,
    worker_process_shutdown,
)

from containers import Container, build_container

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_container: Container | None = None


def init_container() -> Container:
    global _container

    if _container is not None:
        return _container

    with _lock:
        if _container is None:
            container = build_container()
            container.init_resources()
            _container = container
            logger.info("Initialized DI container for Celery worker process.")

    return _container


def get_container() -> Container:
    return _container if _container is not None else init_container()


def shutdown_container() -> None:
    global _container

    if _container is None:
        return

    with _lock:
        container = _container
        _container = None

    try:
        container.shutdown_resources()
        logger.info("Released DI resources for Celery worker process.")
    except Exception:
        logger.exception("Error while releasing DI resources.")


@worker_before_create_process.connect
def _before_child_process(**kwargs: object) -> None:
    # Close or reset any accidental parent-process global clients here.
    # Prefer avoiding parent-process resource creation entirely.
    pass


@worker_process_init.connect
def _on_worker_process_init(**kwargs: object) -> None:
    init_container()


@worker_process_shutdown.connect
def _on_worker_process_shutdown(**kwargs: object) -> None:
    shutdown_container()
```

Keep `worker_process_init` fast. Celery may kill a child process if this signal
handler blocks too long during startup. If a dependency is slow to warm up, consider
lazy initialization behind a provider or an explicit warmup task.

`worker_process_shutdown` is best-effort. Cleanup that must always happen for a task
belongs inside the task/service logic, not only in the shutdown signal.

Ensure the bootstrap module is imported by the worker at startup, for example through
Celery `imports` / `include` settings or a side-effect import from the Celery app
module.

## Thin Task Entry Point

Tasks should deserialize payloads, resolve the service at the task edge, call business
logic, and return serializable results.

```python
from celery import shared_task

from bootstrap.celery_container import get_container


@shared_task(name="domain.process_record")
def process_record_task(record_id: int) -> dict[str, object]:
    processor = get_container().data_processor()
    result = processor.execute(record_id)
    return {"status": "success", "data": result}
```

Do not instantiate infrastructure or services directly in task modules. Keep retry,
idempotency, and transactional cleanup in the service/task logic where Celery can
observe failures correctly.

## Validation Checklist

1. Worker resources are initialized in child processes.
2. Signal handlers accept `**kwargs`.
3. Bootstrap import is guaranteed by worker startup configuration.
4. Task modules stay thin and resolve providers only at the task boundary.
5. Hard-shutdown data safety does not rely solely on shutdown signals.
6. Async resources are avoided in sync Celery tasks unless the project has an explicit event-loop strategy.
