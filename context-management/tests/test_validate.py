from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import init_repo, run_context_ops, write


class ValidateTests(unittest.TestCase):
    def test_default_initialized_layout_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)

            code, data, output = run_context_ops(repo, "validate")

            self.assertEqual(code, 0, output)
            self.assertEqual(data["summary"]["errors"], 0)
            self.assertEqual(data["summary"]["warnings"], 0)

    def test_missing_referenced_shard_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write(repo / ".agents" / "contexts" / "index.md", "## Shards\n\n- `missing.md`: missing\n")

            code, data, _output = run_context_ops(repo, "validate")

            self.assertEqual(code, 2)
            self.assertEqual(data["findings"][0]["code"], "BROKEN_REFERENCE")

    def test_missing_index_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".agents" / "contexts").mkdir(parents=True)

            code, data, _output = run_context_ops(repo, "validate")

            self.assertEqual(code, 2)
            self.assertEqual(data["findings"][0]["code"], "STRUCTURE_ERROR")

    def test_orphan_shard_warns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            context_dir = repo / ".agents" / "contexts"
            write(context_dir / "index.md", "## Shards\n\n- `kept.md`: kept\n")
            write(context_dir / "kept.md", "# Kept\n")
            write(context_dir / "orphan.md", "# Orphan\n")

            code, data, _output = run_context_ops(repo, "validate")

            self.assertEqual(code, 1)
            self.assertIn("ORPHAN_SHARD", {finding["code"] for finding in data["findings"]})

    def test_shard_cannot_escape_context_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            context_dir = repo / ".agents" / "contexts"
            write(context_dir / "index.md", "## Shards\n\n- `../escaped.md`: escaped\n")
            
            code, data, _output = run_context_ops(repo, "validate")
            self.assertEqual(code, 2)
            self.assertEqual(data["findings"][0]["code"], "CONTEXT_REFERENCE_ESCAPE")
            
    def test_source_markdown_reference_is_not_a_shard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            context_dir = repo / ".agents" / "contexts"
            # Reference a source markdown file outside of Shards section
            write(context_dir / "index.md", "Read `docs/architecture.md`.\n\n## Shards\n\n- `a.md`: a\n")
            write(context_dir / "a.md", "# A\n")
            (repo / "docs").mkdir(parents=True)
            write(repo / "docs" / "architecture.md", "# Arch\n")
            
            code, data, output = run_context_ops(repo, "validate")
            # Should pass structure validation without BROKEN_REFERENCE or ESCAPE since it's not in ## Shards
            self.assertEqual(code, 0, output)

    def test_custom_layout_passes_without_optional_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            context_dir = repo / ".agents" / "contexts"
            write(context_dir / "index.md", "## Shards\n\n- `custom.md`: custom\n")
            write(context_dir / "custom.md", "# Custom\n")

            code, data, output = run_context_ops(repo, "validate")

            self.assertEqual(code, 0, output)
            self.assertEqual(data["summary"]["errors"], 0)

    def test_duplicate_index_reference_warns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            context_dir = repo / ".agents" / "contexts"
            write(
                context_dir / "index.md",
                "## Shards\n\n- `a.md`: first\n- `a.md`: duplicate\n",
            )
            write(context_dir / "a.md", "# A\n")

            code, data, _output = run_context_ops(repo, "validate")

            self.assertEqual(code, 1)
            self.assertIn("DUPLICATE_CONTENT_WARNING", {finding["code"] for finding in data["findings"]})


if __name__ == "__main__":
    unittest.main()
