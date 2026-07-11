# Worker Lifecycle and Dependency Injection

Use this reference when a Celery worker needs process-level resources such as
database pools, HTTP/gRPC clients, Redis clients, ML models, or repositories.

## Runtime Model

- In prefork mode, Celery imports modules in the parent process and then forks
  child worker processes.
- Do not create fork-unsafe resources during module import in the parent
  process.
- Initialize process-local resources in `worker_process_init` or lazily on first
  task execution inside the child.
- Celery signal handlers should accept `**kwargs` so they keep working as Celery
  adds arguments.
- `worker_process_init` must not block for long. Keep it fast; lazily load very
  slow resources if startup can exceed a few seconds.
- `worker_process_shutdown` is best-effort and may not be called. Abrupt exits
  must not corrupt state.

## Synchronous Container Bootstrap

```python
import logging
import threading

from celery.signals import (
    worker_before_create_process,
    worker_process_init,
    worker_process_shutdown,
    worker_shutdown,
)

from my_worker.containers import Container, build_container

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
            logger.info("worker container initialized")
    return _container


def get_container() -> Container:
    return _container if _container is not None else init_container()


def shutdown_container() -> None:
    global _container
    with _lock:
        container = _container
        _container = None

    if container is None:
        return

    try:
        container.shutdown_resources()
    except Exception:
        logger.exception("worker container shutdown failed")
    finally:
        container.reset_singletons()


@worker_before_create_process.connect
def _before_create_process(**kwargs: object) -> None:
    # Close or reset any accidental parent-process global clients here.
    # Most projects should keep this empty because resources are child-local.
    return None


@worker_process_init.connect
def _on_worker_process_init(**kwargs: object) -> None:
    init_container()


@worker_process_shutdown.connect
def _on_worker_process_shutdown(**kwargs: object) -> None:
    shutdown_container()


@worker_shutdown.connect
def _on_worker_shutdown(**kwargs: object) -> None:
    # Safe fallback for solo pools or partial startup; no-op if no child
    # container exists in this process.
    shutdown_container()
```

Import this bootstrap module from the Celery app module for side effects:

```python
from celery import Celery

import my_worker.bootstrap  # noqa: F401

app = Celery("my_worker")
```

## Container Pattern

```python
from contextlib import contextmanager
from collections.abc import Iterator

import httpx
from dependency_injector import containers, providers
from pydantic_settings import BaseSettings, SettingsConfigDict

from my_worker.services.orders import OrderService


class Settings(BaseSettings):
    upstream_base_url: str
    upstream_timeout_seconds: float = 10.0

    model_config = SettingsConfigDict(env_prefix="WORKER_", extra="ignore")


@contextmanager
def init_http_client(base_url: str, timeout: float) -> Iterator[httpx.Client]:
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        yield client


class Container(containers.DeclarativeContainer):
    config = providers.Configuration(strict=True)

    http_client = providers.Resource(
        init_http_client,
        base_url=config.upstream_base_url,
        timeout=config.upstream_timeout_seconds,
    )

    order_service = providers.Factory(
        OrderService,
        http_client=http_client,
    )


def build_container(settings: Settings | None = None) -> Container:
    settings = settings or Settings()
    container = Container()
    container.config.from_pydantic(settings)
    return container
```

Use `Factory` for services by default. Use `Singleton` only for immutable,
thread-safe, process-safe objects. Use `Resource` for clients and pools that
must be initialized and shut down.

## Async Resources

If any provider uses an async initializer, `init_resources()` and
`shutdown_resources()` must be awaited. Celery task execution is synchronous by
default, so choose one explicit strategy:

- Prefer synchronous clients for standard Celery workers.
- Or isolate async clients behind a service that owns an event-loop strategy.
- Or initialize async resources with `asyncio.run()` in a sync worker process
  when no event loop is already running.

```python
import asyncio

from my_worker.containers import Container, build_container


def init_async_container() -> Container:
    container = build_container()
    asyncio.run(container.init_resources())
    return container


def shutdown_async_container(container: Container) -> None:
    asyncio.run(container.shutdown_resources())
```

Do not share async clients created in one event loop with work running in a
different event loop.

## Lifecycle Checklist

- Bootstrap module is imported by the Celery app module.
- No network clients, DB pools, model sessions, or event-loop resources are
  created at import time.
- Signal handlers accept `**kwargs`.
- Initialization in `worker_process_init` is fast enough for Celery startup.
- Shutdown logs failures but does not mask worker termination.
- Resources tolerate abrupt process death because shutdown is best-effort.
