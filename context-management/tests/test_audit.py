from __future__ import annotations

import os
import subprocess
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

            self.assertEqual(code, 0)
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

            self.assertEqual(code, 0)
            findings = data["findings"]
            self.assertEqual(len([f for f in findings if f["code"] == "MISSING_SOURCE_PATH"]), 1)

    def test_oversized_index_and_shard_warn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            context_dir = repo / ".agents" / "contexts"
            write(context_dir / "index.md", "x" * 4100)
            write(context_dir / "big.md", "y" * 16050)
            write(context_dir / "medium.md", "z" * 10000)

            code, data, _output = run_context_ops(repo, "audit")

            self.assertEqual(code, 0)
            self.assertGreaterEqual(
                [finding["code"] for finding in data["findings"]].count("SHARD_SIZE_WARNING"),
                2,
            )
            size_files = {
                finding["file"]
                for finding in data["findings"]
                if finding["code"] == "SHARD_SIZE_WARNING"
            }
            self.assertNotIn(".agents/contexts/medium.md", size_files)
            self.assertNotIn("TOTAL_SIZE_WARNING", {f["code"] for f in data["findings"]})

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

            self.assertEqual(code, 0)
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
            code, data, _output = run_context_ops(repo, "audit")
            self.assertEqual(code, 0)
            self.assertEqual(data["summary"]["warnings"], 1)

            strict_code, strict_data, _output = run_context_ops(repo, "audit", "json", "--strict")
            self.assertEqual(strict_code, 1)
            self.assertEqual(strict_data.keys(), data.keys())

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            code, _data, _output = run_context_ops(repo, "audit")
            self.assertEqual(code, 2)

    def test_eager_task_bundle_warns_but_single_shard_route_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            context_dir = repo / ".agents" / "contexts"
            write(
                context_dir / "index.md",
                "## Shards\n\n- `a.md`: a\n- `b.md`: b\n\n"
                "## Loading Policy\n\n"
                "- For backend work, load `a.md` and `b.md`.\n"
                "- For docs work, load only `a.md`.\n",
            )
            write(context_dir / "a.md", "# A\n")
            write(context_dir / "b.md", "# B\n")

            code, data, output = run_context_ops(repo, "audit")

            self.assertEqual(code, 0, output)
            eager = [f for f in data["findings"] if f["code"] == "EAGER_SHARD_BUNDLE"]
            self.assertEqual(len(eager), 1)
            self.assertEqual(eager[0]["details"]["references"], ["a.md", "b.md"])

    def test_section_identifier_density_exempts_routing_files(self) -> None:
        exact = " ".join(f"`service_{i}`" for i in range(12))
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            context_dir = repo / ".agents" / "contexts"
            write(context_dir / "index.md", "## Shards\n\n- `detail.md`: detail\n")
            write(context_dir / "detail.md", f"# Baseline\n\n{exact}\n")

            _code, data, _output = run_context_ops(repo, "audit")
            dense = [f for f in data["findings"] if f["code"] == "POSSIBLE_SOURCE_DETAIL_DUPLICATION"]
            self.assertEqual(len(dense), 1)

            write(context_dir / "detail.md", "# Baseline\n\nDurable architecture boundary.\n")
            write(context_dir / "source-priority.md", f"# Routes\n\n{exact}\n")
            write(
                context_dir / "index.md",
                "## Shards\n\n- `detail.md`: detail\n- `source-priority.md`: routes\n",
            )
            _code, data, _output = run_context_ops(repo, "audit")
            dense = [f for f in data["findings"] if f["code"] == "POSSIBLE_SOURCE_DETAIL_DUPLICATION"]
            self.assertEqual(dense, [])

    def test_local_markdown_links_resolve_from_containing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            context_dir = repo / ".agents" / "contexts"
            write(repo / "docs" / "architecture.md", "# Architecture\n")
            write(context_dir / "index.md", "## Shards\n\n- `detail.md`: detail\n")
            write(
                context_dir / "detail.md",
                "[Broken source](docs/architecture.md) and "
                "[valid source](../../docs/architecture.md).\n",
            )

            _code, data, _output = run_context_ops(repo, "audit")
            broken = [f for f in data["findings"] if f["code"] == "LOCAL_LINK_TARGET_MISSING"]
            self.assertEqual(len(broken), 1)
            self.assertEqual(broken[0]["details"]["target"], "docs/architecture.md")

    def test_generic_agent_runtime_guidance_warns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write(
                repo / ".agents" / "contexts" / "index.md",
                "Network access is restricted. Never delete untracked files.\n",
            )

            _code, data, _output = run_context_ops(repo, "audit")
            generic = [f for f in data["findings"] if f["code"] == "GENERIC_AGENT_RULE"]
            self.assertEqual(len(generic), 1)

    def test_git_commit_and_dirty_mtime_are_drift_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            write(repo / "source.txt", "committed\n")
            subprocess.run(["git", "add", "source.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "source"], cwd=repo, check=True)
            write(repo / ".agents" / "contexts" / "index.md", "# Index\n")
            old = 1_000_000_000
            os.utime(repo / ".agents" / "contexts" / "index.md", (old, old))
            write(repo / "source.txt", "dirty\n")

            _code, data, _output = run_context_ops(repo, "audit")
            drift = [f for f in data["findings"] if f["code"] == "SOURCE_CHANGED_SINCE_CONTEXT"]
            self.assertEqual(len(drift), 1)
            self.assertTrue(drift[0]["details"]["newer_commits"])
            self.assertEqual(drift[0]["details"]["newer_dirty_tracked_files"], ["source.txt"])
            self.assertEqual(drift[0]["details"]["semantic_verification"], "not_performed")

    def test_git_unavailable_is_info_and_does_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            write(repo / ".agents" / "contexts" / "index.md", "# Index\n")

            code, data, output = run_context_ops(repo, "audit", env={"PATH": "/nonexistent"})

            self.assertEqual(code, 0, output)
            info = [f for f in data["findings"] if f["code"] == "GIT_UNAVAILABLE"]
            self.assertEqual(len(info), 1)
            self.assertEqual(info[0]["severity"], "info")


if __name__ == "__main__":
    unittest.main()
