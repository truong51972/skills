---
name: python-monorepo-architecture
description: >
  Use when working on a Python monorepo that follows an apps/packages/infra layout. Triggers include adding or reviewing apps, shared packages, Dockerfiles, Docker Compose, uv dependencies, Celery workers, or build-context issues.
---

# Python Monorepo Architecture

A skill for maintaining clean boundaries between apps, shared packages, and infrastructure inside a Python monorepo that uses `uv` for dependency management and Docker / Docker Compose for deployment.

## Start Here

Before making any change, read the files that own the area you are touching:

- `compose.yaml` — root include file
- The relevant `infra/compose/*.yaml` fragment
- The app `pyproject.toml` and `uv.lock`
- The app Dockerfile
- Any `packages/*/pyproject.toml` consumed by the app

Then decide which reference to load:

| Task | Reference |
|---|---|
| Writing or reviewing `pyproject.toml` | [pyproject-patterns.md](references/pyproject-patterns.md) |
| Writing or reviewing a Dockerfile | [dockerfile-patterns.md](references/dockerfile-patterns.md) |
| Writing or reviewing a Compose service | [compose-patterns.md](references/compose-patterns.md) |
| Adding a shared package or splitting a repo | [package-management.md](references/package-management.md) |

## Repo Shape Convention

```
apps/<app>/          # Deployable applications
packages/<package>/  # Reusable Python packages (src layout)
infra/compose/       # Compose fragments grouped by runtime concern
compose.yaml         # Root include file
```

Key ownership rules:

- Each Python app owns its own `pyproject.toml`.
- Independent apps own their own `uv.lock`; do not share a root lockfile unless a root `pyproject.toml` and root `uv.lock` actually exist.
- Compose fragments in `infra/compose/` use paths relative to that directory; `../../` resolves to repo root.
- Shared packages live under `packages/` with a proper build backend and `src/<import_name>` layout.

## Decision Rules

**Packaging style** — pick one before writing any file:

- *Independent app* — app-local `pyproject.toml` + `uv.lock`, `tool.uv.sources` with relative paths. Easy to split into its own repo later.
- *Packaged app* — adds a `[build-system]` block; app is installed as a wheel. Use package-qualified imports and Celery targets.
- *Root workspace app* — use `workspace = true` in `tool.uv.sources` **only** when a root `pyproject.toml` and root `uv.lock` actually exist.

**Consistency rules** — all of these must agree with each other:

| Concern | Must match |
|---|---|
| `WORKDIR` in Dockerfile | `working_dir` in Compose service |
| Dockerfile `COPY` sources | Compose `build.context` (must include every copied path) |
| `tool.uv.package = false` (flat app) | Flat imports, flat Celery `-A` target |
| Packaged app (`[build-system]` present) | `src/<module>` imports, package-qualified Celery target |
| `--no-install-project` used | App source copied to a runtime-importable path |

**Local packages** — always declare them as real entries in `[project].dependencies` and resolve them via `[tool.uv.sources]`. Never rely on ad-hoc `PYTHONPATH` edits or `sys.path` manipulation.

**Docker ignore** — with `build.context: ../../` (repo root), app-local `.dockerignore` files are ignored by Docker. Use a root `.dockerignore` or a Dockerfile-specific ignore file.

## Workflows

### Add a Shared Package

1. Create `packages/<name>/pyproject.toml` with a real build backend and `src/<import_name>` target.
2. Add the distribution name to the consuming app's `[project].dependencies`.
3. Add a `[tool.uv.sources]` entry pointing at the package path.
4. Re-run `uv lock` and `uv sync --locked` from the app directory.
5. Update the Dockerfile to copy the package directory before `uv sync`.

See [package-management.md](references/package-management.md) for copyable examples.

### Add or Review an App

1. Choose packaging style (independent / packaged / workspace).
2. Write `pyproject.toml` to match.
3. Write the Dockerfile — install dependencies before copying app source.
4. Add a Compose service in the relevant `infra/compose/*.yaml`.
5. Verify `uv sync --locked`, import smoke test, `docker compose config`, and a targeted image build.

See [pyproject-patterns.md](references/pyproject-patterns.md), [dockerfile-patterns.md](references/dockerfile-patterns.md), and [compose-patterns.md](references/compose-patterns.md).

### Split an App into an Independent Repo

See [package-management.md](references/package-management.md) for the full checklist and path-rewrite examples.

## Quick Review Checklist

- [ ] Root workspace files exist before using `workspace = true` or `uv sync --package`
- [ ] App has `uv.lock` if Dockerfile copies it
- [ ] `[project].dependencies` includes local package names; `[tool.uv.sources]` resolves them
- [ ] Compose context includes every path that Dockerfile `COPY`s
- [ ] Ignore file applies at the actual build context root
- [ ] `pyproject.toml` + `uv.lock` + local packages copied before app source (cache layer ordering)
- [ ] Compose `working_dir` matches Dockerfile `WORKDIR`
- [ ] Flat vs package import style is consistent throughout
- [ ] Celery `-A` target, `celeryconfig` imports, and task module paths all agree
- [ ] If `--no-install-project`, app source is on a runtime-importable path
- [ ] Dev volume mounts do not shadow installed package files
