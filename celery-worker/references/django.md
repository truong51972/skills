# Django Integration

Use this reference when Celery runs inside a Django project and should use
Django settings, installed apps, ORM models, transactions, or Django-specific
testing tools.

## When to Use Django Integration

- Use the Django pattern when the web app and workers share Django settings and
  `INSTALLED_APPS`.
- Keep standalone worker guidance in [configuration.md](configuration.md) for
  services that do not import Django.
- Keep [tasks.md](tasks.md) rules: pass IDs, keep task wrappers thin, retry only
  transient failures, and make late-acknowledged tasks idempotent.

## Project Setup

Use the canonical `project/celery.py` module and import the app from
`project/__init__.py` so `@shared_task` binds to the project Celery app.

```text
project/
|-- manage.py
|-- project/
|   |-- __init__.py
|   |-- celery.py
|   |-- settings.py
|   `-- urls.py
`-- orders/
    |-- models.py
    |-- services.py
    `-- tasks.py
```

```python
# project/celery.py
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

app = Celery("project")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

```python
# project/__init__.py
from .celery import app as celery_app

__all__ = ("celery_app",)
```

The `os.environ.setdefault()` call belongs in this setup module, before the app
is created. Do not read environment variables directly inside tasks or services.

## Django Settings

With `namespace="CELERY"`, Django settings use uppercase `CELERY_` names that
map to Celery's lowercase configuration keys.

```python
# project/settings.py
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_TASK_DEFAULT_QUEUE = "default"

CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_IGNORE_RESULT = True

CELERY_TIMEZONE = TIME_ZONE
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_SOFT_TIME_LIMIT = 840
CELERY_TASK_TIME_LIMIT = 900
```

Use the project's normal settings loader for secrets and environment-specific
values. Do not introduce a second settings system only for Celery unless the
project already standardizes on one.

## Task Modules

Place reusable app tasks in `app_name/tasks.py` and use `@shared_task`.

```python
# orders/tasks.py
from typing import Any

import httpx
from celery import Task, shared_task

from orders.services import process_order


@shared_task(
    bind=True,
    name="orders.process_order",
    autoretry_for=(httpx.TimeoutException, httpx.TransportError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def process_order_task(self: Task, order_id: int, job_id: str) -> dict[str, Any]:
    result = process_order(
        order_id=order_id,
        job_id=job_id,
        task_id=self.request.id,
    )
    return {"order_id": order_id, "status": result.status}
```

Prefer service functions/classes for business logic. The service may use Django
ORM, repositories, or domain modules, but the task wrapper should stay small.

## Transactions

Do not enqueue tasks that depend on newly written rows before the surrounding
transaction commits.

Use Celery 5.4+ `delay_on_commit()` when available:

```python
from django.db import transaction

from orders.models import Order
from orders.tasks import process_order_task


@transaction.atomic
def confirm_order(order_id: int) -> Order:
    order = Order.objects.select_for_update().get(pk=order_id)
    order.mark_confirmed()
    order.save(update_fields=["status", "updated_at"])

    process_order_task.delay_on_commit(order.pk, job_id=str(order.public_id))
    return order
```

For older Celery versions or custom dispatch paths, use Django's
`transaction.on_commit()`:

```python
from functools import partial

from django.db import transaction

transaction.on_commit(
    partial(process_order_task.delay, order.pk, job_id=str(order.public_id))
)
```

`delay_on_commit()` does not return a task id immediately because the message is
not sent until the transaction commits. Use plain `.delay()` only when the task
does not depend on uncommitted database state and the caller really needs the
task id immediately.

## ORM and Connection Hygiene

- Pass primary keys or stable IDs to tasks, then re-fetch current rows inside
  the service/task execution path.
- Avoid long `transaction.atomic()` blocks inside workers. Django transactions
  in long-running processes can hold database resources longer than expected.
- Django database connections created outside the request/response cycle can
  stay open until explicitly closed or timed out. Use
  `django.db.close_old_connections()` around custom long-running loops, custom
  threads, or task bases that manage ORM-heavy work.
- With Django 5.1+ database connection pooling, Celery's Django integration
  handles pool closing in worker processes. Do not share pool connections across
  forked worker processes.

If a project uses a custom Celery task base, inherit from `DjangoTask` so
`delay_on_commit()` and `apply_async_on_commit()` remain available:

```python
from celery.contrib.django.task import DjangoTask
from django.db import close_old_connections


class DatabaseHygieneTask(DjangoTask):
    abstract = True

    def before_start(self, task_id: str, args: tuple, kwargs: dict) -> None:
        close_old_connections()

    def after_return(self, status, retval, task_id, args, kwargs, einfo) -> None:
        close_old_connections()
```

Register the custom base in the Celery app only when the project needs it.

## Results and Beat Extensions

- Use `django-celery-results` only when task state/results must live in the
  Django database or cache. For fire-and-forget tasks, prefer ignoring results.
- Use `django-celery-beat` when product/admin users need to manage schedules in
  the Django admin or database.
- Run only one Beat scheduler for a schedule. Duplicate Beat instances can
  enqueue duplicate periodic work.
- If Django `TIME_ZONE` changes, review database-backed periodic schedules
  because existing schedules may keep the old timezone state.

## Testing

Test service logic without Celery first. For transaction-safe enqueueing, assert
that an on-commit callback is registered.

```python
from django.db import transaction
from django.test import TestCase

from orders.models import Order
from orders.tasks import process_order_task


class ConfirmOrderTests(TestCase):
    def test_task_is_registered_after_commit(self) -> None:
        order = Order.objects.create(status="draft")

        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            with transaction.atomic():
                process_order_task.delay_on_commit(order.pk, job_id=str(order.pk))

        assert len(callbacks) == 1
```

Use `TransactionTestCase` or pytest-django transaction tests when a worker or
another connection must observe committed rows. Keep eager mode as a narrow
emulation only; it does not exercise worker processes, broker delivery, or
transaction visibility.

## Checklist

- `project/celery.py` sets `DJANGO_SETTINGS_MODULE` before creating the app.
- Celery loads Django settings with `namespace="CELERY"`.
- `project/__init__.py` imports `celery_app`.
- Reusable app tasks use `@shared_task` in `tasks.py`.
- Producers enqueue DB-dependent tasks with `delay_on_commit()` or
  `transaction.on_commit()`.
- Tasks pass primary keys or stable IDs, not model instances.
- Custom task bases inherit from `DjangoTask`.
- ORM-heavy long-running work handles stale connections deliberately.
- Results and Beat Django extensions are added only when their database/admin
  behavior is needed.
