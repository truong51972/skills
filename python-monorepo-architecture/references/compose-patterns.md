# Docker Compose Patterns

Patterns for Compose service definitions inside a monorepo where fragments live under `infra/compose/` and the repo root is `../../`.

## Table of Contents

- [Service Fragment Template](#service-fragment-template)
- [Context and Build Rules](#context-and-build-rules)
- [Working Directory Alignment](#working-directory-alignment)
- [Docker Ignore at Root Context](#docker-ignore-at-root-context)
- [Useful Root .dockerignore Entries](#useful-root-dockerignore-entries)

---

## Service Fragment Template

Fragments live at `infra/compose/<fragment>.yaml`. Paths are relative to that directory.

```yaml
services:
  my-worker:
    container_name: <project>-my-worker
    build:
      context: ../../          # repo root — must include every path the Dockerfile COPYs
      dockerfile: apps/my-worker/dockerfile
    working_dir: /app          # must match Dockerfile WORKDIR
    restart: unless-stopped
    profiles:
      - workers
    environment:
      - REDIS_HOST=${REDIS_HOST}
      - REDIS_PORT=${REDIS_PORT}
      - REDIS_PASSWORD=${REDIS_PASSWORD}

networks:
  default:
    name: <project>-network
    external: true
```

Replace `<project>` with your project identifier. Remove unused environment variables.

---

## Context and Build Rules

The `build.context` must be broad enough to include **every path that the Dockerfile COPYs**.

| Dockerfile COPY | Required context |
|---|---|
| `COPY packages /packages` | repo root (`../../`) |
| `COPY apps/my-worker/src /app` | repo root (`../../`) |
| Only local app files | app directory (`../../apps/my-worker`) |

When context is repo root and the fragment is at `infra/compose/`, use `../../`:

```yaml
build:
  context: ../../
  dockerfile: apps/my-worker/dockerfile
```

When the app has no local package dependency and can be built from its own directory:

```yaml
build:
  context: ../../apps/my-worker
  dockerfile: dockerfile
```

---

## Working Directory Alignment

Compose `working_dir` overrides the Dockerfile `WORKDIR` at runtime. Always set them to the same value to avoid import path surprises.

```
Dockerfile:  WORKDIR /app
Compose:     working_dir: /app   ← must match
```

If a dev volume mounts source over the same path, make sure it does not shadow installed package files from the venv.

---

## Docker Ignore at Root Context

When `context: ../../` is used, Docker looks for an ignore file at the repo root, not next to the Dockerfile. App-local `.dockerignore` files are **not** applied.

Options:

1. **Root `.dockerignore`** — simplest, applies to all root-context builds.
2. **Dockerfile-specific ignore file** — `apps/my-worker/dockerfile.dockerignore` (Docker BuildKit ≥ 0.6).

---

## Useful Root .dockerignore Entries

```dockerignore
.git
**/.venv
**/__pycache__
**/*.pyc
**/.pytest_cache
**/tmp
**/temp
**/node_modules
**/dist
**/.mypy_cache
**/.ruff_cache
```

Adjust glob patterns to match your project's frontend or other build artifacts.
