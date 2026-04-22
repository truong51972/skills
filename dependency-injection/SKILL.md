---
name: dependency-injection
description: >
    Build and refactor scalable Dependency Injection with `dependency-injector` in Python.
    Use for container design, provider scope selection, FastAPI/Celery wiring, async resource
    lifecycle, and test overrides.
---

## Skill: Dependency Injection Hub

This is one main skill centered on core DI architecture.
Use-case sections (FastAPI, Celery, Testing) are extension examples around the same core.

## When To Use

- Build or refactor a DI container with `dependency-injector`
- Wire runtime entry points for FastAPI or Celery
- Choose provider scopes (`Singleton`, `Factory`, `Resource`)
- Write tests with provider/container overrides

## Example Tracks

1. Core architecture and provider patterns:
[references/core.md](dependency-injection/references/core.md)
2. FastAPI async runtime wiring:
[references/fastapi.md](dependency-injection/references/fastapi.md)
3. Celery worker runtime wiring:
[references/celery.md](dependency-injection/references/celery.md)
4. Testing and override strategy:
[references/testing.md](dependency-injection/references/testing.md)

## Use-case Routing

1. If request includes FastAPI, lifespan, async resources, or `Depends(Provide[...])`, load [references/fastapi.md](dependency-injection/references/fastapi.md).
2. If request includes Celery worker lifecycle, signals, or task entry points, load [references/celery.md](dependency-injection/references/celery.md).
3. If request includes mocks, fakes, fixtures, or state leakage between tests, load [references/testing.md](dependency-injection/references/testing.md).
4. Always load [references/core.md](dependency-injection/references/core.md) for baseline architecture.

## Completion Checklist

1. Services do not read `os.environ` directly; settings are injected.
2. Infrastructure clients use `providers.Resource` with explicit lifecycle.
3. Entry points resolve providers; services receive explicit constructor dependencies.
4. Async runtime awaits `init_resources()` and `shutdown_resources()`.
5. Tests reset overrides with `reset_override()`.

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Using `reset_overrides()` | Use `reset_override()` |
| Overriding with `lambda: Fake()` and expecting instance injection | Override with provider or fake instance directly |
| Mixing async runtime with `Provide[Container...]` from a different container class | Use matching container class or string IDs |
| Heavy IO in service `__init__` | Move lifecycle work to `providers.Resource` |