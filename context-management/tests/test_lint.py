from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import run_context_ops, write


class LintTests(unittest.TestCase):
    def test_changelog_and_session_history_phrases_warn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            context_dir = repo / ".agents" / "contexts"
            write(context_dir / "index.md", "# Index\n")
            write(context_dir / "notes.md", "We changed this today.\nSession summary follows.\n")

            code, data, _output = run_context_ops(repo, "lint")

            self.assertEqual(code, 1)
            self.assertGreaterEqual(data["summary"]["warnings"], 2)

    def test_durable_current_state_sentence_does_not_warn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write(
                repo / ".agents" / "contexts" / "index.md",
                "Source files are authoritative over context files.\n",
            )

            code, data, output = run_context_ops(repo, "lint")

            self.assertEqual(code, 0, output)
            self.assertEqual(data["summary"]["warnings"], 0)

    def test_large_code_fence_warns_but_single_identifier_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            fence = "```python\n" + "\n".join(f"line_{i} = {i}" for i in range(12)) + "\n```\n"
            write(repo / ".agents" / "contexts" / "index.md", f"One `workflow_run` identifier.\n{fence}")

            code, data, _output = run_context_ops(repo, "lint")

            self.assertEqual(code, 1)
            self.assertEqual(data["summary"]["warnings"], 1)
            self.assertEqual(data["findings"][0]["code"], "POSSIBLE_SOURCE_DETAIL_DUPLICATION")

    def test_scan_alias_matches_lint_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write(repo / ".agents" / "contexts" / "index.md", "TODO: remove this.\n")

            lint_code, lint_data, _ = run_context_ops(repo, "lint")
            scan_code, scan_data, _ = run_context_ops(repo, "scan")

            self.assertEqual(scan_code, lint_code)
            self.assertEqual(scan_data["summary"], lint_data["summary"])


if __name__ == "__main__":
    unittest.main()
