# Clear Compatibility Note

Routine `clear` behavior is now part of the autonomous `sync` lifecycle
operation. Use [maintenance.md](maintenance.md) only for broad cleanup or reset.

## Goal

Prune context without losing durable repo memory. Cleanup should preserve current
durable guidance and remove session history, stale assumptions, duplicates, and
source-owned details.

## Remove

- Session summaries.
- Completed work notes.
- Edit history and changelog-style text.
- Temporary TODOs or next-step lists.
- Stale assumptions that source files no longer support.
- Defensive "do not do X because we fixed it" notes.
- Duplicate detail copied from source docs.

## Preserve

- Source priority and conflict rules.
- Recommended startup and source roles.
- Current durable project baseline.
- Scope rules and success criteria that still shape future work.
- Stable working conventions and quality guardrails.
- Active assumptions that future sessions still need.
- Compact shard descriptions in `index.md`.

## Migration Guidance

If an older prompt asks for `context-management clear`, treat it as maintenance
only when the problem is broad. Otherwise fold cleanup into `sync`.

Run deterministic checks after cleanup:

```bash
python3 /path/to/context-management/scripts/context_ops.py lint <repo-path>
python3 /path/to/context-management/scripts/context_ops.py validate <repo-path>
python3 /path/to/context-management/scripts/context_ops.py audit <repo-path>
```

## Shard Cleanup Guide

- `index.md`: keep the shard map short; remove detailed rules that belong in a shard.
- `source-priority.md`: keep source roles and conflict rules; remove source detail that belongs in source files.
- `project-baseline.md`: keep current durable baseline and scope; remove low-level implementation detail unless it guides many future tasks.
- `working-conventions.md`: keep stable conventions and guardrails; remove one-off preferences.
- `active-assumptions.md`: keep only assumptions still needed for future work.

## Reset

Do not reset context to an empty skeleton unless the user explicitly asks for a reset. If a reset is requested, preserve source files and do not delete `.agents/contexts/` without explicit confirmation.
