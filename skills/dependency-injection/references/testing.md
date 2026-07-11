# Testing and Overrides

Use this reference for provider overrides, FastAPI dependency overrides, lifespan
tests, async HTTPX clients, fakes, mocks, and fixture hygiene.

## Override Rules

Prefer context managers. They keep override scope local to the test.

```python
from unittest.mock import Mock


def test_processor_uses_gateway(container):
    gateway = Mock()
    gateway.fetch.return_value = {"id": 123}

    with container.gateway.override(gateway):
        processor = container.data_processor()
        assert processor.execute(123) == {"id": 123}
```

For multiple providers, use container-level provider overrides as a context manager:

```python
def test_many_overrides(container, fake_gateway, fake_cache):
    with container.override_providers(
        gateway=fake_gateway,
        cache=fake_cache,
    ):
        service = container.data_processor()
        assert service.execute(123)
```

If a test cannot use a context manager, reset that provider explicitly:

```python
def test_manual_override_cleanup(container, fake_gateway):
    container.gateway.override(fake_gateway)
    try:
        assert container.data_processor().execute(123)
    finally:
        container.gateway.reset_override()
```

## Container Fixtures

Sync resources:

```python
import pytest

from config import Settings
from containers import Container, build_container


@pytest.fixture()
def container() -> Container:
    c = build_container(Settings(upstream_base_url="https://example.test"))
    c.init_resources()
    try:
        yield c
    finally:
        c.shutdown_resources()
```

Async resources:

```python
import pytest_asyncio

from config import Settings
from containers import Container, build_container


@pytest_asyncio.fixture()
async def async_container() -> Container:
    c = build_container(Settings(upstream_base_url="https://example.test"))
    await c.init_resources()
    try:
        yield c
    finally:
        await c.shutdown_resources()
```

When an async provider is in async mode, await it in tests:

```python
async def test_async_provider(async_container: Container) -> None:
    service = await async_container.data_processor.async_()
    assert await service.execute(123)
```

## FastAPI Dependency Overrides

Use FastAPI overrides for native `Depends` dependencies, and clear them after the
test.

```python
from fastapi.testclient import TestClient

from api.dependencies import get_current_user
from main import create_app


def test_authenticated_route() -> None:
    app = create_app()

    async def override_user() -> dict[str, str]:
        return {"sub": "test-user"}

    app.dependency_overrides[get_current_user] = override_user
    try:
        with TestClient(app) as client:
            response = client.get("/me")
    finally:
        app.dependency_overrides = {}

    assert response.status_code == 200
```

Use `TestClient` as a context manager so FastAPI lifespan runs.

## Async FastAPI Tests With HTTPX

HTTPX `ASGITransport` does not trigger ASGI lifespan events by itself. Use
`asgi-lifespan` when testing an app with lifespan-managed DI resources.

```python
import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from main import create_app


@pytest.mark.asyncio
async def test_records_endpoint() -> None:
    app = create_app()

    async with LifespanManager(app) as manager:
        transport = ASGITransport(app=manager.app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            response = await client.get("/records/123")

    assert response.status_code == 200
```

To override providers that are created during lifespan, apply the override after
lifespan starts:

```python
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_provider_override_inside_lifespan() -> None:
    app = create_app()

    async with LifespanManager(app) as manager:
        service = AsyncMock()
        service.execute.return_value = {"id": 123}

        with app.state.container.data_processor.override(service):
            transport = ASGITransport(app=manager.app)
            async with AsyncClient(
                transport=transport,
                base_url="http://test",
            ) as client:
                response = await client.get("/records/123")

    assert response.json() == {"data": {"id": 123}}
```

## Checklist

1. Prefer override context managers for providers.
2. Use `reset_override()` only as explicit cleanup when a context manager is not enough.
3. Clear FastAPI dependency overrides with `app.dependency_overrides = {}`.
4. Run FastAPI lifespan in tests.
5. Keep tests independent from ambient environment and module-global container state.
6. Use fakes/mocks at provider or native dependency boundaries, not by patching service internals.
