---
name: celery-worker
description: >
  Build, review, or refactor production Celery 5 worker systems. Use this for
  broker and queue configuration, task routing, retry and acknowledgement
  policy, idempotent task wrappers, worker lifecycle hooks, dependency injection
  resource management, Django integration, Celery Beat, and realistic Celery
  testing strategy.
---

# Celery Worker Architecture

Use this skill for Python 3.10+, Celery 5.6.x, Pydantic v2, and
`dependency-injector` 4.49.x worker projects.

## Decision Guide

- Keep Celery tasks as thin adapters: validate input, set task options, delegate
  to services, and return serializable results.
- Keep business logic in service modules that do not import Celery.
- Use explicit queues and routes for production workloads. Do not let task
  modules become the routing policy.
- Treat reliability as broker-aware: Redis, RabbitMQ, and SQS have different
  queue, priority, and visibility semantics.
- Use `dependency-injector` for worker process composition and resource
  lifecycle. Create fork-unsafe clients, sockets, pools, GPU handles, and event
  loop resources in child worker processes.
- Make late-acknowledged tasks idempotent before enabling redelivery behavior.
- Prefer service unit tests and Celery worker integration tests. Use eager mode
  only as a narrow emulation, not as the default proof of worker behavior.

## Reference Routing

Load only the references needed for the task:

- [configuration.md](references/configuration.md): Celery app factories,
  Pydantic settings, queues, routes, broker caveats, shutdown settings, and run
  commands.
- [lifecycle-di.md](references/lifecycle-di.md): `dependency-injector`
  containers, Celery worker signals, prefork safety, sync and async resource
  lifecycle.
- [tasks.md](references/tasks.md): thin task wrappers, Pydantic payloads,
  retries, acknowledgement policy, idempotency, Beat, and observability.
- [testing.md](references/testing.md): service tests, task wrapper tests,
  `celery.contrib.pytest`, `pytest-celery`, eager-mode caveats, and DI override
  cleanup.
- [django.md](references/django.md): Django project setup, `CELERY_` settings,
  `@shared_task`, transaction-safe enqueueing, ORM connection hygiene,
  `django-celery-results`, `django-celery-beat`, and Django-specific tests.

## Project Shape

Prefer one importable package under `src/` or `app/`:

```text
src/my_worker/
|-- main.py              # create_celery_app(), module-level app
|-- settings.py          # Pydantic v2 settings
|-- celery_config.py     # optional config constants/helpers
|-- bootstrap.py         # worker lifecycle and DI container access
|-- containers.py        # dependency-injector providers
|-- tasks/               # thin Celery adapters
|-- services/            # framework-free business logic
|-- schemas/             # Pydantic task payload/result contracts
`-- infrastructure/      # broker clients, repositories, external APIs
```

## Completion Checklist

- Settings are validated once with Pydantic and applied as lowercase Celery
  configuration.
- Celery app creation is centralized in `create_celery_app()`.
- Queues and routes are explicit for production workloads.
- Task payloads pass IDs and compact primitives, not large objects or ORM
  instances.
- Task wrappers validate input and call services without embedding business
  rules.
- Retry policy targets transient exceptions only and uses bounded backoff.
- Late acknowledgement is paired with idempotency and deduplication.
- Worker lifecycle hooks accept `**kwargs`; child-process initialization is
  fast; shutdown is treated as best-effort.
- Fork-unsafe resources are not created in the parent process.
- Tests cover service logic, task wrapper behavior, and at least one real worker
  integration path when reliability matters.
- Django producers enqueue side-effecting tasks after transaction commit.

## Common Pitfalls

| Pitfall | Better Pattern |
| --- | --- |
| Putting domain logic inside `@shared_task` functions | Keep tasks as adapters and call service methods |
| Enabling `acks_late` globally for non-idempotent tasks | Use per-task policy after dedupe/idempotency exists |
| Enabling `task_reject_on_worker_lost` casually | Use only when message loops and duplicate side effects are understood |
| Creating DB, HTTP, gRPC, Redis, or GPU clients before prefork | Initialize resources in `worker_process_init` or lazily in the child |
| Assuming `worker_process_shutdown` always runs | Make shutdown best-effort and design resources to tolerate abrupt exit |
| Using eager mode as the only test strategy | Mock task boundaries for unit tests and run worker-backed integration tests |
| Hard-coding queue names in service code | Keep routing in Celery config or publish-time options |
| Calling `.delay()` inside a Django transaction | Use `delay_on_commit()` or `transaction.on_commit()` |
