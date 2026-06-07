# Clear Workflow

Use this workflow near the end of a session when context has become noisy and should be compacted for the next session.

## Goal

Prune context without losing durable repo memory. `clear` means compact and clean by default, not reset.

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

## Steps

1. Read `index.md` and identify which shards need cleanup.
2. Run the helper scan to find likely noise:

   ```bash
   python3 /path/to/context-management/scripts/context_ops.py scan <repo-path>
   ```

3. For each flagged item, decide whether it is transient noise or a durable rule.
4. Delete transient noise.
5. Rewrite durable corrections as general rules.
6. Keep each shard focused on its stated purpose.
7. Re-run the scan and make sure remaining matches are intentional.

## Shard Cleanup Guide

- `index.md`: keep the shard map short; remove detailed rules that belong in a shard.
- `source-priority.md`: keep source roles and conflict rules; remove source detail that belongs in source files.
- `project-baseline.md`: keep current durable baseline and scope; remove low-level implementation detail unless it guides many future tasks.
- `working-conventions.md`: keep stable conventions and guardrails; remove one-off preferences.
- `active-assumptions.md`: keep only assumptions still needed for future work.

## Reset

Do not reset context to an empty skeleton unless the user explicitly asks for a reset. If a reset is requested, preserve source files and do not delete `.agents/contexts/` without explicit confirmation.
