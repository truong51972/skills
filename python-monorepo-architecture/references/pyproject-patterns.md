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
name = "example-app"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "example-package",      # local package - distribution name, not import name
    "pydantic-settings>=2.0",
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
example-package = { path = "../../packages/example-package" }
```

Key points:

- `[project].dependencies` must include the distribution name (hyphenated).
- `tool.uv.sources` tells uv where to find the local package during dev and Docker builds.
- `package = false` means the app runs from wherever its source is copied; use flat imports and a direct Python module entrypoint such as `python -m main`.
- Keep an app-local `uv.lock` and regenerate it from the app directory.

---

## Packaged App

Use when the app should be installed as a wheel inside the image. Enables fully qualified module imports and package-qualified Python entrypoints.

```toml
[project]
name = "example-app"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "example-package",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/example_app"]

[tool.uv.sources]
example-package = { path = "../../packages/example-package" }
```

Key points:

- Presence of `[build-system]` means `uv sync` will also install the app itself.
- Source lives under `src/example_app/`; imports are `from example_app.x import y`.
- Runtime entrypoint can use `python -m example_app`.
- If using `--no-install-project` in the Dockerfile build stage, copy `src/example_app` explicitly into the runtime image.

---

## Root Workspace App

**Only use this when a root `pyproject.toml` and root `uv.lock` actually exist in the repository.**

```toml
[project]
name = "example-app"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "example-package",
]

[tool.uv.sources]
example-package = { workspace = true }   # resolved via root workspace manifest
```

Expected root `pyproject.toml` shape:

```toml
[tool.uv.workspace]
members = [
    "apps/example-app",
    "packages/example-package",
]
```

Do **not** add `workspace = true` sources in a repo where the root workspace manifest is absent.

---

## Shared Package

Use for reusable code that multiple apps consume. Always uses a real build backend so it can be installed as a wheel.

```toml
[project]
name = "example-package"
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
packages = ["src/example_package"]
```

Directory layout:

```
packages/example-package/
  pyproject.toml
  src/
    example_package/
      __init__.py
      ...
  tests/
```

---

## Naming Conventions

| Kind | Convention | Example |
|---|---|---|
| Distribution name (PyPI / dep list) | kebab-case | `example-package` |
| Import package name (directory) | snake_case | `example_package` |
| uv source key | matches distribution name | `example-package = { path = "..." }` |
