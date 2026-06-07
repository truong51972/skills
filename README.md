# My Custom Codex Skills

This repository contains my personal custom skills for Codex.

Repository: [truong51972/skills](https://github.com/truong51972/skills)

## Install

Clone the repository:

```bash
git clone https://github.com/truong51972/skills.git
cd skills
```

Copy every skill directory into your Codex skills folder:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
for skill in */SKILL.md; do
  [ -e "$skill" ] || continue
  cp -R "$(dirname "$skill")" "${CODEX_HOME:-$HOME/.codex}/skills/"
done
```

## Development Install

If you are editing these skills locally, use symlinks so changes are picked up
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
