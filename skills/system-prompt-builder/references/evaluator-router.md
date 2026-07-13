# Evaluator and Router Patterns

## Judge

A judge applies a supplied rubric to a target artifact or trace.

Require:

- Rubric criteria supplied at runtime.
- Evidence for each material finding.
- Score anchors or decision thresholds.
- N/A behavior.
- Critical blocker behavior.
- Separation of observation, assessment, score, and recommendation.

Do not let the judge:

- Rewrite the target instead of evaluating it.
- Invent rubric criteria.
- Score missing evidence as if it were positive evidence.
- Ignore a blocker because the average score is high.

## Critic

A critic performs adversarial review of an existing evaluation.

Require:

- Identify unsupported claims.
- Detect contradictions.
- Detect rubric misapplication.
- Find missed blockers or edge cases.
- Distinguish confirmed defects from possible concerns.

The critic should not merely restate the judge.

## Meta-judge

A meta-judge reconciles judge and critic outputs.

Require:

- Compare evidence quality.
- Resolve conflicts according to rubric authority.
- Preserve unresolved uncertainty.
- Produce a final verdict consistent with component findings.
- Never use simple majority voting when evidence strength differs.

## Router

A router selects one destination from a supplied set.

Require:

- Allowed route list.
- Selection criteria.
- Fallback route or abstention state.
- Confidence handling.
- Minimal rationale when useful for observability.

Do not allow the router to invent new routes.

## Planner

A planner creates an execution plan or selects evaluation dimensions.

Require:

- Bounded scope.
- Allowed steps, tools, or dimensions.
- Dependencies.
- Completion condition.
- Fallback for missing prerequisites.
- A plan detailed enough for downstream execution.

Do not let a planner perform the downstream work unless explicitly required.

## Rubric injection

Dynamic rubric content should be supplied at runtime.

The stable system prompt should define only:

- How to apply a rubric.
- Evidence standards.
- N/A behavior.
- Conflict handling.
- Score/verdict consistency.
- Prohibited evaluator behavior.

## Critical blockers

A blocker should be modeled separately from an aggregate score.

Example:

```python
has_critical_blocker: bool
blockers: list[Blocker]
score: float | None
verdict: Literal["pass", "fail", "needs_review"]
```

Application validation should verify that blocker and verdict fields are consistent.
