from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import init_repo, run_context_ops, write


class AuditTests(unittest.TestCase):
    def test_lazy_loading_violations_warn_and_conditional_loading_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write(
                repo / ".agents" / "contexts" / "index.md",
                "Always read `source-priority.md` before every task.\nRead all context files first.\n\n## Shards\n\n- `source-priority.md`: src\n",
            )
            write(repo / ".agents" / "contexts" / "source-priority.md", "# Source\n")

            code, data, _output = run_context_ops(repo, "audit")

            self.assertEqual(code, 1)
            codes = [finding["code"] for finding in data["findings"]]
            self.assertGreaterEqual(codes.count("LAZY_LOADING_WARNING"), 2)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write(
                repo / ".agents" / "contexts" / "index.md",
                "Read `source-priority.md` only when source ownership matters.\n\n## Shards\n\n- `source-priority.md`: src\n",
            )
            write(repo / ".agents" / "contexts" / "source-priority.md", "# Source\n")

            code, data, output = run_context_ops(repo, "audit")

            self.assertEqual(code, 0, output)
            self.assertEqual(data["summary"]["warnings"], 0)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "apps").mkdir()
            write(
                repo / ".agents" / "contexts" / "index.md",
                "Missing `apps/missing.py`, URL `https://example.com/x.md`, command `python3`.\n",
            )

            code, data, _output = run_context_ops(repo, "audit")

            self.assertEqual(code, 1)
            findings = data["findings"]
            self.assertEqual(len([f for f in findings if f["code"] == "MISSING_SOURCE_PATH"]), 1)

    def test_oversized_index_and_shard_warn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            context_dir = repo / ".agents" / "contexts"
            write(context_dir / "index.md", "x" * 4100)
            write(context_dir / "big.md", "y" * 10050)

            code, data, _output = run_context_ops(repo, "audit")

            self.assertEqual(code, 1)
            self.assertGreaterEqual(
                [finding["code"] for finding in data["findings"]].count("SHARD_SIZE_WARNING"),
                2,
            )

    def test_duplicate_content_and_orphan_warn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            context_dir = repo / ".agents" / "contexts"
            duplicate = "This durable context sentence is intentionally long enough to be duplicated exactly.\n"
            write(context_dir / "index.md", "## Shards\n\n- `a.md`: a\n- `b.md`: b\n")
            write(context_dir / "a.md", duplicate)
            write(context_dir / "b.md", duplicate)
            write(context_dir / "orphan.md", "# Orphan\n")

            code, data, _output = run_context_ops(repo, "audit")

            self.assertEqual(code, 1)
            codes = {finding["code"] for finding in data["findings"]}
            self.assertIn("DUPLICATE_CONTENT_WARNING", codes)
            self.assertIn("ORPHAN_SHARD", codes)

    def test_json_schema_and_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)

            code, data, output = run_context_ops(repo, "audit")

            self.assertEqual(code, 0, output)
            self.assertEqual(data["schema_version"], 1)
            self.assertEqual(data["command"], "audit")
            self.assertEqual(data["semantic_source_verification"]["status"], "not_performed")

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write(repo / ".agents" / "contexts" / "index.md", "TODO\n")
            code, _data, _output = run_context_ops(repo, "audit")
            self.assertEqual(code, 1)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            code, _data, _output = run_context_ops(repo, "audit")
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
