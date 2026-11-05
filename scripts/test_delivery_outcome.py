#!/usr/bin/env python3
"""Focused tests for the Delivery Close outcome writer."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from typing import Any
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
OUTCOME_PATH = ROOT / "extensions/delivery/scripts/delivery_outcome.py"
SPEC = importlib.util.spec_from_file_location("delivery_outcome_under_test", OUTCOME_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import setup failure
    raise RuntimeError(f"Cannot import {OUTCOME_PATH}")
OUTCOME = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OUTCOME)


class RuntimeStub:
    """The small read-only Runtime surface consumed by close_record."""

    def __init__(self, root: Path, run: str, lane: str = "lightweight") -> None:
        self.root = root.resolve()
        self.run = run
        self.directory = (self.root / ".specify" / "delivery" / run).resolve()
        self.local = self.directory / "runtime"
        self.state: dict[str, Any] = {
            "schema_version": 1,
            "delivery_run": run,
            "lane": lane,
        }

    def inside(self, value: str | Path) -> Path:
        raw = Path(value)
        path = raw if raw.is_absolute() else self.root / raw
        resolved = path.resolve()
        if not resolved.is_relative_to(self.root):
            raise ValueError(f"outside root: {value}")
        return resolved

    def relative(self, path: Path) -> str:
        return path.resolve().relative_to(self.root).as_posix()

    def load(self) -> dict[str, Any]:
        return copy.deepcopy(self.state)

    def git(self, *arguments: str) -> bytes:
        result = subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            capture_output=True,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
        if result.returncode:
            raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
        return result.stdout


class DeliveryOutcomeTest(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="delivery-outcome-")
        self.root = Path(self.temporary.name)
        self.git("init", "--quiet", "--initial-branch=main")
        self.git("config", "user.email", "delivery-outcome-tests@example.invalid")
        self.git("config", "user.name", "Delivery Outcome Tests")
        self.write("src/app.py", "VALUE = 1\n")
        self.write("README.md", "outcome test project\n")
        self.base = self.commit("initial project")
        self.git("checkout", "-b", "review")
        self.write("src/app.py", "VALUE = 2\n")
        self.reviewed = self.commit("reviewed change")
        self.git("checkout", "-B", "main", self.base)
        self.write("src/app.py", "VALUE = 2\n")
        self.merged = self.commit("squash merge pull request")
        self.runtime = RuntimeStub(self.root, "outcome-run")
        self.runtime.directory.mkdir(parents=True, exist_ok=True)
        self.runtime.local.mkdir(parents=True, exist_ok=True)
        self.evidence = self.runtime.directory / "evidence.md"
        self.evidence.write_text(
            "\n".join(
                [
                    "- **delivery_run**: outcome-run",
                    "- **lane**: lightweight",
                    "- **pull_request**: owner/repo#31",
                    f"- **reviewed_head**: {self.reviewed}",
                    "",
                    "## Validation snapshot — 2026-11-05",
                    f"- reviewed_head: {self.reviewed}",
                    "- limitation: CI was still awaited; the PR was not merged at this observation.",
                    "NATIVE_REVIEW_HEAD: " + self.reviewed,
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self.observed = self.runtime.local / "observed-pr.json"
        self.write_observation()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            text=True,
            capture_output=True,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
        if check and result.returncode:
            self.fail(
                "git command failed: "
                + " ".join(arguments)
                + f"\nstdout={result.stdout}\nstderr={result.stderr}"
            )
        return result

    def write(self, relative: str | Path, text: str) -> Path:
        path = self.root / Path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def commit(self, message: str) -> str:
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", message)
        return self.git("rev-parse", "HEAD").stdout.strip()

    def write_observation(self, **overrides: Any) -> None:
        value: dict[str, Any] = {
            "schema_version": 1,
            "delivery_run": "outcome-run",
            "lane": "lightweight",
            "provider": "github",
            "repository": "owner/repo",
            "number": 31,
            "state": "MERGED",
            "head_revision": self.reviewed,
            "base_revision": self.base,
            "merged_revision": self.merged,
            "merged_at": "2026-11-05T11:00:00Z",
            "observed_at": "2026-11-05T12:00:00Z",
            "url": "https://github.com/owner/repo/pull/31",
        }
        value.update(overrides)
        self.observed.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def call(self, *, outcome: str = "merged", verified: bool = True, pr: str = "31") -> dict[str, Any]:
        return OUTCOME.close_record(
            self.runtime,
            outcome,
            verified,
            pr,
            "runtime/observed-pr.json",
        )

    def test_clean_clone_old_sha_unreachable_uses_verified_tracker_mapping(self) -> None:
        # Keep the squashed/effective commit on main but remove every local ref
        # and reflog that could keep the original PR head alive.
        self.git("update-ref", "-d", "refs/heads/review")
        self.git("reflog", "expire", "--expire=now", "--all")
        self.git("gc", "--prune=now", "--quiet")
        self.assertNotEqual(
            self.git("cat-file", "-e", f"{self.reviewed}^{{commit}}", check=False).returncode,
            0,
        )

        result = self.call()

        self.assertEqual(result["merge_proof"], "tracker-head-mapped")
        self.assertEqual(result["reviewed_head"], self.reviewed)
        self.assertEqual(result["original_pr_head"], self.reviewed)
        self.assertEqual(result["merged_revision"], self.merged)
        current = self.evidence.read_text(encoding="utf-8")
        self.assertIn("DELIVERY_CURRENT_OUTCOME_BEGIN", current)
        self.assertIn(f"- **reviewed_head**: {self.reviewed}", current)
        self.assertIn(f"- **original_pr_head**: {self.reviewed}", current)
        self.assertIn(f"- **merged_revision**: {self.merged}", current)

    def test_clean_clone_can_use_an_exact_diff_archive(self) -> None:
        patch = self.runtime.git(
            "diff",
            "--no-ext-diff",
            "--no-renames",
            "--binary",
            "--full-index",
            self.base,
            self.reviewed,
            "--",
        )
        archive = self.runtime.local / "reviewed.patch"
        archive.write_bytes(patch)
        import hashlib

        self.evidence.write_text(
            self.evidence.read_text(encoding="utf-8")
            + "\n"
            + "\n".join(
                [
                    "- **reviewed_diff_archive**: runtime/reviewed.patch",
                    f"- **reviewed_diff_archive_sha256**: {hashlib.sha256(patch).hexdigest()}",
                    f"- **reviewed_diff_archive_base**: {self.base}",
                    f"- **reviewed_diff_archive_head**: {self.reviewed}",
                    f"- **reviewed_diff_archive_reviewed_head**: {self.reviewed}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.git("update-ref", "-d", "refs/heads/review")
        self.git("reflog", "expire", "--expire=now", "--all")
        self.git("gc", "--prune=now", "--quiet")

        result = self.call()

        self.assertEqual(result["merge_proof"], "evidence-archive")

    def test_malformed_or_unverified_observation_does_not_write(self) -> None:
        before_evidence = self.evidence.read_bytes()
        state_before = copy.deepcopy(self.runtime.state)
        malformed = json.loads(self.observed.read_text(encoding="utf-8"))
        del malformed["merged_revision"]
        self.observed.write_text(json.dumps(malformed) + "\n", encoding="utf-8")
        with self.assertRaises(OUTCOME.OutcomeError):
            self.call()
        self.assertEqual(self.evidence.read_bytes(), before_evidence)
        self.assertEqual(self.runtime.state, state_before)

        self.write_observation()
        with self.assertRaises(OUTCOME.OutcomeError):
            self.call(verified=False)
        self.assertEqual(self.evidence.read_bytes(), before_evidence)
        self.assertEqual(self.runtime.state, state_before)

        self.write_observation(state="CLOSED", merged_revision=None, merged_at=None)
        with self.assertRaises(OUTCOME.OutcomeError):
            self.call(outcome="merged")
        self.assertEqual(self.evidence.read_bytes(), before_evidence)
        self.assertEqual(self.runtime.state, state_before)

        self.write_observation()
        with self.assertRaises(OUTCOME.OutcomeError):
            self.call(outcome="closed")
        self.assertEqual(self.evidence.read_bytes(), before_evidence)
        self.assertEqual(self.runtime.state, state_before)

    def test_repeated_execution_is_idempotent(self) -> None:
        first = self.call()
        after_first = self.evidence.read_bytes()
        second = self.call()

        self.assertTrue(first["changed"])
        self.assertFalse(second["changed"])
        self.assertEqual(self.evidence.read_bytes(), after_first)
        self.assertEqual(first["reviewed_head"], second["reviewed_head"])

    def test_runtime_close_record_refreshes_observation_after_success(self) -> None:
        run = "runtime-close-run"
        runtime_module_path = ROOT / "extensions/delivery/scripts/delivery_runtime.py"
        runtime_spec = importlib.util.spec_from_file_location("runtime_close_integration", runtime_module_path)
        if runtime_spec is None or runtime_spec.loader is None:
            self.fail("Cannot load the Delivery runtime helper")
        runtime_module = importlib.util.module_from_spec(runtime_spec)
        exec(compile(runtime_module_path.read_bytes(), str(runtime_module_path), "exec"), runtime_module.__dict__)
        runtime = runtime_module.Runtime(self.root, run)
        runtime.init("lightweight")
        directory = runtime.directory
        local = runtime.local
        evidence = directory / "evidence.md"
        evidence.write_text(
            "\n".join(
                [
                    f"- **delivery_run**: {run}",
                    "- **lane**: lightweight",
                    "- **pull_request**: owner/repo#31",
                    f"- **reviewed_head**: {self.reviewed}",
                    "",
                    "Historical native review snapshot.\n",
                ]
            ),
            encoding="utf-8",
        )
        observed = {
            "schema_version": 1,
            "delivery_run": run,
            "lane": "lightweight",
            "provider": "github",
            "repository": "owner/repo",
            "number": 31,
            "state": "MERGED",
            "head_revision": self.reviewed,
            "base_revision": self.base,
            "merged_revision": self.merged,
            "merged_at": "2026-11-05T11:00:00Z",
            "observed_at": "2026-11-05T12:00:00Z",
            "url": "https://github.com/owner/repo/pull/31",
        }
        (local / "observed-pr.json").write_text(json.dumps(observed) + "\n", encoding="utf-8")
        result = runtime.close_record("merged", True, "31", "runtime/observed-pr.json")
        self.assertEqual(result["status"], "delivered")
        state = runtime.load()
        self.assertEqual(
            state["evidence_observation"]["sha256"],
            hashlib.sha256(evidence.read_bytes()).hexdigest(),
        )
        self.assertEqual(runtime.status()["status"], "delivered")

        before_evidence = evidence.read_bytes()
        before_state = runtime.path.read_bytes()
        observed["merged_revision"] = "0" * 40
        (local / "observed-pr.json").write_text(json.dumps(observed) + "\n", encoding="utf-8")
        with self.assertRaises(runtime_module.ProtocolError):
            runtime.close_record("merged", True, "31", "runtime/observed-pr.json")
        self.assertEqual(evidence.read_bytes(), before_evidence)
        self.assertEqual(runtime.path.read_bytes(), before_state)

    def test_module_cli_uses_the_same_close_record_contract(self) -> None:
        output = io.StringIO()
        with patch.object(OUTCOME, "_load_runtime", return_value=self.runtime):
            with contextlib.redirect_stdout(output):
                code = OUTCOME.main(
                    [
                        "close-record",
                        "--root",
                        str(self.root),
                        "--run",
                        "outcome-run",
                        "--outcome",
                        "merged",
                        "--pr",
                        "31",
                        "--verified",
                        "--file",
                        "runtime/observed-pr.json",
                    ]
                )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "delivered")

    def test_original_review_sha_and_historical_limitations_are_preserved(self) -> None:
        historical = self.evidence.read_text(encoding="utf-8")
        self.call()
        current = self.evidence.read_text(encoding="utf-8")

        self.assertIn("NATIVE_REVIEW_HEAD: " + self.reviewed, current)
        self.assertIn("CI was still awaited; the PR was not merged at this observation.", current)
        self.assertIn("Historical validation snapshots", current)
        self.assertIn(historical, current)
        self.assertNotIn(f"NATIVE_REVIEW_HEAD: {self.merged}", current)

    def test_unrelated_pull_request_is_rejected_without_write(self) -> None:
        before = self.evidence.read_bytes()
        self.evidence.write_text(
            self.evidence.read_text(encoding="utf-8").replace(
                "owner/repo#31", "owner/repo#30"
            ),
            encoding="utf-8",
        )
        before_conflict = self.evidence.read_bytes()
        with self.assertRaises(OUTCOME.OutcomeError):
            self.call(pr="31")
        self.assertEqual(self.evidence.read_bytes(), before_conflict)
        self.assertNotEqual(before, before_conflict)

    def test_publication_head_change_requires_explicit_binding(self) -> None:
        new_head = self.commit("unreviewed publication change")
        self.write_observation(head_revision=new_head)
        before = self.evidence.read_bytes()
        with self.assertRaises(OUTCOME.OutcomeError):
            self.call()
        self.assertEqual(self.evidence.read_bytes(), before)

    def test_merged_content_mismatch_is_rejected_without_write(self) -> None:
        self.write("src/app.py", "VALUE = 999\n")
        wrong_merge = self.commit("merge result with a different tree")
        self.write_observation(merged_revision=wrong_merge)
        before = self.evidence.read_bytes()
        with self.assertRaises(OUTCOME.OutcomeError):
            self.call()
        self.assertEqual(self.evidence.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
