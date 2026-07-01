# Understand Lifecycle Operation

Run this operation automatically before non-trivial repository work when
`.agents/contexts/index.md` exists.

## Goal

Load the smallest useful amount of context needed to work accurately. `understand` is lazy-loading: start with `index.md` only, then open other shards only when the current task gives a clear reason.

## Trigger

Run before:

- Implementation that touches multiple files or repository contracts.
- Debugging that depends on repository structure.
- Code review.
- Architecture or system design work.
- Refactoring.
- Test design.
- Repository documentation work.
- Planning that affects source, workflow, or durable repo behavior.

Skip for independent syntax questions, text rewriting unrelated to the repo, and
trivial tasks that do not need repository knowledge.

## Steps

1. Read `.agents/contexts/index.md` first.
2. Determine the task scope from the user request and repository paths already
   implicated by the task.
3. Decide from the index which shard, if any, is needed next.
4. Read `source-priority.md` only when the task involves source ownership,
   canonical read order, resolving conflicting documentation, or
   detecting/repairing context drift.
5. If `source-priority.md` is loaded, follow its source roles to decide which
   source files to open.
6. Read any other shard only when it directly affects the current task.
7. Open source files when they own the requested change or are needed to verify context.
8. If context and source files disagree, trust the source files and treat context as stale.
9. Keep a note for the later sync phase when a durable context fact appears
   drifted.

## Selection Heuristics

- Load `source-priority.md` for source ownership, read order, file roles, source-of-truth conflicts, or drift repair.
- Load `project-baseline.md` for product, domain, architecture, document narrative, scope, or audience questions.
- Load `working-conventions.md` for style, coding patterns, writing rules, quality checks, test commands, or review expectations.
- Load `active-assumptions.md` when decisions depend on constraints, defaults, limits, or unresolved operating assumptions.
- Load optional shards only when `index.md` says they are relevant to the task.

## Source Verification

Open owning source before relying on a context fact that directly affects an
implementation or review decision. Context can route you to source, but source
is authoritative.

## If Context Is Missing

If `.agents/contexts/index.md` does not exist, say that no context system is initialized. Do not create it unless the user asks for `init` or clearly requests setup.

## Avoid

- Do not load every shard by default.
- Do not read `source-priority.md` automatically after `index.md`; it is also lazy-loaded.
- Do not treat context files as proof that source files are current.
- Do not edit context during `understand` unless the user explicitly asks.
