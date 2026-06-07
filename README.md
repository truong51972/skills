# Codex Skills

This repository contains local Codex skills.

## Install

Clone the repository:

```bash
git clone <repo-url> skills
cd skills
```

Copy the skill directories into your Codex skills folder:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
for skill in */SKILL.md; do
  [ -e "$skill" ] || continue
  cp -R "$(dirname "$skill")" "${CODEX_HOME:-$HOME/.codex}/skills/"
done
```

## Development Install

When editing skills, use symlinks so changes in this repository are picked up
without copying again:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
for skill in */SKILL.md; do
  [ -e "$skill" ] || continue
  dir="$(cd "$(dirname "$skill")" && pwd)"
  ln -s "$dir" "${CODEX_HOME:-$HOME/.codex}/skills/$(basename "$dir")"
done
```

## Verify

```bash
ls "${CODEX_HOME:-$HOME/.codex}/skills"
```

Restart Codex or open a new session after installing.
