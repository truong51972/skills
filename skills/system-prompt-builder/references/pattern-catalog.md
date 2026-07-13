# Pattern Catalog

Use this catalog to select the smallest set of patterns needed for a prompt.

## Selection flow

```text
Is the output machine-consumed?
  yes -> structured-output

Does the model use tools or external mutable state?
  yes -> tool-agent

Does the model judge another output?
  yes -> evaluator

Does the model only select the next workflow?
  yes -> router/planner

Does the model extract facts from supplied data?
  yes -> extraction/classification

Must the answer be supported only by supplied or retrieved evidence?
  yes -> grounded-rag
```

Multiple patterns may apply. For example:

```text
semantic graph extraction
= structured-output
+ extraction
+ grounded-input
+ small-model procedure
```

## Base direct-response

### Use when

- Producing analysis, recommendations, reports, code, or transformations.
- No provider-native structured output is required.
- No tools or retrieval are involved.

### Include

- Stable responsibility and goal.
- Input contract when runtime data is complex.
- Relevant stable constraints.
- Output expectations.
- Semantic completion criteria.

### Avoid

- Generic reasoning loops.
- Empty sections.
- A large decision framework for a simple task.
- Repeating the user request.

## Structured output

### Use when

- The result is parsed by code.
- The provider supports native structured output.
- A Pydantic, JSON Schema, or equivalent contract exists.

### Include

- Semantic meaning of the output.
- Evidence and grounding rules.
- Missing-information behavior.
- Cross-item consistency criteria.

### Keep outside the prompt

- Field names and types already represented by schema.
- Required-property declarations.
- Enum definitions unless their business meaning needs explanation.
- Exact serialization behavior.

### Common failure modes

- Required fields force fabricated values.
- Schema allows no unknown or not-applicable state.
- Prompt and schema disagree.
- Prompt repeats the full schema.
- Semantic validation is assumed to be structural validation.

## Extraction and classification

### Use when

- Extracting entities, relationships, facts, metadata, labels, or attributes.
- Classifying records, messages, documents, or events.

### Include

- What counts as evidence.
- Whether inference is allowed.
- Normalization rules.
- Ambiguity handling.
- Empty-result behavior.
- Batch alignment.
- Duplicate handling.
- Relationship endpoint rules when applicable.

### Common failure modes

- Co-occurrence is mistaken for a relationship.
- Model invents values to satisfy required fields.
- Batch item count changes.
- Unknown and not-applicable are conflated.
- Evidence span does not support the extracted object.

## Grounded RAG

### Use when

- Answering from documents, policy, retrieval, or supplied reference material.
- The model must not rely on unsupported prior knowledge.

### Include

- Allowed source set.
- Source priority.
- Permitted inference level.
- Conflict resolution.
- Citation or evidence requirements.
- Insufficient-evidence behavior.
- Data/instruction boundary.

### Common failure modes

- Retrieved prompt injection overrides system instructions.
- Current policy and stale policy are mixed.
- Model fills gaps using prior knowledge.
- Sources conflict without explicit handling.

## Tool-using agent

### Use when

- The model can call tools, APIs, databases, search, code execution, or MCP servers.
- External state or side effects are possible.

### Include

- When tool use is mandatory, optional, or unnecessary.
- Read/write boundary.
- Verification before using tool results.
- Retry budget.
- Stop conditions.
- Failure behavior.
- Permission requirements for side effects.

### Common failure modes

- Tool schema is duplicated in prompt prose.
- Tool results are fabricated.
- Write actions occur during analysis-only requests.
- Tool failure triggers infinite retries.
- The agent claims completion without verification.

## Router or planner

### Use when

- Selecting a route, tool, agent, workflow, evaluation dimension, or next step.
- Producing a plan for downstream execution.

### Include

- Allowed route set.
- Selection criteria.
- Fallback behavior.
- Confidence or uncertainty behavior.
- Clear prohibition against solving the downstream task when not required.
- Minimum information downstream needs.

### Common failure modes

- Router performs the task itself.
- New routes are invented.
- Output is too vague for downstream use.
- Planner expands scope unnecessarily.

## Evaluator, judge, critic, and meta-judge

### Use when

- Evaluating another model, agent, response, trace, prompt, or record.
- Applying a runtime rubric.

### Include

- Rubric source and authority.
- Evidence requirements.
- N/A behavior.
- Critical blocker policy.
- Score anchors.
- Separation of observation, assessment, and recommendation.
- Reconciliation policy for meta-judges.

### Common failure modes

- Judge rewrites instead of evaluates.
- Score is based on style preference instead of rubric.
- Missing evidence is converted into a confident score.
- Aggregate score hides a blocker.
- Critic repeats the judge without adding adversarial review.

## Coding or implementation agent

### Use when

- Implementing, fixing, refactoring, or reviewing code.
- Editing a repository or configuration.

### Include

- Inspect before modifying.
- Preserve invariants and public contracts.
- Minimal scope.
- Relevant validation.
- Honest completion status.
- Explicit handling of unavailable tests or blockers.

### Common failure modes

- Changes are made without inspecting current behavior.
- Unrelated refactoring expands scope.
- Tests are claimed but not run.
- Existing API compatibility is broken.
- Generated code ignores repository conventions.

## Research and synthesis

### Use when

- Researching current technologies, standards, companies, products, or architecture choices.
- Comparing alternatives.

### Include

- Freshness requirement.
- Source priority.
- Primary-source preference.
- Fact versus inference separation.
- Conflict handling.
- Decision criteria.
- Recommendation tied to evidence and constraints.

### Common failure modes

- Stale information is treated as current.
- Sources are listed but not synthesized.
- Recommendation does not reflect user constraints.
- Inference is presented as fact.
