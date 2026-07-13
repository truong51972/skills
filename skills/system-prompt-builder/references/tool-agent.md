# Tool-Using Agent Pattern

Use this reference for agents that call APIs, search, databases, code execution, file systems, MCP servers, or other tools.

## Tool contract

Each tool definition should communicate:

- Purpose.
- When to use it.
- When not to use it.
- Parameter meaning.
- Preconditions.
- Result meaning.
- Known limitations.
- Side effects.

Do not restate the full tool schema in the system prompt.

## Tool policy

Define:

### Requirement level

- `mandatory`: the task cannot be completed without tool verification.
- `optional`: use tools only when they materially improve correctness.
- `prohibited`: do not use tools for this task.

### Read/write boundary

- Read tools may inspect state.
- Write tools mutate state.
- Analysis-only requests must not trigger write tools.
- Side effects require the permission model enforced by the application.
- Prompt text is not a security boundary.

### Verification

Before relying on a tool result:

- Confirm the call succeeded.
- Confirm the result corresponds to the requested entity and timeframe.
- Detect empty, partial, stale, or contradictory results.
- Do not convert tool errors into facts.
- Use a second source or verification call when the task requires high confidence.

### Retry and stop conditions

Define:

- Maximum retry count.
- Which errors are retryable.
- When to switch strategy.
- When to return a blocker.
- When to stop to avoid duplicate side effects.

### Idempotency

For write actions:

- Prefer idempotency keys or stable operation IDs.
- Read current state before repeating an uncertain write.
- Do not retry non-idempotent operations blindly.
- Confirm final state after mutation when practical.

## Suggested system rules

- Use only tools relevant to the goal.
- Never fabricate a tool call, tool result, or successful side effect.
- Do not perform write actions when the request is read-only.
- Validate critical tool results before using them as evidence.
- Stop and report the blocker when required permission or data is unavailable.
- Do not claim completion until the final state is verified when verification is possible.

## Multi-tool workflows

Use parallel calls only when:

- Calls are independent.
- Side effects cannot conflict.
- Order does not matter.
- Rate and cost budgets permit it.

Use sequential calls when:

- A later call depends on an earlier result.
- Permission must be checked first.
- A write requires prior state.
- Results must be reconciled before proceeding.
