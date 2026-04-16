---
name: celery-worker
description: >
    Production-ready architecture guide for building scalable Celery workers.
    Use this when asked to create, structure, or refactor a Celery worker project,
    configure brokers and queues, manage worker lifecycle (init/shutdown), implement
    idempotent tasks, set up dependency injection, or apply Clean Architecture
    patterns to a task queue system.
---

## Skill: Scalable Celery Worker Architecture

**Goals:**
* Provide a production-ready, highly scalable template for Celery workers.
* Enforce Clean Architecture by strictly separating configuration, infrastructure (queues, routing), process lifecycle hooks, and business logic (services).
* Ensure fault tolerance, graceful shutdowns, and idempotent task execution.

---

### 1) Recommended Project Structure

Choose either `src` or `app` as the source root and maintain consistency.

```text
my_worker/
├── .env
├── pyproject.toml
├── README.md
└── src/ (or app/)
    ├── main.py              # Celery app initialization
    ├── celeryconfig.py      # Queues, concurrency, broker settings
    ├── config.py            # Environment variables via Pydantic
    ├── bootstrap.py         # Process lifecycle (init/shutdown resources)
    ├── tasks/               # Thin wrappers, routing to services
    │   ├── __init__.py
    │   ├── heavy_jobs.py
    │   └── periodic.py      # (Optional) for Celery Beat tasks
    ├── services/            # Pure business logic (isolated for testing)
    │   ├── __init__.py
    │   └── domain_service.py
    ├── containers/          # Dependency Injection setup
    │   └── container.py
    ├── schemas/             # Pydantic models for Task payloads
    │   └── payload.py
    └── utils/
        ├── logging.py
        └── retry.py
```

---

### 2) Core Code Templates

#### 2.1 `main.py`
Creates the Celery app and hooks into process lifecycles.

```python
from celery import Celery

# Side-effect import to register worker lifecycle signals (init/shutdown).
import bootstrap  # noqa: F401

app = Celery("my_worker")
app.config_from_object("celeryconfig")

if __name__ == "__main__":
    app.start()
```

#### 2.2 `config.py`
Validates environment variables safely.

```python
from pathlib import Path
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API & Internal endpoints
    WEB_URL: str = "http://localhost:8000"
    
    # Broker & Backend
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None

    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    CELERY_TASK_DEFAULT_QUEUE: str = "my_worker"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def set_default_celery_urls(self) -> "Settings":
        if not self.REDIS_URL:
            auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
            self.REDIS_URL = f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/0"

        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL

        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL

        return self
```

#### 2.3 `celeryconfig.py`
Defines strict worker behaviors, prioritizing reliability and fair distribution for heavy tasks.

```python
from config import Settings

settings = Settings()

broker_url = settings.CELERY_BROKER_URL
result_backend = settings.CELERY_RESULT_BACKEND

task_queues = {
    settings.CELERY_TASK_DEFAULT_QUEUE: {
        "exchange": settings.CELERY_TASK_DEFAULT_QUEUE,
        "routing_key": settings.CELERY_TASK_DEFAULT_QUEUE,
    },
}
task_default_queue = settings.CELERY_TASK_DEFAULT_QUEUE
task_create_missing_queues = True

# Core behavior
task_serializer = "json"
accept_content = ["json"]
result_serializer = "json"
enable_utc = True
timezone = "Asia/Ho_Chi_Minh"

# Throughput vs Fairness: '1' prevents a single worker from hoarding long-running tasks.
worker_prefetch_multiplier = 1
worker_concurrency = 4

# Reliability: Acknowledge task only AFTER successful execution.
task_acks_late = True
task_reject_on_worker_lost = True

# Imports
imports = (
    "tasks.heavy_jobs",
    # "tasks.periodic", # Uncomment if using Celery Beat
)

# Optional: Celery Beat Schedule
# beat_schedule = {
#     "cleanup-every-midnight": {
#         "task": "tasks.periodic.cleanup_task",
#         "schedule": crontab(minute=0, hour=0),
#     },
# }
```

