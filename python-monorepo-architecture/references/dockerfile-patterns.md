# Dockerfile Patterns

Multi-stage Dockerfile patterns for Python apps managed with `uv` in a monorepo.

## Table of Contents

- [Parameterized App (ARG APP_NAME)](#parameterized-app-arg-app_name)
- [Packaged App (installed as wheel)](#packaged-app-installed-as-wheel)
- [Optional Dependency Groups](#optional-dependency-groups)
- [Path Resolution Rules](#path-resolution-rules)
- [Security and Layer Ordering](#security-and-layer-ordering)

---

## Parameterized App (ARG APP_NAME)

Use this as the default pattern for an app under `apps/<app-name>` with shared local packages under `packages/`.
It keeps dependency installation cacheable by copying only package metadata before `uv sync`, then copying app
source only into the runtime image.

```dockerfile
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /build
ARG APP_NAME=example-app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PROJECT_ENVIRONMENT="/opt/venv"
ENV VIRTUAL_ENV="/opt/venv"

RUN uv venv /opt/venv
# packages
COPY packages/<package-a> /packages/<package-a>
COPY packages/<package-b> /packages/<package-b>

# app
COPY apps/${APP_NAME}/pyproject.toml /build/${APP_NAME}/pyproject.toml
COPY apps/${APP_NAME}/uv.lock /build/${APP_NAME}/uv.lock

RUN --mount=type=cache,target=/root/.cache/uv \
    cd ${APP_NAME} && \
    uv sync --locked --no-dev --no-install-project --no-editable


FROM python:3.12-slim AS runtime

RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
ARG APP_NAME=example-app

COPY --chown=nonroot:nonroot apps/${APP_NAME}/src /app

EXPOSE 8000

USER nonroot

CMD ["python", "-m", "main"]
```

Use Compose or `docker build` to override the app when needed:

```yaml
build:
  context: .
  dockerfile: dockerfile
  args:
    APP_NAME: example-app
```

Keep these details intact unless the app layout differs:

- Set `WORKDIR /build` in the builder and copy app metadata to `/build/${APP_NAME}`.
- Copy `packages` to `/packages` before `uv sync` so `tool.uv.sources` paths like `../../packages/foo` resolve.
- Run `uv sync` from inside `${APP_NAME}` because that directory contains the copied `pyproject.toml` and `uv.lock`.
- Use `--no-install-project` for flat apps where source is copied to `/app` and run directly.
- Use `--no-editable` with local path dependencies so the runtime venv does not depend on editable source paths.
- Repeat `ARG APP_NAME` in the runtime stage before using it in `COPY`; Docker build args are scoped per stage.

> `EXPOSE`, runtime environment variables, and the Python module in `CMD` are app-specific. Replace them for the service being packaged.

---

## Packaged App (installed as wheel)

Use when `pyproject.toml` has a `[build-system]` block and the app should be installed into the virtualenv.
Remove `--no-install-project`, copy the app source before `uv sync`, and run the installed module in runtime.

```dockerfile
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /build
ARG APP_NAME=example-app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PROJECT_ENVIRONMENT="/opt/venv"
ENV VIRTUAL_ENV="/opt/venv"

RUN uv venv /opt/venv

COPY packages /packages
COPY apps/${APP_NAME}/pyproject.toml /build/${APP_NAME}/pyproject.toml
COPY apps/${APP_NAME}/uv.lock /build/${APP_NAME}/uv.lock
COPY apps/${APP_NAME}/src /build/${APP_NAME}/src

RUN --mount=type=cache,target=/root/.cache/uv \
    cd ${APP_NAME} && \
    uv sync --locked --no-dev --no-editable


FROM python:3.12-slim AS runtime

RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
USER nonroot

CMD ["python", "-m", "example_app"]
```

Packaged apps usually do not need `COPY apps/${APP_NAME}/src /app` in runtime because the project is installed into `/opt/venv`.

---

## Optional Dependency Groups

To install a `[dependency-groups]` group such as `heavy`:

```dockerfile
RUN --mount=type=cache,target=/root/.cache/uv \
    cd ${APP_NAME} && \
    uv sync --group heavy --locked --no-dev --no-install-project --no-editable
```

---

## Path Resolution Rules

When the copied app metadata lives at `/build/${APP_NAME}/pyproject.toml` and `tool.uv.sources` declares:

```toml
example-package = { path = "../../packages/example-package" }
```

uv resolves the relative path from `/build/${APP_NAME}`, so the package must exist at
`/packages/example-package` inside the build container. That is why `COPY packages /packages` must come
before `uv sync`.

Adjust the `COPY` destination if your `WORKDIR` or relative path differs:

| Builder location of `pyproject.toml` | `tool.uv.sources` path | Required copy destination |
|---|---|---|
| `/build/example-app/pyproject.toml` | `../../packages/foo` | `/packages/foo` |
| `/app/pyproject.toml` | `../../packages/foo` | `/packages/foo` |
| `/srv/app/pyproject.toml` | `../packages/foo` | `/srv/packages/foo` |

---

## Security and Layer Ordering

- Run as a non-root user in runtime images.
- Keep dependency installation (`uv sync`) in a separate layer from app source so Docker cache is reused when only source changes.
- Order for flat apps: `uv venv` -> copy packages -> copy `pyproject.toml` + `uv.lock` -> `uv sync` -> copy app source in runtime.
- Do not include `uv` in the runtime image unless explicitly needed.
- Add only runtime environment variables that the app needs; keep secrets out of the Dockerfile.
