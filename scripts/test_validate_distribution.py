#!/usr/bin/env python3
"""Regression fixtures for the distribution release contract."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_distribution", ROOT / "scripts" / "validate_distribution.py"
)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class DistributionContractTest(unittest.TestCase):
    def fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for relative in ("catalogs", "bundle", "extensions", "workflows"):
            shutil.copytree(ROOT / relative, root / relative)
        return root

    def test_repository_contract_is_valid(self) -> None:
        self.assertEqual(validator.validate(ROOT), [])

    def test_workflow_catalog_requires_must_match_yaml(self) -> None:
        root = self.fixture()
        catalog_path = root / "catalogs" / "workflows.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        catalog["workflows"]["feature-delivery"]["requires"] = {
            "speckit_version": ">=0.16.4"
        }
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        errors = validator.validate(root)
        self.assertTrue(
            any("feature-delivery: requires" in error for error in errors), errors
        )

    def test_bundle_component_version_must_match_catalog(self) -> None:
        root = self.fixture()
        bundle_path = root / "bundle" / "bundle.yml"
        bundle = yaml.safe_load(bundle_path.read_text(encoding="utf-8"))
        bundle["provides"]["workflows"][0]["version"] = "9.9.9"
        bundle_path.write_text(yaml.safe_dump(bundle), encoding="utf-8")
        errors = validator.validate(root)
        self.assertTrue(
            any("workflow 'feature-delivery'" in error for error in errors), errors
        )

    def test_release_urls_must_match_expected_version(self) -> None:
        root = self.fixture()
        errors = validator.validate(root, expected_version="9.9.9")
        self.assertTrue(any("catalog_url" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
