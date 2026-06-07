---
name: dependency-injection
description: >
    Build, modernize, or refactor Python dependency injection with `dependency-injector`
    and framework-native DI. Use for container design, provider scope selection,
    Pydantic v2 settings injection, async `Resource` lifecycle, FastAPI `Depends`
    and lifespan composition, Celery worker lifecycle, and test overrides.
---

# Dependency Injection Hub

Use this skill for hybrid Python DI: native framework dependencies at runtime edges,
and `dependency-injector` for explicit application composition, shared object graphs,
worker/CLI reuse, and resource lifecycle.

Assume Python 3.10+, Pydantic v2, FastAPI lifespan, `dependency-injector` 4.x,
and Celery 5.x unless the repo proves otherwise.

## Decision Guide

- Use native FastAPI `Depends` and `yield` dependencies for request-scoped web
  dependencies such as sessions, authorization, request context, and per-request cleanup.
- Use `dependency-injector` for cross-runtime composition, complex provider graphs,
  explicit settings injection, resource initialization/shutdown, Celery workers, CLIs,
  scheduled jobs, and background consumers.
- In FastAPI, prefer `create_app()` + lifespan + `app.state.container` as the default
  integration. Use `Provide[...]` wiring only when the project already benefits from
  wiring or needs provider markers across many functions.
- Keep services framework-free: services receive constructor arguments and never reach
  into FastAPI, Celery, global containers, or environment variables.

## Reference Routing

Always load [references/core.md](references/core.md) first.

Load additional references only when relevant:

1. FastAPI, ASGI, lifespan, `Depends`, app state, or `Provide[...]`: [references/fastapi.md](references/fastapi.md)
2. Celery worker lifecycle, signals, task entry points, or fork safety: [references/celery.md](references/celery.md)
3. Provider overrides, FastAPI dependency overrides, fixtures, fakes, mocks, or test leakage: [references/testing.md](references/testing.md)

## Completion Checklist

1. Settings are validated once with Pydantic and injected through providers.
2. Services receive explicit constructor dependencies; only runtime entry points resolve providers.
3. `Factory` is the default for application services; `Singleton` is used only for safe shared objects.
4. Infrastructure clients, pools, engines, and long-lived handles use `providers.Resource`.
5. Async runtimes await `init_resources()` and `shutdown_resources()`.
6. FastAPI request-scoped cleanup uses native `yield` dependencies.
7. Celery resources are created inside the worker child process, not before fork.
8. Tests isolate provider and FastAPI overrides with context managers or explicit cleanup.

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Treating the container as a service locator inside business code | Resolve providers at API/task/CLI boundaries and pass dependencies into constructors |
| Creating clients or DB pools in service `__init__` | Put acquisition and teardown in `providers.Resource` or FastAPI `yield` dependencies |
| Sharing event-loop-bound async clients across ASGI lifespans | Create them in FastAPI lifespan and shut them down in the same lifespan |
| Using `Provide[...]` markers without wiring the exact modules/packages | Wire the running container instance or use `app.state.container` dependencies |
| Creating fork-unsafe clients before Celery prefork workers spawn | Initialize resources from `worker_process_init` in the child process |
| Leaving overrides active after a test | Use override context managers or call `reset_override()` in fixture cleanup |
