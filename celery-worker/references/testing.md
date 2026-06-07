# Testing Celery Workers

Use this reference when designing tests for services, task wrappers, Celery
integration, DI overrides, or smoke tests.

## Testing Pyramid

- Service unit tests: fastest and most important. They do not import Celery.
- Task wrapper unit tests: validate payload parsing, delegation, return shape,
  and retry behavior with mocks.
- Celery integration tests: run a real worker with test broker/backend fixtures.
- Smoke/production tests: run workers and brokers in containers or the target
  deployment shape.

Eager mode is only an emulation. It is useful for narrow producer wiring checks,
but it does not prove worker process behavior, broker semantics, signals,
prefetch, acknowledgement, or shutdown.

## Service Unit Test

```python
from my_worker.services.orders import OrderService


def test_process_order_is_idempotent(order_repo, upstream_client) -> None:
    service = OrderService(order_repo=order_repo, upstream_client=upstream_client)

    first = service.process_order(job_id="job-1", order_id="ord-1", task_id="task-1")
    second = service.process_order(job_id="job-1", order_id="ord-1", task_id="task-2")

    assert first.status == "processed"
    assert second.status == "processed"
    assert order_repo.count_side_effects("job-1") == 1
```

## Task Wrapper Unit Test

```python
from unittest.mock import Mock, patch

from my_worker.tasks.orders import process_order


def test_process_order_delegates_to_service() -> None:
    service = Mock()
    service.process_order.return_value.status = "processed"

    container = Mock()
    container.order_service.return_value = service

    with patch("my_worker.tasks.orders.get_container", return_value=container):
        result = process_order.run({"job_id": "job-1", "order_id": "ord-1"})

    assert result == {"job_id": "job-1", "status": "processed"}
    service.process_order.assert_called_once()
```

For retry tests, mock the service to raise a transient exception and assert the
task raises Celery's retry sentinel or that `apply_async` records a retry in an
integration test. Keep permanent errors out of `autoretry_for`.

## DI Override Hygiene

Use provider override context managers so cleanup is automatic:

```python
from unittest.mock import Mock, patch

from dependency_injector import providers

from my_worker.tasks.orders import process_order


def test_task_with_container_override(container) -> None:
    service = Mock()
    service.process_order.return_value.status = "processed"

    with (
        container.order_service.override(providers.Object(service)),
        patch("my_worker.tasks.orders.get_container", return_value=container),
    ):
        result = process_order.run({"job_id": "job-1", "order_id": "ord-1"})

    assert result["status"] == "processed"
```

If a Celery worker process owns its own container, override the provider before
the worker starts or expose a test-only container factory fixture.

## Celery Integration with `celery.contrib.pytest`

Enable the plugin in `conftest.py`:

```python
pytest_plugins = ("celery.contrib.pytest",)
```

Use in-memory transports only for behavior that does not depend on a real
broker:

```python
import pytest


@pytest.fixture
def celery_config() -> dict[str, object]:
    return {
        "broker_url": "memory://",
        "result_backend": "cache+memory://",
        "task_serializer": "json",
        "accept_content": ["json"],
        "result_serializer": "json",
        "task_always_eager": False,
    }


def test_process_order_with_worker(celery_app, celery_worker) -> None:
    from my_worker.tasks.orders import process_order

    celery_app.tasks.register(process_order)
    celery_worker.reload()

    result = process_order.delay({"job_id": "job-1", "order_id": "ord-1"})

    assert result.get(timeout=10)["job_id"] == "job-1"
```

Use `pytest-celery` for Docker-backed smoke tests when broker behavior matters,
especially Redis visibility timeout, RabbitMQ routing, SQS visibility timeout,
late acknowledgements, or worker shutdown.

## Eager Mode Caveat

When a narrow test intentionally uses eager mode, remember:

- It runs in the calling process, not a worker child process.
- It does not exercise worker signals, broker delivery, prefetch, or shutdown.
- Eager results are not stored unless `task_store_eager_result` is enabled.
- It should not be the only test for retry/acknowledgement behavior.

## Test Checklist

- Services are tested without Celery imports.
- Task wrappers are tested for validation, delegation, and serializable return
  shape.
- Transient failures are covered separately from permanent business failures.
- Provider overrides use context managers and do not leak between tests.
- At least one worker-backed integration test covers critical task registration.
- Broker-specific reliability claims are tested with that broker, not only with
  memory transport or eager mode.
