# Evaluation fixtures

These fixtures evaluate whether the skill selects the right prompt patterns and responsibility layers.

They are intentionally implementation-neutral.

Suggested usage:

1. Send each fixture `request` to the skill.
2. Inspect the generated prompt and design notes.
3. Check `expected_patterns`.
4. Check all `required_elements`.
5. Confirm all `forbidden_elements` are absent.
6. Review `expected_layering`.
