---
name: context-management
description: >
  When .agents/contexts/index.md exists, autonomously manage durable repository context before, during, and after
  non-trivial coding, debugging, review, architecture, planning, testing,
  and documentation tasks. Proactively load relevant context, verify context against source when needed, detect
  drift, and synchronize durable changes without requiring the user to invoke
  this skill by name.
---

# Context Management

Autonomously manage reusable project context stored under `.agents/contexts/`.
This skill is about context discipline, not domain content: keep startup memory
compact, source-grounded, scoped to the current task, and free of session
changelog.

Use this skill proactively. Do not wait for the user to say
`context-management` when `.agents/contexts/index.md` exists and the task is a
non-trivial repository task.

## Ownership Boundary

This skill owns `.agents/contexts/` only: startup memory, durable baseline,
source priority, conventions, assumptions, lifecycle guidance, and deterministic
quality tooling.

Use domain skills for domain facts. Context may point to source files, but it
must not copy source-of-truth detail from Python packages, Dockerfiles, Compose,
Celery configuration, DI containers, schemas, tests, or product documents.

## Activation

Context management is enabled when the repository contains:

```text
.agents/contexts/index.md
```

When that file exists, apply the autonomous lifecycle for non-trivial coding,
debugging, review, architecture, planning, testing, and documentation tasks.

Do not create a context system automatically in unrelated repositories. Run
`init` only when the user requests setup or repository instructions explicitly
enable context management and no `index.md` exists. Never reset, delete, or
reinitialize an existing context system without an explicit request.

## Lifecycle Controller

For repository tasks:

1. Detect whether `.agents/contexts/index.md` exists.
2. If not enabled, continue normally.
3. If enabled, run **UNDERSTAND** before substantial work. Read
   [understand.md](references/understand.md).
4. Perform the requested task against source files, tests, configuration, and
   canonical docs. Source always wins over context.
5. Run a scoped **SEMANTIC AUDIT** when context affects a decision, conflicts
   with source, the task changes source roots referenced by context, or the user
   asks for review/architecture/correctness. Read [audit.md](references/audit.md).
6. Run **SYNC** only when durable repository knowledge changed. Read
   [sync.md](references/sync.md).
7. Run **MAINTENANCE** only for broad cleanup, size/duplicate pressure, orphan
   shards, routing breakage, large architecture changes, or explicit user
   cleanup/reset requests. Read [maintenance.md](references/maintenance.md).

`understand`, `audit`, `sync`, and `maintenance` are internal lifecycle
operations. The user should not need to call them manually during normal work.

## Manual Setup

Use [init.md](references/init.md) only when creating a context system for a repo
that does not already have `.agents/contexts/index.md`.

Compatibility references remain for old prompts:

- [update.md](references/update.md): handled by `sync`.
- [clear.md](references/clear.md): routine cleanup is part of `sync`;
  broad cleanup is `maintenance`.

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
- Do not preload `source-priority.md` for every task; load it only when source
  ownership, canonical read order, source-of-truth editing, conflicting
  documentation, or drift repair matters.
- Store current durable baseline, not revision history.
- Never store session summaries, completed task logs, edit history, temporary
  TODOs, or "what just happened" narration.
- Rewrite durable corrections as general rules instead of recording the
  correction.
- Split or add shards only when targeted loading becomes useful.
- Do not present static CLI checks as semantic verification. Static checks can
  report structure, references, hygiene, compactness, duplicates, and path
  existence; semantic accuracy requires agent reasoning against source files.



## Helper Script

Use the helper only for deterministic operations:

```bash
python3 /path/to/context-management/scripts/context_ops.py init [repo-path]
python3 /path/to/context-management/scripts/context_ops.py lint [repo-path]
python3 /path/to/context-management/scripts/context_ops.py scan [repo-path]
python3 /path/to/context-management/scripts/context_ops.py validate [repo-path]
python3 /path/to/context-management/scripts/context_ops.py audit [repo-path]
python3 /path/to/context-management/scripts/context_ops.py status [repo-path]
```

- `init` creates missing starter files from `templates/` and does not overwrite
  existing files unless `--overwrite` is passed.
- `lint` checks deterministic content hygiene.
- `scan` is a backward-compatible alias for `lint`.
- `validate` is the structural gate.
- `audit` reports static quality signals; it does not verify semantic accuracy
  against repository sources.
- `status` summarizes context size, references, and warnings.

All JSON output includes `semantic_source_verification.status:
not_performed`. Static helper output must never claim that context is fully
aligned with source.

## Completion Checklist

- [ ] `index.md` exists and points to existing shards.
- [ ] Context stores durable current facts, not session history.
- [ ] Context conflicts were resolved in favor of source files.
- [ ] Added or renamed shards are reflected in `index.md`.
- [ ] `source-priority.md` was loaded only when the task needed ownership,
      read-order, editing, documentation conflict, or drift context.
- [ ] `python3 context-management/scripts/context_ops.py lint <repo>` and
      `validate <repo>` pass, or warnings are reviewed.
- [ ] `python3 context-management/scripts/context_ops.py audit <repo>` reports
      only accepted deterministic warnings.
