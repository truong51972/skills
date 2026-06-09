---
name: context-management
description: Manage durable repo context under .agents/contexts for Codex sessions.
---

# Context Management

Manage reusable project context stored under `.agents/contexts/`. This skill is
about context discipline, not domain content: keep startup memory compact,
source-grounded, and free of session changelog.

## Ownership Boundary

This skill owns `.agents/contexts/` only: startup memory, durable baseline,
source priority, conventions, assumptions, and update/clear workflows.

Use domain skills for domain facts. Context may point to source files, but it
must not copy source-of-truth detail from Python packages, Dockerfiles, Compose,
Celery configuration, DI containers, schemas, tests, or product documents.

## Workflow Router

Choose exactly one workflow from the user request:

- **init**: create a new `.agents/contexts/` structure. Read [init.md](references/init.md).
- **understand**: start a new session by loading context. Read [understand.md](references/understand.md).
- **update**: end a session by preserving only durable learnings. Read [update.md](references/update.md).
- **clear**: end a session by pruning context noise. Read [clear.md](references/clear.md).

If the user says `context-management init`, `context-management update`,
`context-management clear`, or `context-management understand`, follow the named
workflow. If the user asks generally to save, clean, compact, remember, or
prepare context for next time, use `update` or `clear` based on whether new
durable information should be added.

## Context Taxonomy

| Type | Store in context? | Example |
|---|---|---|
| Source of truth | No, reference source files instead | API schema, `pyproject.toml`, Dockerfile |
| Durable baseline | Yes | Current architecture, stable repo conventions |
| Active assumption | Yes, if still affects future work | "Workers are deployed separately from API" |
| Session note | No | "Today we changed X" |
| Completed task history | No | "Fixed Dockerfile bug" |
| Temporary TODO | No, unless user asks | "Try this later" |

## Non-Negotiable Rules

- Treat context as startup memory, not source of truth. Real source files win
  when they conflict with context.
- Do not use `AGENTS.md` as the main context mechanism.
- Do not auto-migrate legacy `.agents/context.md` during `init`; only use it if
  the user explicitly asks.
- Keep `.agents/contexts/index.md` compact so future sessions can decide what
  to load.
- Read `index.md` first and lazy-load only the shards needed for the current
  task.
- Do not read all context shards by default.
- Store current durable baseline, not revision history.
- Never store session summaries, completed task logs, edit history, temporary
  TODOs, or "what just happened" narration.
- Rewrite durable corrections as general rules instead of recording the
  correction.
- Split or add shards only when targeted loading becomes useful.

## Update Algorithm

For `context-management update`:

1. Read `.agents/contexts/index.md`.
2. Load only relevant shards.
3. Inspect actual source files related to the session.
4. Identify durable facts that are still true after the changes.
5. Rewrite context as current baseline, not history.
6. Remove dates, "we changed", "today", "previously", and completed-task
   narration.
7. Update `index.md` if shards are added or renamed.
8. Summarize which context areas were updated.

## Clear Algorithm

For `context-management clear`:

1. Scan context for changelog language.
2. Remove stale session history.
3. Merge duplicate rules.
4. Convert correction history into stable rules.
5. Keep current architecture and conventions.
6. Do not delete source-priority or active assumptions unless clearly stale.
7. Report removed noise categories, not every line.

## Conflict Handling Examples

- If context says the app uses Milvus but source now uses Qdrant, source wins.
- If context says root workspace but the repo has no root `pyproject.toml`,
  source wins.
- If context mentions a planned feature but no source confirms it, keep it only
  as an active assumption when it still affects future work.

## Expected Context Layout

Default project context files:

- `.agents/contexts/index.md`: compact entrypoint, shard map, loading policy,
  and startup route.
- `.agents/contexts/source-priority.md`: source-of-truth hierarchy,
  recommended startup, document/source roles, and conflict handling.
- `.agents/contexts/project-baseline.md`: durable current repo, product, domain,
  architecture, content, and scope baseline.
- `.agents/contexts/working-conventions.md`: stable coding, writing, testing,
  naming, quality guardrail, and domain conventions.
- `.agents/contexts/active-assumptions.md`: durable assumptions, constraints,
  and open operating defaults that affect future work, without decision history.

Optional extra shards are allowed when the project has a real need. Name them by
purpose, keep them referenced from `index.md`, and avoid copying source-document
detail into context.

## Context Size Guardrails

- `index.md` should stay compact.
- Shards should be purpose-based, not session-based.
- Do not create a new shard for every feature.
- Prefer fewer durable rules over many historical notes.

## Helper Script

Use the helper only for deterministic operations:

```bash
python3 /path/to/context-management/scripts/context_ops.py init [repo-path]
python3 /path/to/context-management/scripts/context_ops.py scan [repo-path]
python3 /path/to/context-management/scripts/context_ops.py validate [repo-path]
```

- `init` creates missing starter files from `assets/contexts/` and does not
  overwrite existing files unless `--overwrite` is passed.
- `scan` reports changelog-like phrases in `.agents/contexts/*.md`; use the
  results as review signals, not as an automatic rewrite.
- `validate` checks required shards, index references, and obvious changelog
  phrases. It exits nonzero for missing required files.

Do judgment-heavy `update` and `clear` edits manually after reading the relevant
workflow reference.

## Completion Checklist

- [ ] `index.md` exists and points to existing shards.
- [ ] Required default shards exist unless the user intentionally customized the
      layout.
- [ ] Context stores durable current facts, not session history.
- [ ] Context conflicts were resolved in favor of source files.
- [ ] Added or renamed shards are reflected in `index.md`.
- [ ] `python3 context-management/scripts/context_ops.py validate <repo>` passes
      or any warnings are reviewed.
