#!/usr/bin/env python3
"""Small deterministic helpers for the context-management skill."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path


DEFAULT_FILES = (
    "index.md",
    "source-priority.md",
    "project-baseline.md",
    "working-conventions.md",
    "active-assumptions.md",
)

NOISE_PATTERNS = (
    r"\bTODO\b",
    r"\bFIXME\b",
    r"\bTBD\b",
    r"\bchangelog\b",
    r"\bsession summar(?:y|ies)\b",
    r"\bcompleted task",
    r"\bwhat just happened\b",
    r"\bwe (changed|fixed|added|removed|updated)\b",
    r"\bprevious(?:ly)?\b",
    r"\bold version\b",
    r"\blast session\b",
    r"\btoday\b",
)

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md(?:#[^)]+)?)\)")
CODE_MD_RE = re.compile(r"`([^`]+\.md(?:#[^`]*)?)`")


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def contexts_dir(repo: Path) -> Path:
    return repo / ".agents" / "contexts"


def init_context(repo: Path, overwrite: bool) -> int:
    repo = repo.resolve()
    target_dir = contexts_dir(repo)
    template_dir = skill_root() / "assets" / "contexts"
    target_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0
    for name in DEFAULT_FILES:
        source = template_dir / name
        target = target_dir / name
        if target.exists() and not overwrite:
            print(f"skip existing {target}")
            skipped += 1
            continue
        shutil.copyfile(source, target)
        print(f"write {target}")
        created += 1

    legacy = repo / ".agents" / "context.md"
    if legacy.exists():
        print(f"legacy context found, not migrated automatically: {legacy}")

    print(f"done: {created} written, {skipped} skipped")
    return 0


def iter_markdown_files(root: Path):
    if not root.exists():
        return
    yield from sorted(root.rglob("*.md"))


def find_noise(root: Path, repo: Path) -> list[tuple[Path, int, str, str]]:
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in NOISE_PATTERNS]
    findings: list[tuple[Path, int, str, str]] = []
    for path in iter_markdown_files(root):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for pattern in compiled:
                match = pattern.search(line)
                if match:
                    rel = path.relative_to(repo.resolve())
                    findings.append((rel, lineno, match.group(0), line.strip()))
                    break
    return findings


def scan_context(repo: Path) -> int:
    repo = repo.resolve()
    root = contexts_dir(repo)
    if not root.exists():
        print(f"missing context directory: {root}", file=sys.stderr)
        return 2

    findings = find_noise(root, repo)
    for rel, lineno, match, line in findings:
        print(f"{rel}:{lineno}: {match} :: {line}")

    if findings:
        print(f"found {len(findings)} possible context hygiene issue(s)")
        return 1

    print("no obvious changelog-style context noise found")
    return 0


def strip_anchor(reference: str) -> str:
    return reference.split("#", 1)[0].strip().strip("<>")


def referenced_markdown_files(index_text: str) -> set[str]:
    refs: set[str] = set()
    for pattern in (MARKDOWN_LINK_RE, CODE_MD_RE):
        for match in pattern.finditer(index_text):
            reference = strip_anchor(match.group(1))
            if reference and not reference.startswith(("http://", "https://", "mailto:", "#")):
                refs.add(reference)
    return refs


def resolve_context_reference(repo: Path, root: Path, reference: str) -> Path:
    path = Path(reference)
    if path.is_absolute():
        return path
    if path.parts[:2] == (".agents", "contexts"):
        return repo / path
    return root / path


def validate_context(repo: Path) -> int:
    repo = repo.resolve()
    root = contexts_dir(repo)
    errors: list[str] = []
    warnings: list[str] = []

    if not root.exists():
        print(f"missing context directory: {root}", file=sys.stderr)
        return 2

    index = root / "index.md"
    if not index.exists():
        errors.append(f"missing required file: {index.relative_to(repo)}")
        index_text = ""
    else:
        index_text = index.read_text(encoding="utf-8")

    for name in DEFAULT_FILES:
        path = root / name
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(repo)}")

    if index_text:
        for reference in sorted(referenced_markdown_files(index_text)):
            target = resolve_context_reference(repo, root, reference)
            if not target.exists():
                errors.append(
                    f"index references missing file: {reference} "
                    f"(resolved to {target.relative_to(repo) if target.is_relative_to(repo) else target})"
                )

    noise = find_noise(root, repo)
    for rel, lineno, match, line in noise:
        warnings.append(f"{rel}:{lineno}: review '{match}' :: {line}")

    for message in errors:
        print(f"error: {message}", file=sys.stderr)
    for message in warnings:
        print(f"warning: {message}")

    if errors:
        print(f"validation failed: {len(errors)} structural issue(s)", file=sys.stderr)
        return 2
    if warnings:
        print(f"validation found {len(warnings)} hygiene warning(s)")
        return 1

    print("context validation passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Context management helper operations.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create minimal .agents/contexts files.")
    init_parser.add_argument("repo", nargs="?", default=".", help="Repository path.")
    init_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing context files.")

    scan_parser = subparsers.add_parser("scan", help="Scan .agents/contexts for changelog-like noise.")
    scan_parser.add_argument("repo", nargs="?", default=".", help="Repository path.")

    validate_parser = subparsers.add_parser("validate", help="Validate .agents/contexts structure.")
    validate_parser.add_argument("repo", nargs="?", default=".", help="Repository path.")

    args = parser.parse_args()
    repo = Path(args.repo)

    if args.command == "init":
        return init_context(repo, args.overwrite)
    if args.command == "scan":
        return scan_context(repo)
    if args.command == "validate":
        return validate_context(repo)

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
