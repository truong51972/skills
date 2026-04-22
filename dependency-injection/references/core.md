# Core DI Architecture

Use this sub-skill for container structure, provider selection, and shared dependency patterns.

## Target Structure

```text
src/
├── config.py
├── containers/
│   ├── container.py
│   ├── async_container.py
│   └── domain_a/container.py
├── infrastructure/clients.py
├── services/
├── bootstrap.py
├── bootstrap_async.py
├── api/
└── tasks/
```

`containers/async_container.py` is runtime-specific for async apps; define it as the async counterpart of
`containers/container.py` (detailed in the FastAPI track).

## Resource Initializers

```python
from collections.abc import AsyncIterator, Iterator
import httpx


def init_http_client_sync(timeout: int) -> Iterator[httpx.Client]:
    client = httpx.Client(timeout=timeout)
    try:
        yield client
    finally:
        client.close()


async def init_http_client_async(timeout: int) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        yield client
```

## Root Container (Sync Base)

```python
from dependency_injector import containers, providers

from config import Settings
from infrastructure.clients import init_http_client_sync
from containers.domain_a.container import DomainAContainer


class Container(containers.DeclarativeContainer):
    settings = providers.Singleton(Settings)

    http_client = providers.Resource(
        init_http_client_sync,
        timeout=settings.provided.HTTP_TIMEOUT,
    )

    domain_a = providers.Container(
        DomainAContainer,
        settings=settings,
        http_client=http_client,
    )
```

## Domain Sub-container

```python
from dependency_injector import containers, providers

from config import Settings
from services.domain_a.processor import DataProcessorService


class DomainAContainer(containers.DeclarativeContainer):
    settings = providers.Dependency(instance_of=Settings)
    http_client = providers.Dependency()

    data_processor_service = providers.Factory(
        DataProcessorService,
        http_client=http_client,
        feature_flag=settings.provided.ENABLE_NEW_FEATURE,
    )
```

## Provider Scope Guide

| Provider | Use for |
|---|---|
| `providers.Singleton` | Shared stateless services |
| `providers.Factory` | Request/task-scoped service instances |
| `providers.Resource` | Components with explicit init/shutdown lifecycle |

## Core Rules

1. Resolve providers only at entry points (API handlers, tasks, event handlers).
2. Inject dependencies through constructors; avoid service locator patterns inside services.
3. Keep heavy IO out of service `__init__` and place it in `providers.Resource`.
4. Inject settings values; do not read environment variables directly in business logic.
