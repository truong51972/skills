---
name: dependency-injection
description: >
    Production-ready guide for implementing scalable Dependency Injection architecture
    using the dependency-injector library. Use this when asked to set up or refactor
    a DI container, wire services and infrastructure resources, manage provider scopes
    (Singleton, Factory, Resource), structure domain sub-containers, integrate DI with
    Celery worker or FastAPI entry points, or write tests using container overrides.
---

## Skill: Scalable Dependency Injection Architecture

**Goals:**
* Keep task modules and controllers thin and highly testable.
* Centralize the wiring of services, factories, and external resources.
* Eliminate manual object instantiation in business logic (favor Composition over Inheritance).
* Support a deterministic process lifecycle for worker-based or API-based systems.

---

### 1) Recommended DI Architecture

Use a strictly layered wiring approach:

1. **Settings Layer:** A single configuration object (loaded via Pydantic) injected globally.
2. **Resource Layer:** Long-lived infrastructure clients requiring explicit setup/teardown (e.g., DB connection pools, HTTP sessions).
3. **Core Services Layer:** Shared, cross-domain business logic.
4. **Domain Sub-container Layer:** Bounded contexts grouped into dedicated containers to prevent a "God Container" (e.g., `BillingContainer`, `NotificationContainer`).
5. **Entry-point Layer:** The *only* place where dependencies are resolved (Tasks, API Endpoints, Event Handlers).

---

### 2) Suggested Folder Layout

```text
my_project/
├── src/ (or app/)
│   ├── config.py
│   ├── bootstrap.py         # Container lifecycle management
│   ├── containers/
│   │   ├── container.py     # Root container
│   │   └── domain_a/        # Domain-specific sub-container
│   │       └── container.py
│   ├── infrastructure/      # Resource initialization (yield-based)
│   │   └── db_client.py
│   ├── services/
│   │   ├── core/
│   │   └── domain_a/
│   └── tasks/               # Entry points (Resolves DI)
│       └── domain_a_tasks.py
```

---

### 3) Code Templates

#### 3.1 Resource Generator Template (`infrastructure/clients.py`)
Use generator functions for resources that need teardown.

```python
from typing import Iterator

def init_http_client(timeout: int) -> Iterator[object]: # Replace object with actual client type
    client = "MockedHttpClient(timeout=timeout)"
    print("Opening HTTP connection...")
    yield client
    print("Closing HTTP connection...")
```

#### 3.2 Root Container (`containers/container.py`)

```python
from dependency_injector import containers, providers

from config import Settings
from infrastructure.clients import init_http_client
from containers.domain_a.container import DomainAContainer


class Container(containers.DeclarativeContainer):
    # 1. Configuration
    settings = providers.Singleton(Settings)

    # 2. Infra/Resource providers (Using Resource for automatic setup/teardown)
    http_client = providers.Resource(
        init_http_client,
        timeout=settings.provided.HTTP_TIMEOUT,
    )

    # 3. Domain sub-containers
    domain_a = providers.Container(
        DomainAContainer,
        settings=settings,
        http_client=http_client,
    )
```

#### 3.3 Domain Sub-container (`containers/domain_a/container.py`)

```python
from dependency_injector import containers, providers

from config import Settings
from services.domain_a.processor import DataProcessorService


class DomainAContainer(containers.DeclarativeContainer):
    # Dependencies required from the root container
    settings = providers.Dependency(instance_of=Settings)
    http_client = providers.Dependency()

    # Domain-specific services
    data_processor_service = providers.Factory(
        DataProcessorService,
        http_client=http_client,
        feature_flag=settings.provided.ENABLE_NEW_FEATURE,
    )
```

#### 3.4 Worker Lifecycle Bootstrap (`bootstrap.py`)

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
            _container.init_resources()  # Triggers setup in providers.Resource
            logger.info("DI Container initialized and resources acquired.")
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
                _container.shutdown_resources()  # Triggers teardown in providers.Resource
                logger.info("DI Container resources safely released.")
        except Exception as e:
            logger.error(f"Error releasing resources: {e}", exc_info=True)
        finally:
            if _container is not None:
                _container.reset_singletons()
            _container = None


@worker_process_init.connect
def _on_worker_process_init(**_: object) -> None:
    init_container()


@worker_process_shutdown.connect
def _on_worker_process_shutdown(**_: object) -> None:
    shutdown_container()
```

#### 3.5 Task Usage (Entry-point)

```python
from bootstrap import get_container
from celery import shared_task


@shared_task(name="domain_a.process_data")
def process_data_task(record_id: int) -> dict:
    # 1. Resolve dependencies at the edge
    container = get_container()
    processor = container.domain_a.data_processor_service()

    # 2. Delegate to the service (Keep task logic thin)
    result = processor.execute(record_id)

    return {"status": "success", "data": result}
```

---

### 4) DI Best Practices

1. **Keep composition at the edges:** Build and wire dependencies ONLY in containers. Resolve them ONLY at system entry points (Celery tasks, FastAPI endpoints).
2. **Use explicit provider scopes:**
   * `providers.Singleton`: For stateless services or expensive, shared logic.
   * `providers.Factory`: For request/task-specific objects where a fresh instance is needed.
   * `providers.Resource`: For infrastructure requiring explicit connection and teardown (DBs, sessions).
3. **Prefer sub-containers for Bounded Contexts:** Split large root containers into domain containers to reduce coupling and improve code navigation.
4. **Stabilize interfaces at boundaries:** Depend on Python `Protocols` or Abstract Base Classes (ABCs) where possible. This makes mocking and substituting implementations seamless.
5. **Keep settings centralized:** Read `.env` variables strictly in the `Settings` class. Inject configuration down the tree. Never use `os.environ.get()` deep in a service class.

---

### 5) Anti-patterns to Avoid

1. **Service Locator Abuse:** Never pass the `Container` itself into a service class, and do not call `get_container()` deep inside business logic. Pass explicit dependencies via the constructor (`__init__`).
2. **Hidden Side Effects in Constructors:** Avoid network calls, heavy IO, or DB queries inside a class `__init__`. Put expensive setup in `providers.Resource` or explicit lifecycle methods.
3. **Global Mutable State:** Do not maintain state in global variables outside the container's control. Let the container manage singletons.
4. **Framework Leaks:** Your domain services should not know about `Celery.Task` objects or HTTP Request objects. Parse these at the entry point and pass pure data structures to the service.

---

### 6) Testing Strategy

Use `override()` to inject fakes/mocks dynamically during unit tests.

```python
import pytest
from bootstrap import init_container

@pytest.fixture
def container():
    container_instance = init_container()
    yield container_instance
    # Crucial: Reset overrides after test to prevent state leakage
    container_instance.reset_override()

def test_data_processor_with_fake(container):
    class FakeProcessor:
        def execute(self, record_id):
            return "fake_result"

    # Override the provider with the fake implementation
    container.domain_a.data_processor_service.override(
        lambda: FakeProcessor()
    )

    # Resolution now yields the fake
    service = container.domain_a.data_processor_service()
    assert service.execute(123) == "fake_result"
```

---

### 7) Recommended Stack

* **Core DI:** `dependency-injector`
* **Configuration:** `pydantic-settings`
* **Testing:** `pytest`, `pytest-mock`