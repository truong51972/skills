# .agents/skills/scripts/validate_skills.py
#!/usr/bin/env python3
"""Validate this custom Codex skills repository."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


SKIP_TOP_LEVEL_DIRS = {
    ".agents",
    ".codex",
    ".git",
    ".github",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "scripts",
}

DESCRIPTION_MAX_CHARS = 140
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def repo_root_from(path: Path) -> Path:
    return path.resolve()


def skill_dirs(repo: Path) -> list[Path]:
    dirs: list[Path] = []
    for path in sorted(repo.iterdir()):
        if not path.is_dir() or path.name in SKIP_TOP_LEVEL_DIRS or path.name.startswith("."):
            continue
        dirs.append(path)
    return dirs


def frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    block: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        block.append(line)

    data: dict[str, str] = {}
    i = 0
    while i < len(block):
        line = block[i]
        if not line or line[0].isspace() or ":" not in line:
            i += 1
            continue
        key, raw_value = line.split(":", 1)
        value = raw_value.strip()
        if value in {">", "|", ">-", "|-"}:
            collected: list[str] = []
            i += 1
            while i < len(block) and (not block[i] or block[i][0].isspace()):
                collected.append(block[i].strip())
                i += 1
            data[key.strip()] = " ".join(part for part in collected if part)
            continue
        data[key.strip()] = value.strip('"').strip("'")
        i += 1
    return data


def strip_link_target(target: str) -> str:
    target = target.strip().strip("<>")
    target = target.split("#", 1)[0]
    return target.strip()


def is_external_or_anchor(target: str) -> bool:
    return (
        not target
        or target.startswith("#")
        or target.startswith("http://")
        or target.startswith("https://")
        or target.startswith("mailto:")
    )


def local_markdown_links(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    links: list[str] = []
    for match in MARKDOWN_LINK_RE.finditer(text):
        target = strip_link_target(match.group(1))
        if not is_external_or_anchor(target):
            links.append(target)
    return links


def check_markdown_links(path: Path) -> list[str]:
    errors: list[str] = []
    for target in local_markdown_links(path):
        resolved = (path.parent / target).resolve()
        if not resolved.exists():
            errors.append(f"{path}: missing link target {target}")
    return errors


def runnable_script(path: Path) -> tuple[bool, str]:
    if os.access(path, os.X_OK):
        return True, "executable"
    if path.suffix == ".py":
        result = subprocess.run(
            [sys.executable, str(path), "--help"],
            cwd=path.parent,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode == 0:
            return True, "python --help ok"
        return False, result.stderr.strip() or result.stdout.strip()
    return False, "not executable"


def validate(repo: Path) -> int:
    errors: list[str] = []

    skills = skill_dirs(repo)
    if not skills:
        errors.append("no top-level skill directories found")

    for skill in skills:
        skill_md = skill / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"{skill}: missing SKILL.md")
            continue

        metadata = frontmatter(skill_md)
        name = metadata.get("name")
        description = metadata.get("description", "")
        if name != skill.name:
            errors.append(f"{skill_md}: name {name!r} does not match folder {skill.name!r}")
        if not description:
            errors.append(f"{skill_md}: missing description")
        elif "\n" in description or len(description) > DESCRIPTION_MAX_CHARS:
            errors.append(
                f"{skill_md}: description should be one compact sentence "
                f"({len(description)} chars, max {DESCRIPTION_MAX_CHARS})"
            )

        errors.extend(check_markdown_links(skill_md))
        for reference in sorted((skill / "references").glob("*.md")):
            errors.extend(check_markdown_links(reference))

    for script in sorted(repo.glob("**/scripts/*")):
        if script.is_file():
            ok, detail = runnable_script(script)
            if not ok:
                errors.append(f"{script}: script is not executable or runnable: {detail}")

    context_ops = repo / "context-management" / "scripts" / "context_ops.py"
    if context_ops.exists():
        result = subprocess.run(
            [sys.executable, str(context_ops), "--help"],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            errors.append("context-management/scripts/context_ops.py --help failed")
    else:
        errors.append("context-management/scripts/context_ops.py is missing")

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        print(f"validation failed: {len(errors)} issue(s)", file=sys.stderr)
        return 1

    print(f"validated {len(skills)} skill(s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate custom Codex skill metadata and local links.")
    parser.add_argument("repo", nargs="?", default=".", help="Repository path.")
    args = parser.parse_args()
    return validate(repo_root_from(Path(args.repo)))


if __name__ == "__main__":
    raise SystemExit(main())
