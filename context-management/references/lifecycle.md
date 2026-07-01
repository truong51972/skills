# Autonomous Context Lifecycle

Use this lifecycle when `.agents/contexts/index.md` exists and the user gives a
non-trivial repository task.

```text
Repository task begins
        |
        v
Context system enabled?
        |
        +-- No --> Continue normally
        |
        +-- Yes
             |
             v
        UNDERSTAND
             |
             v
        Perform repository task against source
             |
             +-- Context affects decision?
             +-- Context conflicts with source?
             +-- Relevant source changed?
             +-- Review/audit task?
                         |
                         v
                  SCOPED SEMANTIC AUDIT
                         |
                         v
        Durable repository knowledge changed?
             |
             +-- No --> No context mutation
             |
             +-- Yes
                    |
                    v
                   SYNC
                    |
                    +-- verify affected facts
                    +-- prune stale or noisy facts
                    +-- update durable current knowledge
                    +-- run deterministic validation
```

## Constraints

- Context is durable guidance, not source of truth.
- Source code, configuration, schema/migrations, runtime contracts, tests,
  canonical project documentation, and repository instructions win over context.
- Static helper commands verify deterministic quality only. They do not prove
  semantic accuracy against source.
- Load only task-relevant shards. Do not preload every context file.
- Sync only durable current-state knowledge. Do not store session history.
