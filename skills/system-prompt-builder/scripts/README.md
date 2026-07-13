# Prompt linter

`lint_prompt.py` performs deterministic checks only.

It intentionally does not assign a subjective quality score.

## Errors

- Unresolved `[REPLACE]`, `[TODO]`, `[TBD]`, or `[Paste ...]`
- Remaining `NOTE:`, `OPTIONAL:`, `EXAMPLE:` annotations
- Remaining HTML comments
- Unbalanced simple XML-style tags
- Missing files or invalid UTF-8

## Warnings

- Raw chain-of-thought request
- Generic prestige role
- Vague quality instruction
- Duplicate headings
- Too many sections
- Very large prompt
- `<Data>` without a data/instruction boundary
- Structured extraction without absence behavior
- Tool prompt without failure behavior
