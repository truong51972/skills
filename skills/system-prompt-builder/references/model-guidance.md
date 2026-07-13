# Model Guidance

Model type changes the amount and form of instruction, but should not define the entire prompt architecture.

## Reasoning models

Prefer:

- Concise, direct instructions.
- Clear outcome, constraints, and success criteria.
- Decision criteria when trade-offs matter.
- Semantic completion checks.
- Explicit tool and grounding boundaries.

Avoid:

- “Think step by step.”
- Requests for raw chain-of-thought.
- Generic multi-step reasoning rituals.
- Repeating the same constraint across multiple sections.
- Excessive examples before establishing a zero-shot baseline.

Use an explicit procedure only when the procedure itself is externally required, such as a compliance workflow, deterministic review order, or domain-specific algorithm.

## Instruction-following or non-reasoning models

Prefer:

- Explicit task procedure when order matters.
- Direct edge-case rules.
- Concrete labels and boundaries.
- Few-shot examples for difficult distinctions.
- Short sections and unambiguous wording.
- Explicit completion checks.

Avoid:

- Large abstract governance frameworks.
- Many soft priorities with no observable behavior.
- Hidden assumptions about how missing data should be handled.

## Smaller or cost-optimized models

Prefer:

- Narrow prompts with one responsibility.
- Fewer optional behaviors.
- Shorter context.
- Explicit procedures.
- Concrete examples.
- Simple schemas.
- Deterministic preprocessing and post-validation in code.

Consider splitting:

```text
planner -> extractor -> validator
```

instead of asking one small model to perform all three roles.

Avoid:

- Long lists of equally important constraints.
- Deeply nested output schemas.
- Ambiguous enum choices.
- Several independent goals in one invocation.
- Large heterogeneous batches.

## Long-context workloads

Long context does not remove the need for structure.

Prefer:

- Clear document boundaries.
- Stable IDs for evidence references.
- Chunk or section identifiers.
- Explicit source priority.
- A focused task near the beginning and a concise execution directive near the end.
- Retrieval or preprocessing when only a small portion of the context is relevant.

Avoid:

- Treating every token as equally relevant.
- Mixing current and obsolete policy without version metadata.
- Injecting a full document corpus when a retrieval step can narrow it.

## Provider-specific overrides

Keep provider-specific behavior outside the core pattern unless it materially affects:

- Structured output support.
- Tool-calling semantics.
- Reasoning configuration.
- Context limits.
- Prompt caching.
- Safety or refusal behavior.

When provider behavior matters, document it as an integration note rather than creating an entirely separate master prompt.
