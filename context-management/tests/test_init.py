from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import init_repo, run_context_ops, write


class InitTests(unittest.TestCase):
    def test_init_creates_default_layout_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo" / "nested"
            code, _data, output = run_context_ops(repo, "init")

            self.assertEqual(code, 0, output)
            context_dir = repo / ".agents" / "contexts"
            for name in (
                "index.md",
                "source-priority.md",
                "project-baseline.md",
                "working-conventions.md",
                "active-assumptions.md",
            ):
                self.assertTrue((context_dir / name).exists(), name)

            index = context_dir / "index.md"
            original = index.read_text(encoding="utf-8")
            code, _data, output = run_context_ops(repo, "init")
            self.assertEqual(code, 0, output)
            self.assertEqual(index.read_text(encoding="utf-8"), original)

    def test_init_does_not_overwrite_or_delete_custom_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            context_dir = repo / ".agents" / "contexts"
            write(context_dir / "index.md", "# Custom\n")
            write(context_dir / "custom.md", "# Custom shard\n")

            code, _data, output = run_context_ops(repo, "init")

            self.assertEqual(code, 0, output)
            self.assertEqual((context_dir / "index.md").read_text(encoding="utf-8"), "# Custom\n")
            self.assertTrue((context_dir / "custom.md").exists())


if __name__ == "__main__":
    unittest.main()
