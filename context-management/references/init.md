# Init Workflow

Use this workflow when the user asks to create a fresh context system for a repo.

## Goal

Create `.agents/contexts/` with minimal generic starter files. Do not infer a full project baseline unless the user provides it in the request or asks you to inspect source files.

## Steps

1. Locate the repo root from the current working directory unless the user provides a path.
2. Run the helper script:

   ```bash
   python3 /path/to/context-management/scripts/context_ops.py init <repo-path>
   ```

3. If the user provided project details, place them in the correct shard as current-state baseline.
4. If `.agents/context.md` exists, mention that legacy context was found, but do not migrate it unless explicitly requested.
5. Keep generated files minimal and generic. Do not create `AGENTS.md`.

## Starter File Intent

- `index.md`: map available shards, explain loading policy, and keep the entrypoint compact.
- `source-priority.md`: list recommended startup, source roles, source priority, and conflict rules once known.
- `project-baseline.md`: store durable purpose, audience, domain, system/content shape, scope, and success criteria once known.
- `working-conventions.md`: store stable domain conventions, style rules, quality guardrails, and validation commands.
- `active-assumptions.md`: store assumptions, constraints, defaults, and operating limits that future sessions must preserve.

## Placement Guide

- Put source ownership, document roles, config/schema authority, and read conditions in `source-priority.md`.
- Put project identity, architecture/content shape, scope boundaries, and durable narrative in `project-baseline.md`.
- Put writing style, coding style, review rules, testing commands, diagram rules, and quality checks in `working-conventions.md`.
- Put live constraints, accepted defaults, and future-affecting assumptions in `active-assumptions.md`.
- Put only the shard map and startup route in `index.md`.

## Adaptation Examples

- For a code repo, source roles may include package manifests, framework configs, entrypoints, schemas, migrations, tests, API specs, and deployment files.
- For a document repo, source roles may include final artifacts, drafts, reference docs, prompt helpers, checklists, and generated outputs.
- For a mixed repo, keep context organized by ownership and read conditions rather than file type alone.

## Avoid

- Do not auto-migrate legacy `.agents/context.md`.
- Do not invent project-specific shards before the repo needs them.
- Do not fill context files with placeholder prose that future sessions must clean up.
