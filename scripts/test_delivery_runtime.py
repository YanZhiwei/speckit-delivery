#!/usr/bin/env python3
"""Behavioral regression tests for the Delivery runtime coordinator.

These tests deliberately use only the standard library, Git, temporary project
roots, the imported helper, and the helper's real CLI subprocess.  Native owner
reports are represented by small files in the canonical run workspace; the
normalized result envelope always copies its identity from ``begin``.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "extensions/delivery/scripts/delivery_runtime.py"
SPEC = importlib.util.spec_from_file_location("delivery_runtime_under_test", HELPER_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import setup failure
    raise RuntimeError(f"Cannot import {HELPER_PATH}")
RUNTIME = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNTIME)


DIMENSIONS = {
    "requirements",
    "code_quality",
    "architecture",
    "correctness",
    "security_compatibility",
    "test_effectiveness",
}


def _temporary_parent() -> str | None:
    """Keep all temporary Git repositories in the approved test temp root."""

    value = os.environ.get("TMP") or os.environ.get("TEMP")
    return value or None


class DeliveryRuntimeTest(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory(
            prefix="delivery-runtime-", dir=_temporary_parent()
        )
        self.root = Path(self._temporary.name)
        self._counter = 0
        self.git("init", "--quiet")
        self.git("config", "user.email", "delivery-runtime-tests@example.invalid")
        self.git("config", "user.name", "Delivery Runtime Tests")
        self.write("src/app.py", "VALUE = 1\n")
        self.write("README.md", "temporary delivery runtime project\n")
        self.commit("initial project")

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def git(
        self, *arguments: str, check: bool = True, input_text: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            input=input_text,
            text=True,
            capture_output=True,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
        if check and result.returncode != 0:
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

    def relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def commit(self, message: str) -> str:
        self.git("add", "--all")
        self.git("commit", "--quiet", "-m", message)
        return self.git("rev-parse", "HEAD").stdout.strip()

    def cli(
        self,
        operation: str,
        run: str | None = None,
        *,
        expected: int | None = 0,
        **options: Any,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(HELPER_PATH),
            operation,
            "--root",
            str(self.root),
        ]
        if run is not None:
            command.extend(("--run", run))
        for name, value in options.items():
            if value is None or value is False:
                continue
            flag = "--" + name.replace("_", "-")
            if value is True:
                command.append(flag)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    command.extend((flag, str(item)))
            else:
                command.extend((flag, str(value)))
        result = subprocess.run(
            command,
            cwd=self.root,
            text=True,
            capture_output=True,
            env={
                **os.environ,
                "TMP": str(self.root),
                "TEMP": str(self.root),
            },
        )
        if expected is not None:
            self.assertEqual(
                result.returncode,
                expected,
                f"CLI {operation} stdout={result.stdout!r} stderr={result.stderr!r}",
            )
        return result

    def new_runtime(
        self,
        run: str,
        lane: str = "lightweight",
        bug_slug: str | None = None,
    ) -> Any:
        runtime = RUNTIME.Runtime(self.root, run)
        runtime.init(lane, bug_slug)
        return runtime

    def feature_runtime(
        self,
        run: str = "feature-run",
        *,
        tasks: str | None = None,
        commit_files: bool = True,
    ) -> tuple[Any, Path]:
        runtime = self.new_runtime(run, "feature")
        feature = self.root / ".specify" / "features" / run
        self.write(feature / "spec.md", "# Spec\n\nThe approved requirement.\n")
        self.write(feature / "plan.md", "# Plan\n\nThe approved design.\n")
        self.write(
            feature / "tasks.md",
            tasks
            or "# Tasks\n\n- [ ] T1 Implement the change\n- [X] T2 Verify the baseline\n",
        )
        if commit_files:
            self.commit(f"bind feature packet {run}")
        runtime.bind(self.relative(feature), None, [])
        return runtime, feature

    def reference(self, runtime: Any, path: Path) -> dict[str, str]:
        return {
            "path": runtime.relative(path),
            "sha256": RUNTIME.digest(path.read_bytes()),
        }

    def native_file(
        self, runtime: Any, directory: str, suffix: str, text: str
    ) -> Path:
        self._counter += 1
        path = runtime.directory / directory / f"{suffix}-{self._counter}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def result_file(
        self,
        runtime: Any,
        pending: dict[str, Any],
        verdict: str,
        data: dict[str, Any],
        *,
        report_text: str | None = None,
    ) -> Path:
        self._counter += 1
        report = runtime.local / "reports" / (
            f"{pending['stage']}-native-{self._counter}.yml"
        )
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            report_text or f"native {pending['stage']} report\n",
            encoding="utf-8",
        )
        data = json.loads(json.dumps(data))
        if pending["stage"] == "review" and verdict == "pass":
            stages = runtime.load()["stages"]
            if all(stage in stages for stage in ("quality", "standards")):
                data["dependencies"] = {
                    stage: {
                        key: stages[stage][key]
                        for key in ("stage", "ticket", "input_fingerprint", "verdict", "report", "native_receipt")
                    }
                    for stage in ("quality", "standards")
                }
        result = {
            "schema_version": pending["schema_version"],
            "delivery_run": pending["delivery_run"],
            "lane": pending["lane"],
            "stage": pending["stage"],
            "scope": pending.get("scope", "outgoing-diff"),
            "ticket": pending["ticket"],
            "input_fingerprint": pending["input_fingerprint"],
            "verdict": verdict,
            "report": self.reference(runtime, report),
            "data": data,
        }
        def evidence_references(value: Any) -> list[dict[str, str]]:
            if isinstance(value, dict):
                if set(value) == {"path", "sha256"}:
                    return [{"path": value["path"], "sha256": value["sha256"]}]
                return [item for child in value.values() for item in evidence_references(child)]
            if isinstance(value, list):
                return [item for child in value for item in evidence_references(child)]
            return []
        receipt = {
            "schema_version": 1,
            "receipt_type": "delivery-native-owner",
            **{key: result[key] for key in ("delivery_run", "lane", "stage", "scope", "ticket", "input_fingerprint", "verdict", "report")},
            "head": runtime.git("rev-parse", "HEAD").decode().strip() if pending["stage"] == "checkpoint" else pending["snapshot"]["head"],
            "evidence": evidence_references(data),
            "data": data,
        }
        receipt_path = runtime.local / f"native-{pending['stage']}-{pending['ticket']}.json"
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        result["native_receipt"] = self.reference(runtime, receipt_path)
        path = runtime.local / f"result-{pending['stage']}.json"
        path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return path

    def quality_data(
        self, runtime: Any, *, exit_code: int = 0, command: str = "native-check"
    ) -> dict[str, Any]:
        evidence = self.native_file(
            runtime, "checks", "quality-check", f"{command}: exit {exit_code}\n"
        )
        return {
            "checks": [
                {
                    "command": command,
                    "exit_code": exit_code,
                    "evidence": self.reference(runtime, evidence),
                }
            ]
        }

    def review_data(
        self,
        runtime: Any,
        *,
        coverage: str = "complete",
        dimensions: dict[str, str] | None = None,
        findings: list[dict[str, Any]] | None = None,
        repairable: bool = False,
        independence: str = "independent",
        acceptance: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "coverage": coverage,
            "dimensions": dimensions
            or {dimension: "pass" for dimension in DIMENSIONS},
            "findings": findings if findings is not None else [],
            "repairable": repairable,
            "independence": independence,
        }
        if acceptance is not None:
            data["acceptance"] = acceptance
        return data

    def record_pass_quality_and_standards(self, runtime: Any) -> None:
        quality = runtime.begin("quality")
        self.result_file(runtime, quality, "pass", self.quality_data(runtime))
        runtime.record("quality")

        standards = runtime.begin("standards")
        self.result_file(
            runtime,
            standards,
            "pass",
            {"coverage": "complete"},
        )
        runtime.record("standards")

    def record_pass_review(self, runtime: Any) -> dict[str, Any]:
        review = runtime.begin("review")
        self.result_file(
            runtime,
            review,
            "pass",
            self.review_data(runtime),
        )
        return runtime.record("review")

    def assert_blocked(self, callable_object: Any, *arguments: Any, **kwargs: Any) -> None:
        with self.assertRaises(RUNTIME.ProtocolError):
            callable_object(*arguments, **kwargs)

    def test_init_identity_collision_legacy_refusal_and_safe_ids(self) -> None:
        first = self.cli("init", "identity-run", lane="feature")
        first_status = json.loads(first.stdout)
        self.assertEqual(first_status["delivery_run"], "identity-run")
        self.assertEqual(first_status["lane"], "feature")

        same = self.cli("init", "identity-run", lane="feature")
        self.assertEqual(json.loads(same.stdout)["delivery_run"], "identity-run")
        self.assertEqual(
            self.cli("init", "identity-run", lane="bugfix", expected=1).returncode,
            1,
        )

        self.cli("init", "bug-mapped", lane="bugfix", bug_slug="bug-one")
        collision = self.cli(
            "init", "bug-mapped", lane="bugfix", bug_slug="bug-two", expected=1
        )
        self.assertIn("another lane/bug mapping", collision.stderr)

        for invalid in ("../escape", "a/b", "", ".", "bad\\path"):
            with self.subTest(invalid=invalid):
                result = self.cli("init", invalid, lane="lightweight", expected=1)
                self.assertIn("DELIVERY_RUNTIME: blocked", result.stderr)

        legacy = self.root / ".specify" / "delivery" / "legacy-run"
        legacy.mkdir(parents=True)
        (legacy / "evidence.md").write_text(
            "delivery_run: legacy-run\nlane: feature\nstatus: active\n",
            encoding="utf-8",
        )
        listed = json.loads(self.cli("status").stdout)
        legacy_status = next(item for item in listed if item["delivery_run"] == "legacy-run")
        self.assertEqual(legacy_status["status"], "active")
        self.assertIn("recover", legacy_status["next_action"])
        refused = self.cli("init", "legacy-run", lane="feature", expected=1)
        self.assertIn("Legacy or interrupted artifacts", refused.stderr)
        self.assertFalse((legacy / "runtime" / "state.json").exists())

    def test_init_preserves_info_exclude_and_ignores_only_runtime_bookkeeping(self) -> None:
        exclude_raw = self.git("rev-parse", "--git-path", "info/exclude").stdout.strip()
        exclude = Path(exclude_raw)
        if not exclude.is_absolute():
            exclude = self.root / exclude
        exclude.parent.mkdir(parents=True, exist_ok=True)
        existing = "# project-local rule\n/custom-existing-rule\n"
        exclude.write_text(existing, encoding="utf-8")

        runtime = self.new_runtime("ignore-scope")
        rule = "/.specify/delivery/ignore-scope/runtime/"
        exclude_text = exclude.read_text(encoding="utf-8")
        self.assertIn(existing, exclude_text)
        self.assertEqual(exclude_text.count(rule), 1)
        runtime.init("lightweight")
        self.assertEqual(exclude.read_text(encoding="utf-8").count(rule), 1)

        evidence = self.write(
            ".specify/delivery/ignore-scope/evidence.md",
            "delivery_run: ignore-scope\nlane: lightweight\n",
        )
        planning = self.write(
            ".specify/features/visible/plan.md", "approved planning artifact\n"
        )

        def ignored(path: Path) -> bool:
            return (
                self.git(
                    "check-ignore",
                    "--no-index",
                    "--quiet",
                    self.relative(path),
                    check=False,
                ).returncode
                == 0
            )

        self.assertTrue(ignored(runtime.path))
        self.assertFalse(ignored(evidence))
        self.assertFalse(ignored(planning))

    def test_pending_owner_ticket_invalidates_an_older_pass_for_needs_and_require(self) -> None:
        runtime = self.new_runtime("pending-over-pass", "lightweight")
        first = runtime.begin("quality")
        self.result_file(runtime, first, "pass", self.quality_data(runtime))
        runtime.record("quality")
        second = runtime.begin("quality")
        self.assertNotEqual(first["ticket"], second["ticket"])
        state = runtime.load()
        self.assertFalse(runtime.current(state, "quality", "pass"))
        self.assertTrue(runtime.needs("quality"))
        with self.assertRaises(RUNTIME.ProtocolError):
            runtime.require("quality")

    def test_status_and_resume_are_read_only_with_pending_owner_input(self) -> None:
        runtime = self.new_runtime("status-run")
        runtime.begin("review")
        state_before = runtime.path.read_bytes()
        files_before = {
            self.relative(path): path.read_bytes()
            for path in runtime.directory.rglob("*")
            if path.is_file()
        }

        status = self.cli("status", "status-run")
        resumed = self.cli("resume", "status-run")
        status_value = json.loads(status.stdout)
        resume_value = json.loads(resumed.stdout)
        self.assertEqual(status_value, resume_value)
        self.assertEqual(status_value["pending_stages"], ["review"])
        self.assertIn("pending owner result", status_value["next_action"])
        self.assertEqual(runtime.path.read_bytes(), state_before)
        files_after = {
            self.relative(path): path.read_bytes()
            for path in runtime.directory.rglob("*")
            if path.is_file()
        }
        self.assertEqual(files_after, files_before)

    def test_bind_requires_lane_exact_paths_and_rejects_traversal_and_symlinks(self) -> None:
        feature_runtime = self.new_runtime("bind-feature", "feature")
        feature = self.root / ".specify" / "features" / "actual-feature"
        for name in ("spec.md", "plan.md", "tasks.md"):
            self.write(feature / name, f"{name}\n")
        bindings = feature_runtime.bind(self.relative(feature), None, [])
        self.assertEqual(
            bindings["spec"], ".specify/features/actual-feature/spec.md"
        )
        self.assertEqual(
            bindings["plan"], ".specify/features/actual-feature/plan.md"
        )
        self.assertEqual(
            bindings["tasks"], ".specify/features/actual-feature/tasks.md"
        )
        self.assert_blocked(
            feature_runtime.bind,
            ".specify/features/a-different-feature",
            None,
            [],
        )

        non_feature = self.new_runtime("bind-lightweight", "lightweight")
        self.assert_blocked(
            non_feature.bind,
            ".specify/features/actual-feature",
            None,
            [],
        )

        bug_runtime = self.new_runtime("bind-bug", "bugfix", "bug-actual")
        assessment = self.write(
            ".specify/bugs/bug-actual/assessment.md", "official assessment\n"
        )
        self.assertEqual(
            bug_runtime.bind(None, self.relative(assessment), [])["assessment"],
            ".specify/bugs/bug-actual/assessment.md",
        )
        wrong_assessment = self.write(
            ".specify/bugs/other/assessment.md", "wrong assessment\n"
        )
        self.assert_blocked(
            bug_runtime.bind, None, self.relative(wrong_assessment), []
        )

        for invalid in ("../outside", "a/b", ""):
            with self.subTest(invalid=invalid):
                with self.assertRaises(RUNTIME.ProtocolError):
                    RUNTIME.Runtime(self.root, invalid)

        link_parent = self.root / ".specify" / "delivery"
        link_parent.mkdir(parents=True, exist_ok=True)
        link = link_parent / "inside-link"
        try:
            link.symlink_to(self.root / ".specify", target_is_directory=True)
        except (OSError, NotImplementedError):
            symlink_available = False
        else:
            symlink_available = True
        if symlink_available:
            try:
                with self.assertRaises(RUNTIME.ProtocolError):
                    feature_runtime.inside(
                        ".specify/delivery/inside-link/secret.txt"
                    )
            finally:
                link.unlink()

    def test_clarify_checklist_binding_allows_only_checkbox_mark_changes(self) -> None:
        runtime, feature = self.feature_runtime("clarify-checklist")
        checklist = feature / "checklists" / "requirements.md"
        checklist.parent.mkdir(parents=True, exist_ok=True)
        checklist.write_text("# Requirements\n\n- [ ] Keep the boundary\n", encoding="utf-8")
        runtime.bind(self.relative(feature), None, [])
        self.assertEqual(
            runtime.load()["bindings"]["clarification_checklist"],
            ".specify/features/clarify-checklist/checklists/requirements.md",
        )

        pending = runtime.begin("clarify")
        checklist.write_text("# Requirements\n\n- [x] Keep the boundary\n", encoding="utf-8")
        self.result_file(runtime, pending, "ready", {"needs_approval": False})
        runtime.record("clarify")

        pending = runtime.begin("clarify")
        checklist.write_text("# Requirements changed\n\n- [x] Keep the boundary\n", encoding="utf-8")
        self.result_file(runtime, pending, "ready", {"needs_approval": False})
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "checkbox"):
            runtime.record("clarify")

    def test_snapshot_preserves_index_modes_and_conflict_stages(self) -> None:
        runtime = self.new_runtime("index-identity", "lightweight")
        before = runtime.snapshot()
        self.git("update-index", "--chmod=+x", "src/app.py")
        executable_index = runtime.snapshot()
        self.assertNotEqual(before["fingerprint"], executable_index["fingerprint"])
        self.assertNotEqual(before["index"], executable_index["index"])
        self.git("update-index", "--chmod=-x", "src/app.py")

        self.write("conflict.txt", "base\n")
        base = self.commit("add conflict base")
        base_branch = self.git("branch", "--show-current").stdout.strip()
        self.git("checkout", "--quiet", "-b", "conflict-side")
        self.write("conflict.txt", "side\n")
        self.commit("side conflict")
        self.git("checkout", "--quiet", base_branch)
        self.write("conflict.txt", "main\n")
        self.commit("main conflict")
        merged = self.git("merge", "conflict-side", check=False)
        self.assertNotEqual(merged.returncode, 0)
        conflicted = runtime.snapshot()
        stages = [entry["stage"] for entry in conflicted["index"] if entry["path"] == "conflict.txt"]
        self.assertEqual(stages, [1, 2, 3])

    def test_snapshot_includes_untracked_ignored_bound_inputs_config_head_and_constitution(self) -> None:
        self.write(".gitignore", ".ignored-policy.yml\n")
        self.commit("configure ignored policy input")
        runtime, feature = self.feature_runtime("snapshot-run")
        ignored_input = self.write(".ignored-policy.yml", "ignored but bound\n")
        untracked = self.write("src/new_untracked.py", "VALUE = 2\n")
        constitution = self.write(
            ".specify/memory/constitution.md", "project constitution\n"
        )
        delivery_config = self.write(
            ".specify/extensions/delivery/delivery-config.yml",
            "max_review_fix_rounds: 3\nmax_convergence_rounds: 3\n",
        )
        quality_config = self.write(
            ".specify/extensions/quality/quality-config.yml", "checks: []\n"
        )
        runtime.bind(
            self.relative(feature),
            None,
            [self.relative(ignored_input)],
        )

        snapshot = runtime.snapshot()
        self.assertEqual(snapshot["head"], self.git("rev-parse", "HEAD").stdout.strip())
        for path in (ignored_input, untracked, constitution, delivery_config, quality_config):
            self.assertIn(self.relative(path), snapshot["files"])
        self.assertNotIn(
            ".specify/delivery/snapshot-run/runtime/state.json", snapshot["files"]
        )
        self.assertIn(self.relative(feature / "tasks.md"), snapshot["files"])

    def test_native_receipt_and_explicit_report_header_cannot_upgrade_blocked_owner(self) -> None:
        runtime = self.new_runtime("native-downgrade", "lightweight")
        pending = runtime.begin("quality")
        self.result_file(
            runtime,
            pending,
            "pass",
            self.quality_data(runtime),
            report_text="QUALITY_VERDICT: blocked\nCHECKS:\n- failing: fail\n",
        )
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "explicit machine verdict"):
            runtime.record("quality")

    def test_malformed_stored_pass_data_is_not_reusable(self) -> None:
        runtime = self.new_runtime("malformed-pass", "lightweight")
        pending = runtime.begin("quality")
        self.result_file(runtime, pending, "pass", self.quality_data(runtime))
        runtime.record("quality")
        state = json.loads(runtime.path.read_text(encoding="utf-8"))
        state["stages"]["quality"]["data"] = None
        runtime.path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        with self.assertRaises(RUNTIME.ProtocolError):
            runtime.load()

    def test_prior_blocking_finding_cannot_be_reopened_as_nonblocking(self) -> None:
        runtime, _ = self.feature_runtime("finding-lifecycle")
        finding = {"id": "F-BLOCK", "status": "open", "blocking": True}
        first = runtime.begin("review")
        self.result_file(runtime, first, "blocked", self.review_data(runtime, findings=[finding], repairable=True))
        runtime.record("review")
        second = runtime.begin("review")
        reopened = {"id": "F-BLOCK", "status": "open", "blocking": False}
        self.result_file(runtime, second, "blocked", self.review_data(runtime, findings=[reopened], repairable=True))
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "nonblocking"):
            runtime.record("review")

    def test_original_native_report_and_check_evidence_tampering_is_rejected(self) -> None:
        runtime, _ = self.feature_runtime("evidence-run")
        pending = runtime.begin("quality")
        self.result_file(runtime, pending, "pass", self.quality_data(runtime))
        runtime.record("quality")
        self.assertTrue(runtime.current(runtime.load(), "quality", "pass"))

        stage = runtime.load()["stages"]["quality"]
        report = self.root / stage["report"]["path"]
        original_report = report.read_bytes()
        report.write_text("tampered native report\n", encoding="utf-8")
        with self.assertRaises(RUNTIME.ProtocolError):
            runtime.load()

        report.write_bytes(original_report)
        check = self.root / stage["data"]["checks"][0]["evidence"]["path"]
        check.write_text("tampered check receipt\n", encoding="utf-8")
        with self.assertRaises(RUNTIME.ProtocolError):
            runtime.load()

    def test_review_requires_complete_six_axes_and_current_quality_and_standards(self) -> None:
        runtime, _ = self.feature_runtime("review-contract")

        first = runtime.begin("review")
        self.result_file(
            runtime,
            first,
            "pass",
            self.review_data(runtime),
        )
        missing_owner = self.assertRaises(RUNTIME.ProtocolError)
        with missing_owner:
            runtime.record("review")

        incomplete = self.review_data(
            runtime,
            coverage="incomplete",
            dimensions={**{dimension: "pass" for dimension in DIMENSIONS}, "correctness": "incomplete"},
        )
        self.result_file(runtime, first, "incomplete", incomplete)
        self.assertEqual(runtime.record("review")["verdict"], "incomplete")

        second = runtime.begin("review")
        missing_dimension = self.review_data(runtime, coverage="complete")
        del missing_dimension["dimensions"]["architecture"]
        self.result_file(runtime, second, "incomplete", missing_dimension)
        with self.assertRaises(RUNTIME.ProtocolError):
            runtime.record("review")

        self.record_pass_quality_and_standards(runtime)
        self.result_file(
            runtime,
            second,
            "pass",
            self.review_data(runtime),
        )
        runtime.record("review")
        self.assertFalse(runtime.needs("review"))
        needs = self.cli("needs", "review-contract", kind="review")
        self.assertEqual(needs.stdout, "false")
        self.assertEqual(runtime.require("review"), {"required": "review", "ready": True})

    def test_stale_review_dependencies_remain_readable_until_quality_and_standards_refresh(self) -> None:
        runtime, _ = self.feature_runtime("stale-review-deps")
        self.record_pass_quality_and_standards(runtime)
        self.record_pass_review(runtime)
        pending_standards = runtime.begin("standards")
        self.assertFalse(runtime.current(runtime.load(), "review", "pass"))
        self.result_file(runtime, pending_standards, "pass", {"coverage": "complete"})
        runtime.record("standards")
        pending_quality = runtime.begin("quality")
        self.result_file(runtime, pending_quality, "pass", self.quality_data(runtime))
        runtime.record("quality")
        refreshed_review = runtime.begin("review")
        self.result_file(runtime, refreshed_review, "pass", self.review_data(runtime))
        runtime.record("review")
        self.assertTrue(runtime.current(runtime.load(), "review", "pass"))

    def test_current_review_is_invalidated_by_source_and_late_policy_changes(self) -> None:
        self.write(
            ".specify/extensions/delivery/delivery-config.yml",
            "max_review_fix_rounds: 3\nmax_convergence_rounds: 3\n",
        )
        self.commit("add initial delivery policy")
        runtime, _ = self.feature_runtime("freshness-run")
        self.record_pass_quality_and_standards(runtime)
        self.record_pass_review(runtime)
        self.assertFalse(runtime.needs("review"))

        source = self.root / "src/app.py"
        original_source = source.read_bytes()
        source.write_bytes(b"VALUE = 99\n")
        self.assertTrue(runtime.needs("review"))
        with self.assertRaises(RUNTIME.ProtocolError):
            runtime.require("review")

        source.write_bytes(original_source)
        policy = self.root / ".specify/extensions/delivery/delivery-config.yml"
        policy.write_text(
            "max_review_fix_rounds: 2\nmax_convergence_rounds: 3\n",
            encoding="utf-8",
        )
        self.assertTrue(runtime.needs("review"))

    def test_unresolved_finding_id_must_survive_a_head_change(self) -> None:
        runtime, _ = self.feature_runtime("finding-run")
        finding = {
            "id": "F-KEEP-ME",
            "status": "open",
            "blocking": True,
        }
        first = runtime.begin("review")
        self.result_file(
            runtime,
            first,
            "blocked",
            self.review_data(runtime, findings=[finding], repairable=True),
        )
        runtime.record("review")
        old_head = self.git("rev-parse", "HEAD").stdout.strip()

        self.write("src/app.py", "VALUE = 3\n")
        new_head = self.commit("change after blocked review")
        self.assertNotEqual(old_head, new_head)

        second = runtime.begin("review")
        self.result_file(
            runtime,
            second,
            "blocked",
            self.review_data(runtime, findings=[], repairable=False),
        )
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "unresolved finding"):
            runtime.record("review")
        self.assertIn("review", runtime.load()["pending"])

    def test_failed_quality_check_cannot_pass_and_zero_host_without_result_is_blocked(self) -> None:
        runtime = self.new_runtime("quality-failure", "lightweight")
        pending = runtime.begin("quality")
        self.result_file(
            runtime,
            pending,
            "pass",
            self.quality_data(runtime, exit_code=1, command="failing-native-check"),
        )
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "failing mechanical check"):
            runtime.record("quality")
        self.assertIn("quality", runtime.load()["pending"])

        (runtime.local / "result-quality.json").unlink()
        host = subprocess.run(
            [sys.executable, "-c", "pass"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(host.returncode, 0)
        blocked = self.cli("record", "quality-failure", stage="quality", expected=1)
        self.assertIn("Cannot read result-quality.json", blocked.stderr)
        self.assertIn("quality", runtime.load()["pending"])

    def test_wrong_run_lane_and_ticket_envelopes_cannot_be_recorded(self) -> None:
        runtime = self.new_runtime("envelope-run", "lightweight")
        pending = runtime.begin("quality")
        result_path = self.result_file(
            runtime,
            pending,
            "pass",
            self.quality_data(runtime),
        )
        original = json.loads(result_path.read_text(encoding="utf-8"))
        for field, value in (
            ("delivery_run", "other-run"),
            ("lane", "feature"),
            ("ticket", "wrong-ticket"),
        ):
            with self.subTest(field=field):
                changed = dict(original)
                changed[field] = value
                result_path.write_text(
                    json.dumps(changed, indent=2) + "\n", encoding="utf-8"
                )
                blocked = self.cli(
                    "record", "envelope-run", stage="quality", expected=1
                )
                self.assertIn(f"Result {field} does not match", blocked.stderr)
                self.assertIn("quality", runtime.load()["pending"])

        result_path.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
        other = RUNTIME.Runtime(self.root, "other-run")
        with self.assertRaises(RUNTIME.ProtocolError):
            other.record("quality")

    def test_begin_and_readonly_guards_cannot_mutate_product_code(self) -> None:
        runtime, _ = self.feature_runtime("readonly-run")
        source = self.root / "src/app.py"
        source_before = source.read_bytes()
        status_before = self.git("status", "--short").stdout

        runtime.begin("review")
        with self.assertRaises(RUNTIME.ProtocolError):
            runtime.require("review")
        self.cli("status", "readonly-run")

        self.assertEqual(source.read_bytes(), source_before)
        self.assertEqual(self.git("status", "--short").stdout, status_before)

    def test_converge_is_append_only_tracks_actual_ids_and_converged_keeps_bytes(self) -> None:
        original_tasks = (
            "# Tasks\n\n"
            "- [ ] T1 Implement the change\n"
            "- [X] T2 Verify the baseline\n"
        )
        runtime, feature = self.feature_runtime(
            "converge-run", tasks=original_tasks
        )
        tasks_path = feature / "tasks.md"
        pending = runtime.begin("converge")
        tasks_path.write_text(
            original_tasks + "- [ ] T3 Add regression coverage\n",
            encoding="utf-8",
        )
        appended = self.result_file(
            runtime,
            pending,
            "tasks-appended",
            {"appended_tasks": ["T3"]},
        )
        self.assertTrue(appended.exists())
        recorded = runtime.record("converge")
        self.assertEqual(recorded["data"]["appended_tasks"], ["T3"])
        self.assertTrue(tasks_path.read_text(encoding="utf-8").startswith(original_tasks))

        tasks_path.write_text(
            tasks_path.read_text(encoding="utf-8").replace("- [ ]", "- [x]"),
            encoding="utf-8",
        )
        before_converged = tasks_path.read_bytes()
        converged = runtime.begin("converge")
        self.result_file(
            runtime,
            converged,
            "converged",
            {"appended_tasks": []},
        )
        runtime.record("converge")
        self.assertEqual(tasks_path.read_bytes(), before_converged)
        self.assertFalse(runtime.needs("convergence"))
        self.assertEqual(
            runtime.require("convergence"),
            {"required": "convergence", "ready": True},
        )

        rewritten = runtime.begin("converge")
        current = tasks_path.read_text(encoding="utf-8")
        tasks_path.write_text(
            current.replace("T1 Implement the change", "T1 Rewritten task")
            + "- [ ] T4 Another task\n",
            encoding="utf-8",
        )
        self.result_file(
            runtime,
            rewritten,
            "tasks-appended",
            {"appended_tasks": ["T4"]},
        )
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "append tasks"):
            runtime.record("converge")

    def test_limits_support_indented_block_yaml_and_reject_flow_defaults(self) -> None:
        runtime = self.new_runtime("config-shape", "lightweight")
        config = self.write(
            ".specify/extensions/delivery/delivery-config.yml",
            "delivery:\n  max_review_fix_rounds: 1\n  max_convergence_rounds: 2\n",
        )
        self.assertEqual(runtime.limits(), {"review": 1, "convergence": 2})
        config.write_text("limits: {max_review_fix_rounds: 1, max_convergence_rounds: 2}\n", encoding="utf-8")
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "flow"):
            runtime.limits()

    def test_one_round_budgets_persist_pending_resume_completion_across_head_and_init(self) -> None:
        self.write(
            ".specify/extensions/delivery/delivery-config.yml",
            "max_review_fix_rounds: 1\nmax_convergence_rounds: 1\n",
        )
        self.commit("set one-round delivery budgets")
        runtime = self.new_runtime("budget-run")

        first = json.loads(
            self.cli(
                "reserve",
                "budget-run",
                kind="review",
                scope="outgoing-diff",
            ).stdout
        )
        self.assertEqual(first["attempt"], 1)
        self.assertFalse(first["resumed"])

        fresh = RUNTIME.Runtime(self.root, "budget-run")
        self.assertEqual(fresh.init("lightweight")["attempts"]["review:outgoing-diff"]["pending"], 1)
        self.write("src/app.py", "VALUE = 4\n")
        new_head = self.commit("new head while review repair is pending")
        self.assertTrue(new_head)

        resumed = fresh.reserve("review", "outgoing-diff", resume=1)
        self.assertEqual(resumed, {"attempt": 1, "cap": 1, "resumed": True})
        self.assert_blocked(fresh.reserve, "review", "outgoing-diff")
        self.assert_blocked(fresh.complete, "review", "outgoing-diff", 2)
        completed = RUNTIME.Runtime(self.root, "budget-run").complete(
            "review", "outgoing-diff", 1
        )
        self.assertEqual(completed, {"used": 1, "pending": None})
        self.assert_blocked(
            RUNTIME.Runtime(self.root, "budget-run").reserve,
            "review",
            "outgoing-diff",
        )

        convergence = RUNTIME.Runtime(self.root, "budget-run").reserve(
            "convergence", "outgoing-diff"
        )
        self.assertEqual(convergence["attempt"], 1)
        RUNTIME.Runtime(self.root, "budget-run").complete(
            "convergence", "outgoing-diff", 1
        )
        state = RUNTIME.Runtime(self.root, "budget-run").load()
        self.assertEqual(state["attempts"]["review:outgoing-diff"], {"used": 1, "pending": None})
        self.assertEqual(state["attempts"]["convergence:outgoing-diff"], {"used": 1, "pending": None})

    def test_planning_manifest_uses_configured_direct_proposed_adr_directory(self) -> None:
        runtime, _ = self.feature_runtime("adr-manifest")
        state = runtime.load()
        config = self.write(
            ".specify/extensions/decision/decision-config.yml",
            "adr_directories:\n  - docs/architecture/decisions\nproposed_statuses: [proposed]\n",
        )
        proposed = self.write(
            "docs/architecture/decisions/feature.md",
            "# Feature ADR\nADR_STATUS: Proposed\n",
        )
        accepted = self.write(
            "docs/architecture/decisions/accepted.md",
            "# Accepted ADR\nADR_STATUS: Accepted\n",
        )
        arbitrary = self.write("docs/other.md", "ADR_STATUS: Proposed\n")
        self.assertTrue(runtime._planning_path_allowed(state, runtime.relative(proposed), "decision"))
        self.assertFalse(runtime._planning_path_allowed(state, runtime.relative(accepted), "decision"))
        self.assertFalse(runtime._planning_path_allowed(state, runtime.relative(arbitrary), "decision"))
        decision_context = self.write(
            ".specify/delivery/adr-manifest/decision-context.md",
            "DECISION_CONTEXT: current\n",
        )
        evidence = self.write(
            ".specify/delivery/adr-manifest/evidence.md",
            "delivery_run: adr-manifest\nlane: feature\nstatus: active\n",
        )
        self.assertTrue(runtime._planning_path_allowed(state, runtime.relative(decision_context), "core"))
        self.assertFalse(runtime._planning_path_allowed(state, runtime.relative(evidence), "core"))
        self.assertTrue(config.is_file())
        config.unlink()

        legacy_runtime, _ = self.feature_runtime("adr-legacy")
        legacy = self.write(
            ".specify/decisions/legacy.md",
            "# Legacy ADR\nADR_STATUS: Proposed\n",
        )
        self.assertTrue(legacy_runtime._planning_path_allowed(legacy_runtime.load(), legacy_runtime.relative(legacy), "adr"))

    def test_slice_approval_metadata_does_not_change_analyze_fingerprint_but_plan_bytes_do(self) -> None:
        runtime, feature = self.feature_runtime("slice-freshness")
        slices = runtime.directory / "slices.md"
        slices.write_text(
            "SLICE_PLAN_FINGERPRINT: plan-hash\n"
            "SLICE_APPROVAL: pending\n"
            "S1: T1\n",
            encoding="utf-8",
        )
        analyze = runtime.begin("analyze")
        self.result_file(runtime, analyze, "pass", {"coverage": "complete"})
        runtime.record("analyze")
        analyze_fingerprint = runtime.load()["stages"]["analyze"]["output_fingerprint"]

        slices.write_text(
            slices.read_text(encoding="utf-8")
            + "SLICE_APPROVAL: approved\nApproved by: fixture-user\nApproved mode: single\nApproved at: now\n",
            encoding="utf-8",
        )
        self.assertEqual(runtime.snapshot()["fingerprint"], analyze_fingerprint)

        approved = [runtime.load()["bindings"][name] for name in ("spec", "plan", "tasks")]
        approved.append(".specify/delivery/slice-freshness/slices.md")
        checkpoint = runtime.begin("checkpoint", scope="initial")
        (runtime.local / f"planning-inputs-{checkpoint['ticket']}.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "delivery_run": "slice-freshness",
                    "lane": "feature",
                    "authorization": "fixture planning authorization",
                    "paths": [{"path": path, "source_owner": "core"} for path in approved],
                },
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        self.git("add", "--", self.relative(slices))
        self.git("commit", "--quiet", "-m", "record slice approval metadata")
        self.result_file(
            runtime,
            checkpoint,
            "pass",
            {
                "planning_stage": "initial",
                "approved_paths": approved,
                "branch": self.git("branch", "--show-current").stdout.strip(),
                "base_head": checkpoint["snapshot"]["head"],
                "planning_commit": "none",
                "authorization": "fixture planning authorization",
                "analyze_fingerprint": analyze_fingerprint,
                "content_fingerprint": checkpoint["snapshot"]["fingerprint"],
            },
        )
        runtime.record("checkpoint")
        self.assertTrue(runtime.current(runtime.load(), "analyze", "pass"))
        self.assertTrue(runtime.current(runtime.load(), "checkpoint", "pass"))

        feature.joinpath("plan.md").write_text("# Plan\n\nChanged plan bytes.\n", encoding="utf-8")
        self.assertFalse(runtime.current(runtime.load(), "analyze", "pass"))
        with self.assertRaises(RUNTIME.ProtocolError):
            runtime.require("planning")

    def test_stored_checkpoint_survives_adr_finalization_but_new_checkpoint_requires_proposed(self) -> None:
        runtime, _ = self.feature_runtime("checkpoint-adr")
        adr = self.write(
            ".specify/decisions/checkpoint-adr.md",
            "# ADR\nADR_STATUS: Proposed\n",
        )
        self.commit("add proposed planning ADR")
        analyze = runtime.begin("analyze")
        self.result_file(runtime, analyze, "pass", {"coverage": "complete"})
        runtime.record("analyze")
        approved = [runtime.load()["bindings"][name] for name in ("spec", "plan", "tasks")]
        approved.append(runtime.relative(adr))
        checkpoint = runtime.begin("checkpoint", scope="initial")
        (runtime.local / f"planning-inputs-{checkpoint['ticket']}.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "delivery_run": "checkpoint-adr",
                    "lane": "feature",
                    "authorization": "fixture ADR planning authorization",
                    "paths": [
                        *[{"path": path, "source_owner": "core"} for path in approved[:-1]],
                        {"path": approved[-1], "source_owner": "decision"},
                    ],
                },
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        self.result_file(
            runtime,
            checkpoint,
            "pass",
            {
                "planning_stage": "initial",
                "approved_paths": approved,
                "branch": self.git("branch", "--show-current").stdout.strip(),
                "base_head": checkpoint["snapshot"]["head"],
                "planning_commit": "none",
                "authorization": "fixture ADR planning authorization",
                "analyze_fingerprint": runtime.load()["stages"]["analyze"]["output_fingerprint"],
                "content_fingerprint": checkpoint["snapshot"]["fingerprint"],
            },
        )
        runtime.record("checkpoint")

        adr.write_text("# ADR\nADR_STATUS: Accepted\n", encoding="utf-8")
        self.assertIsInstance(runtime.load(), dict)
        self.assertFalse(runtime.current(runtime.load(), "checkpoint", "pass"))
        self.assertFalse(runtime.needs("simplification-verification"))
        self.assertNotEqual(runtime.status()["status"], "corrupt")

        fresh = runtime.begin("checkpoint", scope="simplify")
        (runtime.local / f"planning-inputs-{fresh['ticket']}.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "delivery_run": "checkpoint-adr",
                    "lane": "feature",
                    "authorization": "fixture ADR planning authorization",
                    "paths": [
                        *[{"path": path, "source_owner": "core"} for path in approved[:-1]],
                        {"path": approved[-1], "source_owner": "decision"},
                    ],
                },
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        self.result_file(
            runtime,
            fresh,
            "pass",
            {
                "planning_stage": "simplify",
                "approved_paths": approved,
                "branch": self.git("branch", "--show-current").stdout.strip(),
                "base_head": fresh["snapshot"]["head"],
                "planning_commit": "none",
                "authorization": "fixture ADR planning authorization",
            },
        )
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "Proposed ADR|allowlist"):
            runtime.record("checkpoint")

    def test_present_then_decide_rejects_changed_input_until_represented(self) -> None:
        runtime = self.new_runtime("decision-run")
        presented = json.loads(
            self.cli(
                "present",
                "decision-run",
                name="plan-gate",
                input=["src/app.py"],
            ).stdout
        )
        original_hash = presented["inputs"]["src/app.py"]
        self.write("src/app.py", "VALUE = 5\n")
        blocked = self.cli(
            "decide",
            "decision-run",
            name="plan-gate",
            choice="approve",
            expected=1,
        )
        self.assertIn("inputs changed", blocked.stderr)
        self.assertEqual(
            runtime.load()["approvals"]["plan-gate"]["choice"], "pending"
        )
        represented = json.loads(
            self.cli(
                "present",
                "decision-run",
                name="plan-gate",
                input=["src/app.py"],
            ).stdout
        )
        self.assertNotEqual(represented["inputs"]["src/app.py"], original_hash)
        decided = json.loads(
            self.cli(
                "decide",
                "decision-run",
                name="plan-gate",
                choice="reject",
            ).stdout
        )
        self.assertEqual(decided["choice"], "reject")

    def test_operational_run_records_do_not_block_entry_but_source_does(self) -> None:
        runtime, _ = self.feature_runtime("operational-dirt")
        self.write(
            runtime.directory / "reviews" / "outgoing-diff" / "review.yml",
            "native review report\n",
        )
        self.write(
            runtime.directory / "runtime" / "pending-note.txt",
            "local coordinator note\n",
        )
        self.write(runtime.directory / "task-verdicts.yml", "task receipt\n")
        self.write(runtime.directory / "pull-request.md", "# body\n")
        self.assertEqual(runtime.execution_dirty_paths(), [])

        self.write("src/app.py", "VALUE = 2\n")
        dirty = runtime.execution_dirty_paths()
        self.assertIn("src/app.py", dirty)

    def test_planning_requires_passing_analyze_and_native_checkpoint(self) -> None:
        runtime, feature = self.feature_runtime("planning-run")
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "checkpoint"):
            runtime.require("planning")

        analyze = runtime.begin("analyze")
        self.result_file(runtime, analyze, "pass", {"coverage": "complete"})
        runtime.record("analyze")

        approved = [
            runtime.load()["bindings"][name]
            for name in ("spec", "plan", "tasks")
        ]
        checkpoint = runtime.begin("checkpoint", scope="initial")
        manifest = runtime.local / f"planning-inputs-{checkpoint['ticket']}.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "delivery_run": "planning-run",
                    "lane": "feature",
                    "authorization": "project-approved planning paths",
                    "paths": [{"path": path, "source_owner": "core"} for path in approved],
                },
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        branch = self.git("branch", "--show-current").stdout.strip()
        self.result_file(
            runtime,
            checkpoint,
            "pass",
            {
                "planning_stage": "initial",
                "approved_paths": approved,
                "branch": branch,
                "base_head": checkpoint["snapshot"]["head"],
                "planning_commit": "none",
                "authorization": "project-approved planning paths",
                "analyze_fingerprint": runtime.load()["stages"]["analyze"]["output_fingerprint"],
                "content_fingerprint": checkpoint["snapshot"]["fingerprint"],
            },
        )
        runtime.record("checkpoint")
        self.assertEqual(runtime.require("planning"), {"required": "planning", "ready": True})

        plan = feature / "plan.md"
        plan.write_text("# Plan\n\nChanged after the approved checkpoint.\n", encoding="utf-8")
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "clean execution entry"):
            runtime.require("planning")
        self.assertIn(self.relative(plan), self.git("status", "--short").stdout)
        self.commit("change planning input after checkpoint")
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "checkpoint"):
            runtime.require("planning")

    def test_ticket_specific_manifests_allow_two_checkpoint_histories(self) -> None:
        runtime, feature = self.feature_runtime("checkpoint-history")
        approved_initial = [runtime.load()["bindings"][name] for name in ("spec", "plan", "tasks")]
        analyze = runtime.begin("analyze")
        self.result_file(runtime, analyze, "pass", {"coverage": "complete"})
        runtime.record("analyze")
        first = runtime.begin("checkpoint", scope="initial")
        first_manifest = runtime.local / f"planning-inputs-{first['ticket']}.json"
        first_manifest.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "delivery_run": "checkpoint-history",
                    "lane": "feature",
                    "authorization": "initial planning authorization",
                    "paths": [{"path": path, "source_owner": "core"} for path in approved_initial],
                },
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        branch = self.git("branch", "--show-current").stdout.strip()
        self.result_file(
            runtime,
            first,
            "pass",
            {
                "planning_stage": "initial",
                "approved_paths": approved_initial,
                "branch": branch,
                "base_head": first["snapshot"]["head"],
                "planning_commit": "none",
                "authorization": "initial planning authorization",
            },
        )
        runtime.record("checkpoint")

        research = feature / "research.md"
        research.write_text("# Research\n\nNew convergence planning output.\n", encoding="utf-8")
        reassess = runtime.begin("analyze")
        self.result_file(runtime, reassess, "pass", {"coverage": "complete"})
        runtime.record("analyze")
        approved_next = [*approved_initial, runtime.relative(research)]
        second = runtime.begin("checkpoint", scope="converge")
        second_manifest = runtime.local / f"planning-inputs-{second['ticket']}.json"
        second_manifest.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "delivery_run": "checkpoint-history",
                    "lane": "feature",
                    "authorization": "convergence planning authorization",
                    "paths": [{"path": path, "source_owner": "core"} for path in approved_next],
                },
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        self.git("add", "--", self.relative(research))
        self.git("commit", "--quiet", "-m", "commit convergence research output")
        self.result_file(
            runtime,
            second,
            "pass",
            {
                "planning_stage": "converge",
                "approved_paths": approved_next,
                "branch": branch,
                "base_head": second["snapshot"]["head"],
                "planning_commit": self.git("rev-parse", "HEAD").stdout.strip(),
                "authorization": "convergence planning authorization",
            },
        )
        runtime.record("checkpoint")
        state = runtime.load()
        self.assertNotEqual(first_manifest, second_manifest)
        self.assertEqual(len(state["checkpoint_history"]), 2)
        self.assertTrue(runtime.current(state, "checkpoint", "pass"))
        self.assertTrue(runtime.current(state, "analyze", "pass"))
        self.assertEqual(runtime.require("planning"), {"required": "planning", "ready": True})

    def test_status_reports_disappeared_observed_evidence_as_a_blocker(self) -> None:
        runtime = self.new_runtime("evidence-disappears", "lightweight")
        evidence = self.write(
            ".specify/delivery/evidence-disappears/evidence.md",
            "delivery_run: evidence-disappears\n"
            "lane: lightweight\n"
            "status: active\n"
            "pull_request: pending\n",
        )
        runtime.require("evidence")
        evidence.unlink()
        status = runtime.status()
        self.assertEqual(status["status"], "active")
        self.assertTrue(any("missing" in blocker.lower() for blocker in status["blockers"]))

    def test_unverified_close_leaves_every_run_file_and_state_unchanged(self) -> None:
        runtime = self.new_runtime("unverified-close")
        evidence = self.write(
            ".specify/delivery/unverified-close/evidence.md",
            "delivery_run: unverified-close\n"
            "lane: lightweight\n"
            "status: active\n"
            "pull_request: pending\n",
        )
        self.write(
            ".specify/delivery/unverified-close/exploration.md",
            "workspace evidence\n",
        )
        before = {
            self.relative(path): path.read_bytes()
            for path in runtime.directory.rglob("*")
            if path.is_file()
        }
        state_before = runtime.path.read_bytes()
        blocked = self.cli(
            "outcome",
            "unverified-close",
            outcome="unverified",
            expected=1,
        )
        self.assertIn("unverified", blocked.stderr.lower())
        after = {
            self.relative(path): path.read_bytes()
            for path in runtime.directory.rglob("*")
            if path.is_file()
        }
        self.assertEqual(after, before)
        self.assertEqual(runtime.path.read_bytes(), state_before)
        self.assertTrue(evidence.exists())

    def test_pending_pr_binds_first_verified_reference_and_concrete_conflicts_block(self) -> None:
        runtime = self.new_runtime("pr-run")
        evidence = self.write(
            ".specify/delivery/pr-run/evidence.md",
            "delivery_run: pr-run\n"
            "lane: lightweight\n"
            "status: active\n"
            "pull_request: pending\n",
        )
        pending_bytes = evidence.read_bytes()
        runtime.require("evidence")
        first = runtime.outcome("merged", True, "#42")
        self.assertEqual(
            first,
            {
                "eligible": True,
                "outcome": "merged",
                "pull_request": "#42",
                "writes_performed": False,
            },
        )
        self.assertEqual(evidence.read_bytes(), pending_bytes)

        evidence.write_text(
            "delivery_run: pr-run\n"
            "lane: lightweight\n"
            "status: active\n"
            "pull_request: https://github.com/Org/Repo/pull/42\n",
            encoding="utf-8",
        )
        runtime.require("evidence")
        same_concrete = runtime.outcome(
            "merged", True, "https://github.com/Org/Repo/pull/42"
        )
        self.assertTrue(same_concrete["eligible"])
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "identity conflict"):
            runtime.outcome("merged", True, "https://github.com/org/repo/pull/43")
        with self.assertRaises(RUNTIME.ProtocolError):
            runtime.outcome("merged", True, "#42")
        with self.assertRaises(RUNTIME.ProtocolError):
            runtime.outcome("closed", True, None)

    def test_handoff_ready_is_distinct_from_delivered_terminal_scope(self) -> None:
        runtime, _ = self.feature_runtime("handoff-run")
        self.record_pass_quality_and_standards(runtime)
        self.record_pass_review(runtime)
        evidence = self.write(
            ".specify/delivery/handoff-run/evidence.md",
            "delivery_run: handoff-run\n"
            "lane: feature\n"
            "status: active\n"
            "pull_request: pending\n",
        )
        self.write(
            ".specify/delivery/handoff-run/pull-request.md",
            "# Handoff\n\nNative Handoff body.\n",
        )
        runtime.require("evidence")

        handoff = runtime.phase("handoff")
        self.assertEqual(handoff["status"], "handoff-ready")
        self.assertEqual(runtime.status()["status"], "handoff-ready")
        self.assertIn("Await separately authorized publication", runtime.status()["next_action"])

        evidence.write_text(
            "delivery_run: handoff-run\n"
            "lane: feature\n"
            "status: delivered\n"
            "pull_request: https://github.com/org/repo/pull/42\n",
            encoding="utf-8",
        )
        self.assertEqual(runtime.status()["status"], "verification-required")
        self.assertTrue(runtime.status()["blockers"])
        runtime.outcome("merged", True, "https://github.com/org/repo/pull/42")
        self.assertEqual(runtime.status()["status"], "delivered")
        self.assertEqual(runtime.status()["next_action"], "Outcome recorded; retain durable evidence.")
        with self.assertRaises(RUNTIME.ProtocolError):
            runtime.phase("handoff")

    def test_workflow_occurrence_journal_replays_only_the_same_active_step(self) -> None:
        runtime = self.new_runtime("engine-journal", "lightweight")
        engine_state = self.root / ".specify" / "workflows" / "runs" / "engine-run" / "state.json"
        self.write(
            engine_state.relative_to(self.root),
            json.dumps(
                {
                    "run_id": "engine-run",
                    "status": "running",
                    "current_step_id": "quality-begin-loop-0",
                    "current_occurrence_path": "delivery/quality-loop/0/begin",
                    "inputs": {"delivery_run": "engine-journal"},
                },
                indent=2,
            ) + "\n",
        )
        first = json.loads(
            self.cli(
                "begin",
                "engine-journal",
                stage="quality",
                workflow_run="engine-run",
            ).stdout
        )
        state_before = runtime.path.read_bytes()
        second = json.loads(
            self.cli(
                "begin",
                "engine-journal",
                stage="quality",
                workflow_run="engine-run",
            ).stdout
        )
        self.assertEqual(first, second)
        self.assertEqual(runtime.path.read_bytes(), state_before)
        self.assertEqual(len(runtime.load()["operations"]), 1)

        self.result_file(runtime, first, "pass", self.quality_data(runtime))
        runtime.record("quality")
        self.write(
            engine_state.relative_to(self.root),
            json.dumps(
                {
                    "run_id": "engine-run",
                    "status": "running",
                    "current_step_id": "quality-begin-loop-1",
                    "current_occurrence_path": "delivery/quality-loop/1/begin",
                    "inputs": {"delivery_run": "engine-journal"},
                },
                indent=2,
            ) + "\n",
        )
        next_occurrence = json.loads(
            self.cli(
                "begin",
                "engine-journal",
                stage="quality",
                workflow_run="engine-run",
            ).stdout
        )
        self.assertNotEqual(next_occurrence["ticket"], first["ticket"])
        self.assertNotEqual(next_occurrence["operation_id"], first.get("operation_id"))

        missing = self.cli(
            "begin",
            "engine-journal",
            stage="quality",
            workflow_run="missing-engine-run",
            expected=1,
        )
        self.assertIn("state.json", missing.stderr)


if __name__ == "__main__":
    unittest.main()
