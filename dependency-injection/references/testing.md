# Testing Sub-skill

Use this sub-skill for provider overrides, fakes/mocks, and DI fixture hygiene.

## Override Rules

1. Override one provider: `provider.override(...)`.
2. Override many providers: `container.override_providers(...)`.
3. Override full container: `container.override(another_container)`.
4. Always clean up with `reset_override()`.

## Sync Fixture Pattern

```python
import pytest

from bootstrap import init_container
from containers.container import Container


@pytest.fixture()
def container() -> Container:
    c = init_container()
    yield c
    c.reset_override()
```

## Async Fixture Pattern

```python
import pytest_asyncio

from containers.async_container import AsyncContainer


@pytest_asyncio.fixture()
async def async_container() -> AsyncContainer:
    c = AsyncContainer()
    await c.init_resources()
    yield c
    await c.shutdown_resources()
    c.reset_override()
```

## Fake Override Example

```python
def test_data_processor_with_fake(container: Container) -> None:
    class FakeProcessor:
        def execute(self, record_id: int) -> str:
            return "fake_result"

    container.domain_a.data_processor_service.override(FakeProcessor())

    service = container.domain_a.data_processor_service()
    assert service.execute(123) == "fake_result"

    container.domain_a.data_processor_service.reset_override()
```

## Checklist

1. Use `reset_override()` (not `reset_overrides()`).
2. Avoid leaked overrides between tests.
3. Keep tests independent from environment/global state.
4. For async resources, always await setup and teardown.
