# Update Compatibility Note

`update` is now handled by the autonomous `sync` lifecycle operation.

Use [sync.md](sync.md) when durable current-state repository knowledge changed.
The user should not need to call `context-management update` during normal work.

## Durable Candidates

Preserve information that will help future sessions across tasks:

- Source-of-truth hierarchy or file ownership.
- Recommended startup paths, source roles, and read conditions.
- Stable project, product, architecture, domain, or workflow baseline.
- Reusable writing, coding, testing, naming, review, or collaboration conventions.
- Quality guardrails, acceptance checks, scope rules, or pruning labels.
- Durable decisions or assumptions that affect future work.
- Corrections that reveal a reusable rule.

## Reject

Remove or avoid adding:

- Session summaries and completed task logs.
- Edit history, changelog, "we changed X", "previously Y", or "fixed today" notes.
- Temporary TODOs, debugging notes, next actions, and transient blockers.
- Defensive corrections such as "do not do X because we just fixed it".
- Detailed source-document content that should remain in the source document.

## Migration Guidance

If an older prompt asks for `context-management update`, treat it as a request to
run `sync`:

- Load affected shards only.
- Verify affected facts against source.
- Rewrite durable context as current state.
- Run lint, validate, and static audit.

## Style

Prefer concise declarative rules:

- Good: `Use source documents as the authority for API shape.`
- Bad: `We fixed the API section today, so remember not to use the old shape.`

## Placement Guide

- `source-priority.md`: source ownership, recommended startup, file roles, source priority, conflict rules.
- `project-baseline.md`: purpose, audience, domain, architecture/content shape, scope boundaries, success criteria.
- `working-conventions.md`: domain conventions, style/output rules, quality guardrails, validation commands.
- `active-assumptions.md`: active assumptions, durable constraints, defaults, operating limits.
- `index.md`: shard map and loading policy only.
