# Understand Workflow

Use this workflow at the start of a session or when the user asks you to bootstrap from existing context.

## Goal

Load the smallest useful amount of context needed to work accurately. `understand` is lazy-loading: start with `index.md` only, then open other shards only when the current task gives a clear reason.

## Steps

1. Read `.agents/contexts/index.md` first.
2. Decide from the user request and the index which shard, if any, is needed next.
3. Read `source-priority.md` only when the task involves editing files, interpreting source ownership, choosing source files, or resolving drift.
4. If `source-priority.md` is loaded, follow its `Recommended Startup` and `Source Roles` to decide which source files to open.
5. Read any other shard only when it directly affects the current task.
6. Open source files when they own the requested change or are needed to verify context.
7. If context and source files disagree, trust the source files and treat context as stale.
8. Summarize only the context actually loaded before doing substantial work.

## Selection Heuristics

- Load `source-priority.md` for source ownership, read order, file roles, source-of-truth conflicts, or edits.
- Load `project-baseline.md` for product, domain, architecture, document narrative, scope, or audience questions.
- Load `working-conventions.md` for style, coding patterns, writing rules, quality checks, test commands, or review expectations.
- Load `active-assumptions.md` when decisions depend on constraints, defaults, limits, or unresolved operating assumptions.
- Load optional shards only when `index.md` says they are relevant to the task.

## If Context Is Missing

If `.agents/contexts/index.md` does not exist, say that no context system is initialized. Do not create it unless the user asks for `init` or clearly requests setup.

## Avoid

- Do not load every shard by default.
- Do not read `source-priority.md` automatically after `index.md`; it is also lazy-loaded.
- Do not treat context files as proof that source files are current.
- Do not edit context during `understand` unless the user explicitly asks.
