# Celery Sub-skill

Use this sub-skill when runtime is Celery worker processes.

## Procedure

1. Build sync container bootstrap for worker process lifecycle.
2. Initialize resources on `worker_process_init`.
3. Shutdown resources on `worker_process_shutdown`.
4. Keep tasks thin and resolve providers at task edge.

## Worker Bootstrap

```python
import logging
import threading

from celery.signals import worker_process_init, worker_process_shutdown

from containers.container import Container

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_container: Container | None = None


def init_container() -> Container:
    global _container
    if _container is not None:
        return _container
    with _lock:
        if _container is None:
            _container = Container()
            _container.init_resources()
            logger.info("DI container initialised and resources acquired.")
    return _container


def get_container() -> Container:
    return _container if _container is not None else init_container()


def shutdown_container() -> None:
    global _container
    if _container is None:
        return
    with _lock:
        try:
            if _container is not None:
                _container.shutdown_resources()
                logger.info("DI container resources safely released.")
        except Exception:
            logger.exception("Error releasing DI container resources.")
        finally:
            _container = None


@worker_process_init.connect
def _on_worker_process_init(**_: object) -> None:
    init_container()


@worker_process_shutdown.connect
def _on_worker_process_shutdown(**_: object) -> None:
    shutdown_container()
```

Note: `worker_process_shutdown` is best-effort and may not run on hard process termination.
Note: ensure the module containing these signal handlers is imported by the worker at startup
(for example via `imports` / `include` settings, or by importing `bootstrap` from task modules).

## Thin Task Entry Point

```python
from celery import shared_task
from bootstrap import get_container


@shared_task(name="domain_a.process_data")
def process_data_task(record_id: int) -> dict:
    processor = get_container().domain_a.data_processor_service()
    result = processor.execute(record_id)
    return {"status": "success", "data": result}
```

## Validation

1. Task modules do not instantiate services directly.
2. Container lifecycle hooks are process-safe.
3. Cleanup logic that must always run is inside task logic, not only signal handlers.
