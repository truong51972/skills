# Context Management Skill

Use this skill to manage reusable project context under `.agents/contexts/`. It helps future Codex sessions start quickly without relying on changelog, session notes, or stale memory.

## Workflows

- `context-management init`: create the default `.agents/contexts/` files for a repo.
- `context-management understand`: start a session by reading `index.md` only, then lazy-load relevant shards and source files.
- `context-management update`: end a session by saving durable project context only.
- `context-management clear`: end a session by pruning noisy context while preserving durable memory.

## Helper Commands

Initialize context files:

```bash
python3 skills/context-management/scripts/context_ops.py init .
```

Scan context for changelog-like noise:

```bash
python3 skills/context-management/scripts/context_ops.py scan .
```

## Context Layout

- `.agents/contexts/index.md`: compact startup map.
- `.agents/contexts/source-priority.md`: source ownership and read order.
- `.agents/contexts/project-baseline.md`: durable project baseline.
- `.agents/contexts/working-conventions.md`: stable conventions and guardrails.
- `.agents/contexts/active-assumptions.md`: assumptions and constraints that still affect future work.

## Rule Of Thumb

Context should describe the current durable state of the project. Do not store edit history, completed task notes, temporary TODOs, or session summaries.
