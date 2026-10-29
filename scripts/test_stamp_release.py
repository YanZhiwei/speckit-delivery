#!/usr/bin/env python3
"""Regression tests for the release-stamping preflight."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
STAMP = ROOT / "scripts" / "stamp_release.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "validate_distribution", ROOT / "scripts" / "validate_distribution.py"
)
STAMP_SPEC = importlib.util.spec_from_file_location("stamp_release", STAMP)
assert VALIDATOR_SPEC and VALIDATOR_SPEC.loader
assert STAMP_SPEC and STAMP_SPEC.loader
validator = importlib.util.module_from_spec(VALIDATOR_SPEC)
stamp = importlib.util.module_from_spec(STAMP_SPEC)
VALIDATOR_SPEC.loader.exec_module(validator)
STAMP_SPEC.loader.exec_module(stamp)


class ReleaseStampTest(unittest.TestCase):
    def setUp(self) -> None:
        current = yaml.safe_load(
            (ROOT / "bundle" / "bundle.yml").read_text(encoding="utf-8")
        )["bundle"]["version"]
        # Keep the fixture different from the checkout so this test also runs
        # on an already-stamped release-preparation branch.
        self.target = "9.9.9" if current != "9.9.9" else "9.9.10"

    def fixture(self, *, with_changelog: bool = True) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for relative in ("bundle", "extensions", "workflows", "catalogs"):
            shutil.copytree(ROOT / relative, root / relative)
        for changelog in ("CHANGELOG.md", "CHANGELOG.zh-CN.md"):
            content = (ROOT / changelog).read_text(encoding="utf-8")
            if with_changelog:
                content += (
                    f"\n## [{self.target}] - 2026-01-01\n\nTest release notes.\n"
                )
            (root / changelog).write_text(content, encoding="utf-8")
        return root

    def run_stamp(
        self, root: Path, *arguments: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(STAMP), "--root", str(root), *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_stamp_updates_all_release_surfaces(self) -> None:
        root = self.fixture()
        result = self.run_stamp(root, "--version", self.target)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        bundle = yaml.safe_load(
            (root / "bundle" / "bundle.yml").read_text(encoding="utf-8")
        )
        self.assertEqual(bundle["bundle"]["version"], self.target)
        bug = next(
            item
            for item in bundle["provides"]["extensions"]
            if item["id"] == "bug"
        )
        self.assertEqual(bug["version"], "1.0.1")
        self.assertTrue(
            all(
                item["version"] == self.target
                for item in bundle["provides"]["extensions"]
                + bundle["provides"]["workflows"]
                if item["id"] != "bug"
            )
        )

        extension_catalog = json.loads(
            (root / "catalogs" / "extensions.json").read_text(encoding="utf-8")
        )
        for entry in extension_catalog["extensions"].values():
            self.assertEqual(entry["version"], self.target)
            self.assertIn(f"/v{self.target}/", entry["download_url"])
            self.assertTrue(entry["download_url"].endswith(f"-{self.target}.zip"))
            if entry.get("documentation"):
                self.assertIn(f"/v{self.target}/", entry["documentation"])

        workflow_catalog = json.loads(
            (root / "catalogs" / "workflows.json").read_text(encoding="utf-8")
        )
        for entry in workflow_catalog["workflows"].values():
            self.assertEqual(entry["version"], self.target)
            self.assertIn(f"/v{self.target}/", entry["url"])

        bundle_catalog = json.loads(
            (root / "catalogs" / "bundles.json").read_text(encoding="utf-8")
        )
        entry = bundle_catalog["bundles"]["speckit-delivery"]
        self.assertEqual(entry["version"], self.target)
        self.assertIn(f"/v{self.target}/", entry["download_url"])
        self.assertTrue(entry["download_url"].endswith(f"-{self.target}.zip"))

        self.assertEqual(validator.validate(root, self.target), [])

    def test_check_detects_unstamped_then_accepts_stamped(self) -> None:
        root = self.fixture()
        before = self.run_stamp(root, "--version", self.target, "--check")
        self.assertEqual(before.returncode, 1)
        self.assertIn("not stamped", before.stdout)

        stamped = self.run_stamp(root, "--version", self.target)
        self.assertEqual(stamped.returncode, 0, stamped.stdout + stamped.stderr)
        after = self.run_stamp(root, "--version", self.target, "--check")
        self.assertEqual(after.returncode, 0, after.stdout + after.stderr)

    def test_missing_changelog_section_fails_without_writing(self) -> None:
        root = self.fixture(with_changelog=False)
        before = (root / "bundle" / "bundle.yml").read_text(encoding="utf-8")
        result = self.run_stamp(root, "--version", self.target)
        self.assertEqual(result.returncode, 1)
        self.assertIn("release notes first", result.stdout)
        self.assertEqual(
            (root / "bundle" / "bundle.yml").read_text(encoding="utf-8"), before
        )

    def test_plan_uses_expected_tag(self) -> None:
        root = self.fixture()
        with self.assertRaisesRegex(
            ValueError, f"must be 'v{self.target}'"
        ):
            stamp.plan(root, self.target, "v9.9.8")


if __name__ == "__main__":
    unittest.main()
