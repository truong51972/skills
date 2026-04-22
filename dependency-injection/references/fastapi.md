# FastAPI Sub-skill

Use this sub-skill when the runtime is FastAPI/ASGI and resources are asynchronous.

## Procedure

1. Define a dedicated async container.
2. Manage resource lifecycle in FastAPI lifespan.
3. Wire routes after resources are initialized.
4. Use matching provider markers in `Provide[...]`.

## Async Container

```python
from dependency_injector import containers, providers

from config import Settings
from infrastructure.clients import init_http_client_async
from containers.domain_a.container import DomainAContainer


class AsyncContainer(containers.DeclarativeContainer):
    settings = providers.Singleton(Settings)

    http_client = providers.Resource(
        init_http_client_async,
        timeout=settings.provided.HTTP_TIMEOUT,
    )

    domain_a = providers.Container(
        DomainAContainer,
        settings=settings,
        http_client=http_client,
    )
```

## Lifespan Bootstrap

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from containers.async_container import AsyncContainer


_container: AsyncContainer | None = None


def get_container() -> AsyncContainer:
    if _container is None:
        raise RuntimeError("Container not initialised. Is the lifespan running?")
    return _container


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _container
    _container = AsyncContainer()
    await _container.init_resources()
    _container.wire(packages=["src"])
    try:
        yield
    finally:
        _container.unwire()
        await _container.shutdown_resources()
        _container = None
```

## Route Injection Patterns

```python
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from bootstrap_async import get_container
from containers.async_container import AsyncContainer
from services.domain_a.processor import DataProcessorService

router = APIRouter()


@router.get("/process/{record_id}")
async def process_record(record_id: int) -> dict:
    processor: DataProcessorService = get_container().domain_a.data_processor_service()
    return {"data": await processor.execute_async(record_id)}


@router.get("/process-wired/{record_id}")
@inject
async def process_record_wired(
    record_id: int,
    processor: DataProcessorService = Depends(
        Provide[AsyncContainer.domain_a.data_processor_service]
    ),
) -> dict:
    return {"data": await processor.execute_async(record_id)}
```

## Validation

1. `init_resources()` and `shutdown_resources()` are awaited.
2. Marker container class in `Provide[...]` matches the wired container class.
3. `unwire()` is called on shutdown if wiring is used.
