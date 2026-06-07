# Core DI Architecture

Use this reference for baseline `dependency-injector` container design, provider
selection, settings injection, and package boundaries.

## Target Structure

Choose names that match the repo, but keep the same responsibilities:

```text
src/
|-- config.py                  # Pydantic settings only
|-- containers.py              # root container and build_container()
|-- infrastructure/            # clients, pools, gateways, repositories
|-- services/                  # framework-free business services
|-- api/                       # FastAPI routes and dependencies
|-- tasks/                     # Celery task entry points
`-- bootstrap/                 # runtime lifecycle glue, if needed
```

Large projects can split containers by package. Keep one root application container
that supplies infrastructure dependencies to smaller package containers.

## Settings Pattern

Use Pydantic settings as the validation boundary. Load the validated object into a
strict `providers.Configuration` provider.

```python
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    upstream_base_url: str
    http_timeout_seconds: float = 10.0
    enable_new_feature: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
```

```python
# containers.py
from dependency_injector import containers, providers

from config import Settings
from infrastructure.http import init_http_client
from services.processor import DataProcessorService


class Container(containers.DeclarativeContainer):
    config = providers.Configuration(strict=True)

    http_client = providers.Resource(
        init_http_client,
        base_url=config.upstream_base_url,
        timeout=config.http_timeout_seconds,
    )

    data_processor = providers.Factory(
        DataProcessorService,
        http_client=http_client,
        feature_enabled=config.enable_new_feature,
    )


def build_container(settings: Settings | None = None) -> Container:
    container = Container()
    container.config.from_pydantic(settings or Settings())
    return container
```

## Resource Initializers

Use `Resource` for anything that must be opened and closed explicitly: HTTP clients,
database engines, connection pools, thread pools, model handles, and SDK sessions.

```python
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

import httpx


@contextmanager
def init_http_client(
    base_url: str,
    timeout: float,
) -> Iterator[httpx.Client]:
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        yield client


@asynccontextmanager
async def init_async_http_client(
    base_url: str,
    timeout: float,
) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
        yield client
```

If a container has any async resource, call container lifecycle methods with `await`:

```python
container = build_container()
await container.init_resources()
try:
    ...
finally:
    await container.shutdown_resources()
```

## Provider Scope Guide

| Provider | Default use |
|---|---|
| `providers.Factory` | Application services, use cases, repositories, request/task-scoped objects |
| `providers.Singleton` | Stateless, thread-safe, event-loop-neutral shared objects only |
| `providers.Resource` | Clients, pools, engines, and resources with explicit lifecycle |
| `providers.Dependency` | Inputs required by a package/sub-container from the root container |
| `providers.Configuration` | Validated settings values loaded from Pydantic settings |

Prefer `Factory` until there is a clear reason to share an instance. Avoid
`Singleton` for mutable request state, database sessions, event-loop-bound async
clients, and anything that needs teardown.

## Package Boundary Pattern

Use `providers.Dependency` inside package containers so packages do not know where
infrastructure comes from.

```python
from dependency_injector import containers, providers

from billing.services import BillingService
from infrastructure.http import init_http_client


class BillingContainer(containers.DeclarativeContainer):
    http_client = providers.Dependency()

    billing_service = providers.Factory(
        BillingService,
        http_client=http_client,
    )


class Container(containers.DeclarativeContainer):
    config = providers.Configuration(strict=True)

    http_client = providers.Resource(
        init_http_client,
        base_url=config.upstream_base_url,
        timeout=config.http_timeout_seconds,
    )

    billing = providers.Container(
        BillingContainer,
        http_client=http_client,
    )
```

## Core Rules

1. Use container instances, not class-level providers, when resolving dependencies.
2. Resolve providers at runtime entry points: routes, tasks, CLIs, event handlers, tests.
3. Inject dependencies through constructors; avoid service locator calls inside services.
4. Keep business logic free of framework imports and environment access.
5. Put heavy IO and teardown in `Resource` initializers, not service constructors.
6. Split containers by package only when it reduces coupling or matches repo boundaries.
