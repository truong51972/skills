# system-prompt-builder

A reusable Agent Skill for building, reviewing, refactoring, and standardizing production system/developer prompts.

## What it does

The skill treats prompt construction as a small compilation pipeline:

```text
use case
  -> classify task
  -> allocate responsibilities
  -> select patterns
  -> compose prompt
  -> lint
  -> evaluate
```

It supports:

- Free-form generation
- Provider-native structured output
- Extraction and classification
- Grounded RAG
- Tool-using agents
- Routers and planners
- Judges, critics, and meta-judges
- Coding and implementation agents
- Reasoning, instruction-following, and smaller models

## Install

Copy the entire `system-prompt-builder` directory into the skill directory used by your agent environment.

Keep the directory name unchanged unless your environment explicitly supports renaming skills.

## Typical requests

- Build a system prompt for a semantic extraction worker.
- Review and shorten this system prompt.
- Convert this prompt to provider-native structured output.
- Separate stable system instructions from runtime specs.
- Build a tool-agent prompt with read/write boundaries.
- Create a judge prompt for a supplied runtime rubric.

## Main files

- `SKILL.md`: primary workflow and trigger description
- `references/`: pattern and design guidance loaded as needed
- `assets/`: reusable prompt templates
- `scripts/lint_prompt.py`: deterministic prompt linter
- `evals/fixtures/`: sample skill-evaluation cases
- `examples/`: completed prompt examples

## Lint a prompt

```bash
python scripts/lint_prompt.py path/to/prompt.md
```

Strict mode exits non-zero when warnings are found:

```bash
python scripts/lint_prompt.py --strict path/to/prompt.md
```

JSON output:

```bash
python scripts/lint_prompt.py --format json path/to/prompt.md
```

## Design principle

```text
Stable behavior       -> system/developer prompt
Request-specific rule -> runtime input
Output shape          -> response schema
Hard enforcement      -> application code
Quality confidence    -> eval suite
```
