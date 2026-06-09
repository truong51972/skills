# Package Management

Workflows and checklists for adding shared packages and splitting apps out of the monorepo.

## Table of Contents

- [Adding a Shared Package](#adding-a-shared-package)
- [Splitting an App into an Independent Repo](#splitting-an-app-into-an-independent-repo)
- [Full Review Checklist](#full-review-checklist)

---

## Adding a Shared Package

### 1 — Create the package directory

```
packages/my-shared-lib/
  pyproject.toml
  src/
    my_shared_lib/
      __init__.py
  tests/
```

### 2 — Write the package `pyproject.toml`

```toml
[project]
name = "my-shared-lib"
version = "0.1.0"
description = "Shared utilities"
requires-python = ">=3.12"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/my_shared_lib"]
```

### 3 — Declare it in the consuming app

```toml
# apps/my-worker/pyproject.toml

[project]
dependencies = [
    "my-shared-lib",   # distribution name
]

[tool.uv.sources]
my-shared-lib = { path = "../../packages/my-shared-lib" }
```

### 4 — Update and verify the lockfile

Run from the **app** directory:

```bash
uv lock
uv sync --locked
uv run python -c "import my_shared_lib; print('ok')"
```

### 5 — Update the Dockerfile

Add a `COPY` step for the package **before** `uv sync`:

```dockerfile
COPY packages/my-shared-lib /packages/my-shared-lib
# or copy all packages at once:
COPY packages /packages
```

---

## Splitting an App into an Independent Repo

### Decide how shared packages are handled

| Option | When to use |
|---|---|
| Copy packages into new repo | Package is tightly coupled; no intention to publish |
| Publish package to an index | Multiple external consumers; clean versioning desired |
| Inline the code | Package is small and used only by this app |

### Copy packages into the new repo

New repo layout:

```
new-repo/
  apps/my-worker/         # or just the root if single-app
    pyproject.toml
    uv.lock
    src/
  packages/
    my-shared-lib/
```

Update `tool.uv.sources` to reflect the new relative path:

```toml
[tool.uv.sources]
my-shared-lib = { path = "../packages/my-shared-lib" }
```

Update Compose `build.context` to the new repo root (usually `.`):

```yaml
build:
  context: .
  dockerfile: apps/my-worker/dockerfile
```

Update Dockerfile `COPY` paths to match the new layout:

```dockerfile
COPY packages /packages
COPY apps/my-worker/pyproject.toml /app/pyproject.toml
COPY apps/my-worker/uv.lock        /app/uv.lock
```

### Publish the package to an index

Remove the path source entry; pin the version in `[project].dependencies`:

```toml
[project]
dependencies = [
    "my-shared-lib>=0.1.0",   # resolves from the configured index
]

# No [tool.uv.sources] entry for my-shared-lib.
```

### After any split

1. `uv sync --locked` from the app directory.
2. Import smoke test: `python -c "from my_worker import main"`.
3. `docker compose config` to validate the Compose fragment.
4. Targeted image build: `docker compose build my-worker`.

---

## Full Review Checklist

Use before merging Dockerfile, Compose, or `pyproject.toml` changes.

**uv and lockfile**
- [ ] Root workspace files (`pyproject.toml`, `uv.lock`) exist if `workspace = true` is used
- [ ] App has its own `uv.lock` if the Dockerfile copies it
- [ ] `uv sync --locked` passes without errors

**Dependencies**
- [ ] `[project].dependencies` lists every local package by its distribution name
- [ ] `[tool.uv.sources]` resolves each local package to a valid path

**Docker build**
- [ ] Compose `build.context` covers every path the Dockerfile `COPY`s
- [ ] Ignore file is at the build context root, not inside the app directory
- [ ] Dependency layer order: venv → local packages → lockfile → `uv sync` → app source

**Runtime**
- [ ] Compose `working_dir` matches Dockerfile `WORKDIR`
- [ ] Import style (flat vs. package) is consistent across all source files, config, and `CMD`
- [ ] Celery `-A` target, `celeryconfig` imports, and task module paths all agree
- [ ] If `--no-install-project` is used, app source is on a runtime-importable path
- [ ] Dev volume mounts do not shadow installed package files in `/opt/venv`
