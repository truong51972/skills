# FastAPI Integration

Use this reference for FastAPI/ASGI apps, async resources, app lifespan, native
`Depends`, and optional `dependency-injector` wiring.

## Default Approach

Prefer this order:

1. Build the container in `create_app()`.
2. Initialize and shut down resources in FastAPI lifespan.
3. Store the running container on `app.state.container`.
4. Use native `Annotated` dependencies with `Depends` in routes.
5. Add `Provide[...]` wiring only when it is already useful for the project.

## Application Factory and Lifespan

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import router
from containers import build_container


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    container = build_container()
    await container.init_resources()
    app.state.container = container
    try:
        yield
    finally:
        await container.shutdown_resources()
        del app.state.container


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    return app
```

This keeps async resources in the same ASGI lifespan and event loop that serves
requests.

## Native FastAPI Dependencies First

Use native dependencies for request-scoped objects and route-level composition.

```python
from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request

from containers import Container
from services.processor import DataProcessorService

router = APIRouter()


def get_container(request: Request) -> Container:
    return cast(Container, request.app.state.container)


async def get_processor(
    container: Annotated[Container, Depends(get_container)],
) -> DataProcessorService:
    return await container.data_processor.async_()


@router.get("/records/{record_id}")
async def process_record(
    record_id: int,
    processor: Annotated[DataProcessorService, Depends(get_processor)],
) -> dict[str, object]:
    result = await processor.execute(record_id)
    return {"data": result}
```

If the provider graph is fully synchronous, call `container.data_processor()`
instead of awaiting `async_()`.

For per-request resources such as database sessions or transactions, prefer FastAPI
dependencies with `yield`:

```python
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from containers import Container


def get_session_factory(
    container: Annotated[Container, Depends(get_container)],
) -> async_sessionmaker[AsyncSession]:
    return container.session_factory()


async def get_session(
    session_factory: Annotated[
        async_sessionmaker[AsyncSession],
        Depends(get_session_factory),
    ],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
```

## Optional Wiring Pattern

Use wiring when the project already uses `dependency-injector.wiring` broadly or when
it removes repetitive boundary dependencies. The `@inject` decorator must be directly
above the route function, below the FastAPI route decorator.

```python
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from containers import Container
from services.processor import DataProcessorService

router = APIRouter()


@router.get("/wired-records/{record_id}")
@inject
async def process_record_wired(
    record_id: int,
    processor: Annotated[
        DataProcessorService,
        Depends(Provide[Container.data_processor]),
    ],
) -> dict[str, object]:
    result = await processor.execute(record_id)
    return {"data": result}
```

Wire and unwire the running container instance in lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    container = build_container()
    await container.init_resources()
    container.wire(packages=["api"])
    app.state.container = container
    try:
        yield
    finally:
        container.unwire()
        await container.shutdown_resources()
        del app.state.container
```

Use marker class paths that match the actual running container. String identifiers
can reduce import coupling, but they still require the target modules to be wired.

## Advanced Starlette Lifespan Provider

`dependency_injector.ext.starlette.Lifespan` can initialize container resources for
ASGI apps. Use it only when the app itself is intentionally assembled by providers.
For most FastAPI codebases, an explicit `create_app()` lifespan is easier to read,
test, and override.

## Validation Checklist

1. FastAPI uses `FastAPI(lifespan=...)`.
2. Async containers call `await container.init_resources()` and `await container.shutdown_resources()`.
3. `app.state.container` is assigned only after resources initialize successfully.
4. Request-scoped cleanup is modeled with native FastAPI `yield` dependencies.
5. Wired routes have `@inject` immediately above the route function.
6. `container.unwire()` runs during shutdown if wiring is used.
