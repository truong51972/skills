---
name: dependency-injection
description: Design Python dependency injection across FastAPI, Celery, CLI, resources, and tests.
---

# Dependency Injection Hub

Use this skill for hybrid Python DI: framework-native dependencies at runtime
edges, and `dependency-injector` for explicit application composition, shared
object graphs, worker/CLI reuse, and resource lifecycle.

## Ownership Boundary

This skill owns container design, provider scope, resource lifecycle,
FastAPI/Celery/CLI integration, and test overrides.

Use a focused pointer instead of duplicating another skill:

- For Celery reliability, routing, retries, and Beat behavior, use
  `celery-worker`.
- For Docker, Compose, uv, package layout, or import paths, use
  `python-monorepo-architecture`.
- For durable `.agents/contexts/` memory, use `context-management`.

Assume Python 3.10+, Pydantic v2, FastAPI lifespan, `dependency-injector` 4.x,
and Celery 5.x unless the repo proves otherwise.

## Reference Routing

Always load [references/core.md](references/core.md) first.

Load additional references only when relevant:

| Task | Reference |
|---|---|
| FastAPI, ASGI, lifespan, `Depends`, app state, or `Provide[...]` | [fastapi.md](references/fastapi.md) |
| Celery lifecycle, signals, task entry points, or fork safety | [celery.md](references/celery.md) |
| Provider overrides, FastAPI overrides, fixtures, fakes, mocks, or test leakage | [testing.md](references/testing.md) |

## Provider Decision Matrix

| Need | Provider or pattern |
|---|---|
| Config/settings | `providers.Configuration` or validated Pydantic settings provider |
| Stateless service | `providers.Factory` |
| Safe shared pure object | `providers.Singleton` |
| DB engine/client/pool | `providers.Resource` |
| Runtime-supplied object | `providers.Dependency` |
| Request-scoped web dependency | FastAPI `Depends` / `yield` dependency |
| Test fake | Provider override or FastAPI dependency override |

Prefer `Factory` until there is a clear reason to share an instance. Avoid
`Singleton` for mutable request state, database sessions, event-loop-bound async
clients, and anything that needs teardown.

## Boundary Rules

- Resolve providers only at runtime boundaries: API route, task entry point,
  CLI command, scheduler startup, consumer startup, or test fixture.
- Business services must not import the container.
- Business services must not call `Provide[...]`.
- Business services must not read environment variables directly.
- Constructor injection is the default inside application code.
- The container composes objects; it must not become a service locator.

## FastAPI Integration Decision

- Prefer `create_app()` + lifespan + `app.state.container` as the default.
- Use FastAPI `Depends` for request-scoped state, auth, DB sessions, and cleanup.
- Use `Provide[...]` only when the project already uses wiring heavily or
  clearly benefits from provider markers across many functions.
- Do not mix multiple container instances accidentally. The running app's
  container instance must be the one that resolves dependencies.

## Celery Integration Decision

- For prefork workers, create fork-unsafe resources in child processes.
- Do not initialize DB pools, Redis clients, HTTP clients, event loops, GPU
  handles, or model handles before fork.
- Resolve the task service at the task entry point or through worker bootstrap,
  then keep business logic framework-free.
- If task reliability, routing, or acknowledgement behavior is the main
  problem, defer to `celery-worker`.

## Django And DRF Note

- Do not force external DI into normal Django request/ORM paths unless there is
  clear cross-runtime reuse.
- Django settings, app registry, middleware, and ORM already provide substantial
  framework composition.
- Use explicit service classes when the same logic is reused by DRF views,
  Celery workers, CLIs, or scheduled jobs.
- Avoid global container access inside models, serializers, and business
  services.

## Test Override Recipes

Provider override with cleanup:

```python
with container.user_service.override(providers.Object(fake_user_service)):
    result = handler()
```

FastAPI override with cleanup:

```python
app.dependency_overrides[get_session] = lambda: fake_session
try:
    ...
finally:
    app.dependency_overrides.clear()
```

Reset provider overrides after tests:

```python
container.reset_override()
container.unwire()
```

Avoid shared singleton leakage by creating a fresh container per test or by
resetting singletons that hold mutable state.

## Symptom To Fix

| Symptom | Likely cause | Fix |
|---|---|---|
| Service imports `Container` or calls `Provide[...]` | Container is being used as a service locator | Resolve at entry point and pass constructor dependencies |
| FastAPI override does not affect route | Route resolves a different container instance | Use `app.state.container` or wire the running instance |
| Async client fails across requests/tests | Event-loop-bound object was shared as a singleton | Use lifespan or `providers.Resource` in the active event loop |
| Celery worker crashes after prefork | Fork-unsafe resource created in parent process | Initialize resource in child process or lazily after fork |
| Tests leak fakes into later tests | Overrides or singletons were not reset | Use context managers and fixture cleanup |

## Completion Checklist

1. Settings are validated once with Pydantic and injected through providers.
2. Services receive explicit constructor dependencies; only runtime entry points
   resolve providers.
3. `Factory` is the default for application services; `Singleton` is used only
   for safe shared objects.
4. Infrastructure clients, pools, engines, and long-lived handles use
   `providers.Resource`.
5. Async runtimes await `init_resources()` and `shutdown_resources()`.
6. FastAPI request-scoped cleanup uses native `yield` dependencies.
7. Celery resources are created inside the worker child process, not before fork.
8. Tests isolate provider and FastAPI overrides with context managers or
   explicit cleanup.
9. Run focused unit tests for services and integration tests for runtime
   boundaries touched by the change.
