# Context Management Skill

When `.agents/contexts/index.md` exists, this skill manages repository context
autonomously during normal agent work.

The agent:

- reads relevant context before substantial work;
- verifies context against source when needed;
- detects drift;
- synchronizes durable changes after work;
- avoids storing session history and source-owned implementation details.

Context is durable guidance, not a source-of-truth replacement. Source code,
configuration, migrations, runtime contracts, tests, canonical docs, and
repository instructions remain authoritative.

## Diagnostics

The helper CLI is for deterministic diagnostics and setup, not the primary
operating model.

```bash
python3 skills/context-management/scripts/context_ops.py init .
python3 skills/context-management/scripts/context_ops.py lint .
python3 skills/context-management/scripts/context_ops.py scan .
python3 skills/context-management/scripts/context_ops.py validate .
python3 skills/context-management/scripts/context_ops.py audit .
python3 skills/context-management/scripts/context_ops.py audit . --format json
python3 skills/context-management/scripts/context_ops.py status .
```

## Context Layout

- `.agents/contexts/index.md`: compact startup map.
- `.agents/contexts/source-priority.md`: source ownership and read order.
- `.agents/contexts/project-baseline.md`: durable project baseline.
- `.agents/contexts/working-conventions.md`: stable conventions and guardrails.
- `.agents/contexts/active-assumptions.md`: assumptions and constraints that still affect future work.

## Rule Of Thumb

Context should describe the current durable state of the project. Do not store edit history, completed task notes, temporary TODOs, or session summaries.

Static CLI checks report structure, references, hygiene, compactness, duplicate
signals, and path existence. They do not prove semantic accuracy against source;
semantic verification requires the agent lifecycle workflow.
