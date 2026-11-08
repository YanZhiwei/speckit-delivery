#!/usr/bin/env python3
"""Contract tests for the Docs Sync README structure guard."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "extensions" / "docs-sync" / "scripts" / "readme_structure.py"
SPEC = importlib.util.spec_from_file_location("readme_structure", GUARD)
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


README = """# Project

Intro paragraph.

## Contents

- [Quick start](#quick-start)
- [Documentation map](#documentation-map)

## Quick start

```bash
make start
```

## Documentation map

| Document | Contents |
| --- | --- |
| [quality](docs/quality.md) | Quality commands |
"""


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class GuardTest(unittest.TestCase):
    def run_guard(self, *arguments: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(GUARD), *arguments],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        write(root / "README.md", README)
        write(root / "docs" / "quality.md", "# Quality\n\nCommands.\n")
        return root

    def git(self, root: Path, *arguments: str) -> None:
        result = subprocess.run(
            ["git", *arguments],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def commit_all(self, root: Path, message: str = "base") -> None:
        self.git(root, "init", "-q")
        self.git(root, "add", "-A")
        self.git(
            root,
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            message,
        )

    def test_repository_readmes_pass(self) -> None:
        result = self.run_guard(
            "README.md", "README.en.md", "--max-lines", "220", "--docs-root", "docs",
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("README_STRUCTURE: pass", result.stdout)

    def test_duplicate_heading_blocks(self) -> None:
        text = README + "\n## Quick start\n\nAgain.\n"
        problems = guard.check_structure(Path("README.md"), text, None, None, None)
        self.assertTrue(any("duplicate heading" in problem for problem in problems), problems)

    def test_section_missing_from_contents_blocks(self) -> None:
        text = README.replace(
            "- [Documentation map](#documentation-map)\n", ""
        )
        problems = guard.check_structure(Path("README.md"), text, None, None, None)
        self.assertTrue(
            any("missing from the table of contents" in problem for problem in problems),
            problems,
        )

    def test_contents_entry_must_resolve(self) -> None:
        text = README.replace(
            "- [Quick start](#quick-start)",
            "- [Quick start](#quick-start)\n- [Removed](#removed-section)",
        )
        problems = guard.check_structure(Path("README.md"), text, None, None, None)
        self.assertTrue(
            any("does not resolve to a heading" in problem for problem in problems),
            problems,
        )

    def test_release_anchored_prose_blocks(self) -> None:
        text = README + "\n从 `0.4.2` 起, this is a release note.\n"
        problems = guard.check_structure(Path("README.md"), text, None, None, None)
        self.assertTrue(
            any("belongs in the changelog" in problem for problem in problems), problems
        )

    def test_budget_names_the_split_target(self) -> None:
        problems = guard.check_structure(Path("README.md"), README, 5, None, "docs")
        self.assertTrue(
            any("docs/<topic>.md" in problem for problem in problems), problems
        )

    def test_broken_local_link_blocks(self) -> None:
        text = README.replace("docs/quality.md", "docs/missing.md")
        problems = guard.check_structure(
            Path("/tmp/README.md"), text, None, None, None
        )
        self.assertTrue(any("does not resolve" in problem for problem in problems), problems)

    def test_section_whitelist_blocks_a_new_section(self) -> None:
        text = README + "\n## Extras\n\nMore.\n"
        problems = guard.check_structure(
            Path("README.md"), text, None, ["Contents", "Quick start", "Documentation map"], None
        )
        self.assertTrue(
            any("instead of adding one" in problem for problem in problems), problems
        )

    def test_appending_a_section_at_the_end_blocks(self) -> None:
        root = self.fixture()
        self.commit_all(root)
        with (root / "README.md").open("a", encoding="utf-8") as handle:
            handle.write("\n## Release notes\n\n- v1 shipped.\n")
        result = self.run_guard("README.md", "--base", "HEAD", cwd=root)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("appended at the end of the file", result.stdout)

    def test_new_docs_page_must_be_registered(self) -> None:
        root = self.fixture()
        self.commit_all(root)
        write(root / "docs" / "operations.md", "# Operations\n\nDeploy.\n")
        result = self.run_guard(
            "README.md", "--base", "HEAD", "--docs-root", "docs", cwd=root
        )
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("is not registered in the README index", result.stdout)

        with (root / "README.md").open("a", encoding="utf-8") as handle:
            handle.write("| [operations](docs/operations.md) | Deploy |\n")
        result = self.run_guard(
            "README.md", "--base", "HEAD", "--docs-root", "docs", cwd=root
        )
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_splitting_detail_out_of_the_readme_passes(self) -> None:
        root = self.fixture()
        self.commit_all(root)
        readme = README.replace(
            "## Documentation map\n\n| Document | Contents |\n| --- | --- |\n"
            "| [quality](docs/quality.md) | Quality commands |\n",
            "## Documentation map\n\n| Document | Contents |\n| --- | --- |\n"
            "| [quality](docs/quality.md) | Quality commands |\n"
            "| [operations](docs/operations.md) | Deploy and rollback |\n",
        )
        write(root / "README.md", readme)
        write(root / "docs" / "operations.md", "# Operations\n\nDeploy and rollback.\n")
        result = self.run_guard(
            "README.md", "--base", "HEAD", "--docs-root", "docs", cwd=root
        )
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
