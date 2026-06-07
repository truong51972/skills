---
name: context-management
description: Reusable repo context management for Codex sessions. Use when the user asks to initialize `.agents/contexts/`, bootstrap a new session by understanding project context, update context at the end of a session, or clear/compact context by removing changelog-style noise while preserving durable repo memory.
---

# Context Management

Manage reusable project context stored under `.agents/contexts/`. This skill is about context discipline, not domain content: keep startup memory compact, source-grounded, and free of session changelog.

## Workflow Router

Choose exactly one workflow from the user request:

- **init**: create a new `.agents/contexts/` structure. Read [init.md](references/init.md).
- **understand**: start a new session by loading context. Read [understand.md](references/understand.md).
- **update**: end a session by preserving only durable learnings. Read [update.md](references/update.md).
- **clear**: end a session by pruning context noise. Read [clear.md](references/clear.md).

If the user says `context-management init`, `context-management update`, `context-management clear`, or `context-management understand`, follow the named workflow. If the user asks generally to save, clean, compact, remember, or prepare context for next time, use `update` or `clear` based on whether new durable information should be added.

## Non-Negotiable Rules

- Treat context as startup memory, not source of truth. Real source files win when they conflict with context.
- Do not use `AGENTS.md` as the main context mechanism.
- Do not auto-migrate legacy `.agents/context.md` during `init`; only use it if the user explicitly asks.
- Keep `.agents/contexts/index.md` compact so future sessions can decide what to load.
- Read `index.md` first and lazy-load only the shards needed for the current task.
- Do not read all context shards by default.
- Store current durable baseline, not revision history.
- Never store session summaries, completed task logs, edit history, temporary TODOs, or "what just happened" narration.
- Rewrite durable corrections as general rules instead of recording the correction.
- Split or add shards only when targeted loading becomes useful.

## Expected Context Layout

Default project context files:

- `.agents/contexts/index.md`: compact entrypoint, shard map, loading policy, and startup route.
- `.agents/contexts/source-priority.md`: source-of-truth hierarchy, recommended startup, document/source roles, and conflict handling.
- `.agents/contexts/project-baseline.md`: durable current repo, product, domain, architecture, content, and scope baseline.
- `.agents/contexts/working-conventions.md`: stable coding, writing, testing, naming, quality guardrail, and domain conventions.
- `.agents/contexts/active-assumptions.md`: durable assumptions, constraints, and open operating defaults that affect future work, without decision history.

Optional extra shards are allowed when the project has a real need. Name them by purpose, keep them referenced from `index.md`, and avoid copying source-document detail into context.

## Adaptation Pattern

For code projects, source priority often maps configs, schemas, entrypoints, tests, APIs, migrations, and package manifests to their ownership roles. For document projects, source priority often maps drafts, reference docs, prompts, checklists, and final artifacts. In both cases, the skill should preserve the same generic shape: where to start, which source owns which facts, which baseline matters, which conventions shape edits, and which assumptions remain active.

## Helper Script

Use the helper only for deterministic operations:

```bash
python3 /path/to/context-management/scripts/context_ops.py init [repo-path]
python3 /path/to/context-management/scripts/context_ops.py scan [repo-path]
```

- `init` creates missing starter files from `assets/contexts/` and does not overwrite existing files unless `--overwrite` is passed.
- `scan` reports changelog-like phrases in `.agents/contexts/*.md`; use the results as review signals, not as an automatic rewrite.

Do judgment-heavy `update` and `clear` edits manually after reading the relevant workflow reference.
