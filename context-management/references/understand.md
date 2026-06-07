# Understand Workflow

Use this workflow at the start of a session or when the user asks you to bootstrap from existing context.

## Goal

Load the smallest useful amount of context needed to work accurately.

## Steps

1. Read `.agents/contexts/index.md` first.
2. Read `source-priority.md` next when the task involves editing, interpreting source ownership, or resolving drift.
3. Follow `Recommended Startup` and `Source Roles` to decide which source files to open.
4. Use the index to choose only the remaining shards relevant to the user request.
5. Open source files named by `source-priority.md` when they own the requested change.
6. If context and source files disagree, trust the source files and treat context as stale.
7. Summarize the loaded baseline briefly before doing substantial work.

## Selection Heuristics

- Load `project-baseline.md` for product, domain, architecture, document narrative, scope, or audience questions.
- Load `working-conventions.md` for style, coding patterns, writing rules, quality checks, test commands, or review expectations.
- Load `active-assumptions.md` when decisions depend on constraints, defaults, limits, or unresolved operating assumptions.
- Load optional shards only when `index.md` says they are relevant to the task.

## If Context Is Missing

If `.agents/contexts/index.md` does not exist, say that no context system is initialized. Do not create it unless the user asks for `init` or clearly requests setup.

## Avoid

- Do not load every shard by default.
- Do not treat context files as proof that source files are current.
- Do not edit context during `understand` unless the user explicitly asks.
