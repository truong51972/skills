# Skill Evaluation

Evaluate the skill itself, not only the prompts it generates.

## Evaluation dimensions

### Outcome

- Does the generated prompt address the requested use case?
- Is the final deliverable directly usable?
- Does it preserve required behavior?
- Does it define missing-information behavior?

### Process

- Did the skill classify the task correctly?
- Did it select the necessary patterns?
- Did it separate system, runtime, schema, code, and eval responsibilities?
- Did it avoid unnecessary modules?

### Style

- Is the prompt concise and unambiguous?
- Are completion criteria observable?
- Are data and instruction boundaries explicit when needed?
- Are authoring annotations removed?

### Efficiency

- Is the prompt no longer than necessary?
- Does it avoid duplicating schema or tool definitions?
- Does it avoid a generic reasoning ritual?
- Would a narrower prompt or pipeline be more reliable?

## Must-pass checks

A small set of deterministic checks is more useful than a vague global score.

Recommended checks:

- No unresolved placeholders.
- No request for raw chain-of-thought.
- No duplicated full response schema.
- Missing-information behavior exists for extraction.
- Tool prompts distinguish read and write.
- Evaluator prompts use runtime rubrics.
- Router prompts restrict allowed routes.
- Coding prompts require verification before claiming completion.

## Regression fixture format

```yaml
name: example
request: |
  User request here.
expected_patterns:
  - structured-output
required_elements:
  - evidence-only extraction
forbidden_elements:
  - raw chain-of-thought
expected_layering:
  system:
    - stable role
  runtime:
    - current specs
  schema:
    - output fields
  code:
    - cross-field validation
```

## Review questions

1. What pattern did the skill select?
2. Which instructions were moved out of the system prompt?
3. What failure behavior was added?
4. What was intentionally left to schema or code?
5. What test would catch the most likely regression?
