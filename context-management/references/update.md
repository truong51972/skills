# Update Workflow

Use this workflow near the end of a session when the user asks to save context, remember what matters, or prepare the next session.

## Goal

Update `.agents/contexts/` with durable current-state memory only.

## Durable Candidates

Keep information that will help future sessions across tasks:

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

## Steps

1. Review the session outcome and current context files.
2. Inspect source files for any fact that should be grounded before writing context.
3. Classify each candidate as source priority, source role, baseline, scope rule, convention, guardrail, assumption, or reject.
4. Rewrite the relevant shard as current state, not history.
5. Update `index.md` only if shard descriptions or read order changed.
6. Run the helper scan and prune any changelog-like leftovers:

   ```bash
   python3 /path/to/context-management/scripts/context_ops.py scan <repo-path>
   ```

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
