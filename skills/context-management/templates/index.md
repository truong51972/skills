# Context Index

<!-- context-management:default-layout:v1 -->

Use this file as the compact startup map for this repo.

## Startup

1. Read this file first.
2. Decide which context shard, if any, is needed for the current task.
3. Load only the shard needed next; do not read all shards by default.
4. Read `source-priority.md` only when the task involves:
   - source ownership;
   - canonical read order;
   - resolving conflicting documentation;
   - detecting or repairing context drift.
5. Open source files before editing anything they own.
6. If context conflicts with source files, trust source files and update context later.

## Shards

- `source-priority.md`: source-of-truth hierarchy, recommended startup, source roles, and conflict rules.
- `project-baseline.md`: durable current project, domain, content, architecture, and scope baseline.
- `working-conventions.md`: stable repo conventions, quality guardrails, and style rules.
- `active-assumptions.md`: durable assumptions, constraints, and operating defaults that affect future work.

## Loading Policy

- Keep this index short enough to read at the start of every focused task.
- Treat every other context file as lazy-loaded.
- Load shards individually; do not assign a task category a default multi-shard bundle.
- Add optional shards only when targeted loading would make future work faster or safer.
- Keep shard descriptions current when files are added, renamed, or retired.

## Context Hygiene

Keep context concise, durable, and current-state focused.
