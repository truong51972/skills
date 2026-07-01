# Sync Lifecycle Operation

Use `sync` to mutate `.agents/contexts/` after a task only when durable
repository knowledge changed.

## Durable Deltas

Sync changes to:

- Architecture boundaries.
- Component ownership.
- Source-of-truth locations.
- Stable repository workflows.
- Stable conventions.
- Reusable quality guardrails.
- Durable invariants.
- Current project scope.
- Active assumptions.
- Recommended repository read paths.

Do not sync for a small implementation bug fix, internal rename with no contract
impact, temporary workaround, completed task history, a one-time test result, or
details already clear from source.

## Steps

1. Identify the durable delta.
2. Load affected shards only.
3. Verify existing affected facts against source.
4. Remove stale, duplicated, historical, overly detailed, or misplaced content.
5. Add or rewrite durable current-state knowledge.
6. Preserve concise source references rather than copied detail.
7. Update `index.md` only when shard routing changes.
8. Run `context_ops.py lint`.
9. Run `context_ops.py validate`.
10. Run `context_ops.py audit`.
11. Resolve deterministic findings where possible.

Cleanup is part of sync. Do not run a separate cleanup flow unless maintenance
conditions apply.
