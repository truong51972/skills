# pyproject.toml Patterns

Copyable templates for the three app packaging styles and the shared package style.

## Table of Contents

- [Independent App with Local Package](#independent-app-with-local-package)
- [Packaged App](#packaged-app)
- [Root Workspace App](#root-workspace-app)
- [Shared Package](#shared-package)
- [Naming Conventions](#naming-conventions)

---

## Independent App with Local Package

Use when the app should be easy to move to its own repo later. The app is **not** installed as a wheel (`package = false`); source is run directly from the working directory.

```toml
[project]
name = "my-worker"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "celery>=5.0",
    "my-shared-lib",        # local package — distribution name, not import name
    "pydantic-settings>=2.0",
    "redis>=5.0",
]

[dependency-groups]
dev = [
    "ruff>=0.1",
]
# Example optional group for heavy extras
heavy = [
    "some-ml-library>=1.0",
]

[tool.uv]
package = false             # app is NOT installed as a wheel

[tool.uv.sources]
my-shared-lib = { path = "../../packages/my-shared-lib" }
```

Key points:

- `[project].dependencies` must include the distribution name (hyphenated).
- `tool.uv.sources` tells uv where to find the local package during dev and Docker builds.
- `package = false` means the app runs from wherever its source is copied; use flat imports and a flat Celery `-A` target (e.g. `-A main`).
- Keep an app-local `uv.lock` and regenerate it from the app directory.

---

## Packaged App

Use when the app should be installed as a wheel inside the image. Enables fully qualified module imports and package-qualified Celery targets.

```toml
[project]
name = "my-worker"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "celery>=5.0",
    "my-shared-lib",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/my_worker"]

[tool.uv.sources]
my-shared-lib = { path = "../../packages/my-shared-lib" }
```

Key points:

- Presence of `[build-system]` means `uv sync` will also install the app itself.
- Source lives under `src/my_worker/`; imports are `from my_worker.x import y`.
- Celery target: `celery -A my_worker.main worker`.
- If using `--no-install-project` in the Dockerfile build stage, copy `src/my_worker` explicitly into the runtime image.

---

## Root Workspace App

**Only use this when a root `pyproject.toml` and root `uv.lock` actually exist in the repository.**

```toml
[project]
name = "my-worker"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "celery>=5.0",
    "my-shared-lib",
]

[tool.uv.sources]
my-shared-lib = { workspace = true }   # resolved via root workspace manifest
```

Expected root `pyproject.toml` shape:

```toml
[tool.uv.workspace]
members = [
    "apps/my-worker",
    "packages/my-shared-lib",
]
```

Do **not** add `workspace = true` sources in a repo where the root workspace manifest is absent.

---

## Shared Package

Use for reusable code that multiple apps consume. Always uses a real build backend so it can be installed as a wheel.

```toml
[project]
name = "my-shared-lib"
version = "0.1.0"
description = "Shared models and utilities"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/my_shared_lib"]
```

Directory layout:

```
packages/my-shared-lib/
  pyproject.toml
  src/
    my_shared_lib/
      __init__.py
      ...
  tests/
```

---

## Naming Conventions

| Kind | Convention | Example |
|---|---|---|
| Distribution name (PyPI / dep list) | kebab-case | `my-shared-lib` |
| Import package name (directory) | snake_case | `my_shared_lib` |
| uv source key | matches distribution name | `my-shared-lib = { path = "..." }` |