#### 2.4 `bootstrap.py`
Thread-safe singleton management for heavy resources (DB pools, ML models) tied to the worker process lifecycle.

```python
import logging
import threading

from celery.signals import worker_process_init, worker_process_shutdown

# Assuming Container inherits from dependency_injector.containers.DeclarativeContainer
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
            logger.info("Initialized container for worker process")
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
                logger.info("Resources gracefully shut down.")
        except Exception as e:
            logger.error(f"Error shutting down resources: {e}", exc_info=True)
        finally:
            if _container is not None:
                _container.reset_singletons()
            _container = None
            logger.info("Container released.")


@worker_process_init.connect
def _on_worker_process_init(**_: object) -> None:
    init_container()


@worker_process_shutdown.connect
def _on_worker_process_shutdown(**_: object) -> None:
    shutdown_container()
```

#### 2.5 Idempotent Task Template (`tasks/heavy_jobs.py`)
Tasks must be thin layers. All business logic lives in the Service layer.

```python
from celery import shared_task

from bootstrap import get_container


@shared_task(
    bind=True,
    autoretry_for=(TimeoutError, ConnectionError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_data(self, payload: dict) -> dict:
    container = get_container()
    service = container.domain_service()

    # Rule: Same input + request_id must yield the same state (Idempotency).
    result = service.process(payload)
    return {"status": "ok", "result": result}
```

---

### 3) Critical Best Practices

1. **Idempotency is Non-Negotiable:** Every task should carry a unique identifier (`job_id` or `request_id`). If a task crashes mid-execution and is retried due to `task_acks_late = True`, it must not duplicate side effects (e.g., creating double records).
2. **Resource Lifecycle Management:** Initialize heavy clients (DB connections, GPU tensors) in `worker_process_init`. Always clean them up in `worker_process_shutdown` using a `try-except-finally` block to prevent resource leaks.
3. **Queue Routing Strategy:** Isolate workloads. Create separate queues for `cpu_heavy`, `io_heavy`, `gpu_heavy`, and `callbacks`. Run dedicated workers for each queue to prevent fast IO tasks from being blocked by slow CPU tasks.
4. **Testing Configurations:** When writing unit/integration tests, set `app.conf.task_always_eager = True`. This forces Celery to execute tasks synchronously within the same process, allowing you to test task logic without spinning up Redis or worker clusters.
5. **Smart Retries:** Only retry transient failures (e.g., `ConnectionError`, `Timeout`). Never auto-retry permanent business-rule errors (e.g., `ValidationError`, `DataNotFound`), as this will endlessly clog the queue.
6. **Timeouts:** Avoid "zombie tasks". Set strict explicit timeouts on external HTTP/gRPC calls (using `httpx` timeouts or equivalent) inside your services.
7. **Observability:** Include context variables (`task_id`, `job_id`, `duration_ms`) in structured logs.

---

### 4) Core Tech Stack & Tooling

* **Task Queue:** `celery`, `redis`
* **Configuration & Validation:** `pydantic`, `pydantic-settings`
* **Dependency Injection:** `dependency-injector` (Highly recommended for instantiating the `Container`)
* **Resilience:** `tenacity` (For granular retries deep inside service layers, independent of Celery's task-level retry)
* **Testing:** `pytest`
* **Periodic Tasks:** `celery-beat` (Optional, if scheduling is required)

---

### 5) Run Commands

**Start standard worker:**
```bash
celery -A main worker --loglevel=info
```

**Start specialized worker for a specific queue with defined concurrency:**
```bash
celery -A main worker -Q gpu_tasks --loglevel=info --concurrency=2
```

**Start Celery Beat (if scheduling periodic tasks):**
```bash
celery -A main beat --loglevel=info
```