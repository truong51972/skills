#!/usr/bin/env python3
"""Deterministic linter for production system/developer prompts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    line: int | None = None


PLACEHOLDER_PATTERNS = [
    (r"\[REPLACE(?:\:|\])", "UNRESOLVED_REPLACE", "Unresolved [REPLACE] annotation."),
    (r"\[(?:Paste|TODO|TBD)\b[^\]]*\]", "UNRESOLVED_PLACEHOLDER", "Unresolved authoring placeholder."),
]

ANNOTATION_PATTERNS = [
    (r"^\s*(?:>\s*)?NOTE\s*:", "AUTHOR_NOTE", "Author NOTE annotation remains in runtime prompt."),
    (r"^\s*(?:>\s*)?OPTIONAL\s*:", "AUTHOR_OPTIONAL", "Author OPTIONAL annotation remains in runtime prompt."),
    (r"^\s*(?:>\s*)?EXAMPLE\s*:", "AUTHOR_EXAMPLE", "Author EXAMPLE annotation remains in runtime prompt."),
    (r"<!--.*?-->", "HTML_COMMENT", "HTML authoring comment remains in runtime prompt."),
]

WARNING_PATTERNS = [
    (
        r"\b(?:show|reveal|provide|output|write)\b.{0,40}\b(?:chain[- ]of[- ]thought|internal scratchpad|private reasoning)\b",
        "CHAIN_OF_THOUGHT_REQUEST",
        "Prompt appears to request internal chain-of-thought.",
    ),
    (
        r"\b(?:world[- ]class|top[- ]tier|leading|best)\s+(?:expert|specialist|professional)\b",
        "GENERIC_EXPERT_ROLE",
        "Generic prestige role detected; prefer an observable responsibility.",
    ),
    (
        r"\b(?:analyze carefully|think carefully|ensure high quality|be accurate)\b",
        "VAGUE_QUALITY_RULE",
        "Vague quality instruction detected; replace with observable criteria.",
    ),
]


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def find_patterns(
    text: str,
    patterns: Iterable[tuple[str, str, str]],
    severity: str,
    flags: int = re.IGNORECASE | re.MULTILINE | re.DOTALL,
) -> list[Finding]:
    findings: list[Finding] = []
    for pattern, code, message in patterns:
        for match in re.finditer(pattern, text, flags):
            findings.append(
                Finding(
                    severity=severity,
                    code=code,
                    message=message,
                    line=line_number(text, match.start()),
                )
            )
    return findings


def xml_tag_findings(text: str) -> list[Finding]:
    """Perform a light balance check for simple XML-style runtime tags."""
    findings: list[Finding] = []
    # Only treat standalone XML-style lines as runtime container tags.
    # Inline references such as `<Specs>` in prose are not container openings.
    token_re = re.compile(
        r"(?m)^\s*(</?([A-Za-z][A-Za-z0-9_-]*)\b[^>]*>)\s*$"
    )
    stacks: dict[str, list[int]] = {}

    for match in token_re.finditer(text):
        token = match.group(1)
        name = match.group(2)
        if token.endswith("/>"):
            continue
        if token.startswith("</"):
            if stacks.get(name):
                stacks[name].pop()
            else:
                findings.append(
                    Finding(
                        severity="error",
                        code="UNMATCHED_XML_CLOSE",
                        message=f"Closing tag </{name}> has no matching opening tag.",
                        line=line_number(text, match.start()),
                    )
                )
        else:
            stacks.setdefault(name, []).append(line_number(text, match.start()))

    for name, lines in stacks.items():
        for line in lines:
            findings.append(
                Finding(
                    severity="error",
                    code="UNCLOSED_XML_TAG",
                    message=f"Opening tag <{name}> is not closed.",
                    line=line,
                )
            )
    return findings


def duplicate_heading_findings(text: str) -> list[Finding]:
    headings: dict[str, int] = {}
    findings: list[Finding] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", line)
        if not match:
            continue
        normalized = re.sub(r"\s+", " ", match.group(1).strip().lower())
        if normalized in headings:
            findings.append(
                Finding(
                    severity="warning",
                    code="DUPLICATE_HEADING",
                    message=f"Duplicate heading: {match.group(1).strip()}",
                    line=idx,
                )
            )
        else:
            headings[normalized] = idx
    return findings


def structural_warnings(text: str) -> list[Finding]:
    findings: list[Finding] = []
    heading_count = len(re.findall(r"^\s{0,3}#{1,6}\s+", text, re.MULTILINE))
    if heading_count > 12:
        findings.append(
            Finding(
                severity="warning",
                code="TOO_MANY_SECTIONS",
                message=f"Prompt has {heading_count} headings; consider removing or modularizing sections.",
            )
        )

    if len(text.split()) > 1800:
        findings.append(
            Finding(
                severity="warning",
                code="LARGE_PROMPT",
                message="Prompt exceeds 1,800 words; verify that all sections are required at runtime.",
            )
        )

    has_data_tag = bool(re.search(r"<Data\b", text, re.IGNORECASE))
    has_data_boundary = bool(
        re.search(
            r"(?:data|content).{0,80}(?:not\s+(?:an\s+)?instruction|untrusted)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
    )
    if has_data_tag and not has_data_boundary:
        findings.append(
            Finding(
                severity="warning",
                code="MISSING_DATA_BOUNDARY",
                message="Prompt uses <Data> but does not clearly state that data is not instruction.",
            )
        )

    structured_markers = bool(
        re.search(
            r"(?:structured output|response schema|pydantic|json schema|provider-native)",
            text,
            re.IGNORECASE,
        )
    )
    absence_markers = bool(
        re.search(
            r"(?:unknown|not[- ]applicable|insufficient evidence|empty (?:list|result)|absence|missing information)",
            text,
            re.IGNORECASE,
        )
    )
    extraction_markers = bool(re.search(r"(?:extract|classification|relationship|entity)", text, re.IGNORECASE))
    if structured_markers and extraction_markers and not absence_markers:
        findings.append(
            Finding(
                severity="warning",
                code="MISSING_ABSENCE_BEHAVIOR",
                message="Structured extraction prompt does not appear to define absence or insufficient-evidence behavior.",
            )
        )

    tool_markers = bool(
        re.search(
            r"(?:^#{1,6}\s+.*tool|<AvailableTools>|use (?:the )?available tools|call (?:a |the )?tool|tool policy)",
            text,
            re.IGNORECASE | re.MULTILINE,
        )
    )
    failure_markers = bool(
        re.search(r"(?:tool failure|tool error|retry|stop condition|failed result|empty.*tool result)", text, re.IGNORECASE)
    )
    if tool_markers and not failure_markers:
        findings.append(
            Finding(
                severity="warning",
                code="MISSING_TOOL_FAILURE_POLICY",
                message="Tool-oriented prompt does not appear to define failure or stop behavior.",
            )
        )
    return findings


def lint_text(text: str) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(find_patterns(text, PLACEHOLDER_PATTERNS, "error"))
    findings.extend(find_patterns(text, ANNOTATION_PATTERNS, "error"))
    findings.extend(find_patterns(text, WARNING_PATTERNS, "warning"))
    findings.extend(xml_tag_findings(text))
    findings.extend(duplicate_heading_findings(text))
    findings.extend(structural_warnings(text))
    return sorted(findings, key=lambda f: (f.line is None, f.line or 0, f.severity, f.code))


def render_text(path: Path, findings: list[Finding]) -> str:
    if not findings:
        return f"{path}: OK"

    lines = [f"{path}: {len(findings)} finding(s)"]
    for item in findings:
        location = f":{item.line}" if item.line is not None else ""
        lines.append(f"  {item.severity.upper():7} {item.code}{location} - {item.message}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Prompt files to lint.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero for warnings as well as errors.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    all_results: list[dict[str, object]] = []
    has_error = False
    has_warning = False

    for path in args.paths:
        if not path.exists() or not path.is_file():
            finding = Finding("error", "FILE_NOT_FOUND", "File does not exist.")
            findings = [finding]
        else:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                findings = [Finding("error", "INVALID_UTF8", "File is not valid UTF-8.")]
            else:
                findings = lint_text(text)

        has_error = has_error or any(f.severity == "error" for f in findings)
        has_warning = has_warning or any(f.severity == "warning" for f in findings)
        all_results.append({"path": str(path), "findings": [asdict(f) for f in findings]})

        if args.format == "text":
            print(render_text(path, findings))

    if args.format == "json":
        print(json.dumps(all_results, ensure_ascii=False, indent=2))

    if has_error or (args.strict and has_warning):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
