# Dockerfile Patterns

Multi-stage Dockerfile patterns for Python apps managed with `uv`.

## Table of Contents

- [Independent App (flat, no-install-project)](#independent-app-flat-no-install-project)
- [Packaged App (installed as wheel)](#packaged-app-installed-as-wheel)
- [Optional Dependency Groups](#optional-dependency-groups)
- [Path Resolution Rules](#path-resolution-rules)
- [Security and Layer Ordering](#security-and-layer-ordering)

---

## Independent App (flat, no-install-project)

Use when `pyproject.toml` has `tool.uv.package = false`. Source is copied to `WORKDIR` and run directly.

```dockerfile
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PROJECT_ENVIRONMENT="/opt/venv"
ENV VIRTUAL_ENV="/opt/venv"

RUN uv venv /opt/venv

# Copy local packages BEFORE uv sync so the relative path resolves correctly.
# Adjust source path to match your repo layout.
COPY packages /packages

COPY apps/my-worker/pyproject.toml /app/pyproject.toml
COPY apps/my-worker/uv.lock        /app/uv.lock

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

# ── Runtime image ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS production

RUN groupadd --system --gid 999 nonroot \
    && useradd  --system --gid 999 --uid 999 --create-home nonroot

ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=nonroot:nonroot apps/my-worker/src /app

USER nonroot

CMD ["celery", "-A", "main", "worker", "--loglevel=info"]
```

> **`WORKDIR` note** — The value here (`/app`) must match the Compose service `working_dir`. Pick one value and use it consistently.

---

## Packaged App (installed as wheel)

Use when `pyproject.toml` has a `[build-system]` block. Remove `--no-install-project` so `uv sync` also installs the app.

```dockerfile
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PROJECT_ENVIRONMENT="/opt/venv"
ENV VIRTUAL_ENV="/opt/venv"

RUN uv venv /opt/venv

COPY packages /packages

COPY apps/my-worker/pyproject.toml /app/pyproject.toml
COPY apps/my-worker/uv.lock        /app/uv.lock
# Copy src so uv can install the app itself
COPY apps/my-worker/src            /app/src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev        # no --no-install-project

# ── Runtime image ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS production

RUN groupadd --system --gid 999 nonroot \
    && useradd  --system --gid 999 --uid 999 --create-home nonroot

ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
USER nonroot

# App is installed into /opt/venv; no source copy needed.
CMD ["celery", "-A", "my_worker.main", "worker", "--loglevel=info"]
```

---

## Optional Dependency Groups

To install a `[dependency-groups]` extras group (e.g. `[dependency-groups] heavy = [...]`):

```dockerfile
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --group heavy --locked --no-dev --no-install-project
```

---

## Path Resolution Rules

When `WORKDIR` is `/app` and `tool.uv.sources` declares:

```toml
my-shared-lib = { path = "../../packages/my-shared-lib" }
```

uv resolves that relative to `pyproject.toml`, so the package must exist at `/packages/my-shared-lib` inside the build container. That is why `COPY packages /packages` must come **before** `uv sync`.

Adjust the `COPY` destination if your `WORKDIR` or relative path differs:

| `WORKDIR` | `tool.uv.sources` path | Required copy destination |
|---|---|---|
| `/app` | `../../packages/foo` | `/packages/foo` |
| `/user/app` | `../../packages/foo` | `/packages/foo` |
| `/srv/app` | `../packages/foo` | `/srv/packages/foo` |

---

## Security and Layer Ordering

- Run as a non-root user in production images.
- Keep dependency installation (`uv sync`) in a separate layer from app source so Docker cache is reused when only source changes.
- Order: `uv venv` → copy packages → copy `pyproject.toml` + `uv.lock` → `uv sync` → copy app source.
- Do **not** include `uv` in the production image unless explicitly needed.
