# Structured Output

Use this reference for provider-native structured output, LangChain structured output, Pydantic, or JSON Schema.

## Responsibility matrix

| Concern | Primary layer |
|---|---|
| Field names | Schema |
| Types | Schema |
| Required fields | Schema |
| Enum values | Schema |
| Nullability | Schema |
| Field meaning | Schema description and prompt |
| Evidence requirements | Prompt |
| Missing-information behavior | Schema and prompt |
| Cross-field integrity | Application validation |
| Referential integrity | Application validation |
| Retry policy | Application |
| Business policy | Runtime specs |
| Stable invariants | System prompt |

## Core rules

1. Treat the schema as the structural source of truth.
2. Do not reproduce the full schema in prompt prose.
3. Use field descriptions for local semantic meaning.
4. Use the system prompt for global semantic behavior.
5. Use runtime specs for request-specific business policy.
6. Use application validation for rules the model cannot guarantee deterministically.

## Represent absence explicitly

A schema should allow legitimate absence.

Prefer:

```python
relationships: list[Relationship] = []
```

or:

```python
status: Literal["extracted", "insufficient_evidence", "not_applicable"]
value: Value | None = None
reason: str | None = None
```

Avoid requiring a fabricated value when no evidence exists.

## Unknown versus not applicable

- `unknown`: a value should exist, but the input does not establish it.
- `not_applicable`: the field or criterion does not apply.
- `empty`: the valid result is an empty collection.
- `failed`: processing could not complete.
- `unsupported`: the input is outside the task contract.

Do not collapse these states unless the application genuinely treats them the same.

## Batch alignment

For batch extraction:

- Preserve one output envelope per input item.
- Carry a stable input ID.
- Do not drop failed items.
- Do not reorder items unless explicitly allowed.
- Put item-level errors inside the corresponding output envelope.
- Validate output count and IDs in application code.

Example envelope:

```python
class ItemResult(BaseModel):
    input_id: str
    status: Literal["success", "insufficient_evidence", "failed"]
    extraction: Extraction | None = None
    error: ErrorInfo | None = None
```

## Semantic validation

Schema validation does not guarantee:

- Evidence supports a claim.
- A relationship endpoint exists.
- A selected enum is correct.
- A score matches a rubric.
- A summary is faithful.
- Results are mutually consistent.

Add deterministic validators where possible.

Typical validators:

- IDs referenced by relationships exist.
- No forbidden self-reference.
- Evidence span belongs to the input item.
- Enum choice is compatible with populated fields.
- Status and nullable fields are consistent.
- Batch input IDs are preserved exactly.

## Retry classification

Distinguish:

1. **Transport/provider failure**  
   Retry according to infrastructure policy.

2. **Schema parse failure**  
   Retry with the same task and concise validation feedback.

3. **Semantic validation failure**  
   Retry only when feedback is actionable and bounded.

4. **Unsupported or insufficient input**  
   Return the schema-defined failure or absence state. Do not retry blindly.

5. **Policy conflict**  
   Resolve instruction priority or fail explicitly.

## LangChain and Pydantic notes

- Prefer provider-native structured output when supported.
- Use Pydantic field descriptions for semantic details local to a field.
- Keep models shallow when using smaller models.
- Avoid validators that silently mutate model output into a different meaning.
- Log raw validation errors and distinguish structural from semantic failures.
