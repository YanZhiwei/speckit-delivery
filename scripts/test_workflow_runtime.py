#!/usr/bin/env python3
"""Full Spec Kit workflow probes with real shell/runtime transport and fake models."""
from __future__ import annotations

import contextlib
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import types
import tempfile
import unittest
from typing import Any
from unittest.mock import patch

import yaml
from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine
from specify_cli.workflows.step.command import CommandStep
from specify_cli.workflows.step.gate import GateStep


ROOT = Path(__file__).resolve().parents[1]
HELPER_SOURCE = ROOT / "extensions/delivery/scripts/delivery_runtime.py"
SPEC = importlib.util.spec_from_file_location("delivery_runtime_workflow_test", HELPER_SOURCE)
if SPEC is None or SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"Cannot import {HELPER_SOURCE}")
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


class FakeConsumers:
    def __init__(
        self,
        root: Path,
        *,
        repairs_to_resolve: int = 0,
        omit_first_review_result: bool = False,
        stale_recheck_result: bool = False,
    ) -> None:
        self.root = root
        self.repairs_to_resolve = repairs_to_resolve
        self.omit_first_review_result = omit_first_review_result
        self.stale_recheck_result = stale_recheck_result
        self.calls: list[str] = []
        self.review_calls = 0
        self.repair_calls = 0

    @staticmethod
    def token(args: str, name: str) -> str | None:
        import re

        match = re.search(rf"(?<!\S){re.escape(name)}=(\S+)", args)
        return match.group(1) if match else None

    def _runtime(self) -> RUNTIME.Runtime:
        run = self.token(self.current_args, "delivery_run")
        if not run:
            raise AssertionError(f"runtime command omitted delivery_run: {self.current_args}")
        return RUNTIME.Runtime(self.root, run)

    def _save_result(
        self,
        runtime: RUNTIME.Runtime,
        pending: dict[str, Any],
        report: Path,
        verdict: str,
        data: dict[str, Any],
        result_path: Path,
    ) -> None:
        def reference(path: Path) -> dict[str, str]:
            return {"path": runtime.relative(path), "sha256": RUNTIME.digest(path.read_bytes())}

        def evidence_references(value: Any) -> list[dict[str, str]]:
            if isinstance(value, dict):
                if set(value) == {"path", "sha256"}:
                    return [value]
                return [reference for child in value.values() for reference in evidence_references(child)]
            if isinstance(value, list):
                return [reference for child in value for reference in evidence_references(child)]
            return []

        if pending["stage"] == "review" and verdict == "pass":
            stages = runtime.load()["stages"]
            data["dependencies"] = {
                stage: {
                    key: stages[stage][key]
                    for key in ("stage", "ticket", "input_fingerprint", "verdict", "report", "native_receipt")
                }
                for stage in ("quality", "standards")
            }
        envelope = {
            key: pending[key]
            for key in ("schema_version", "delivery_run", "lane", "stage", "scope", "ticket", "input_fingerprint")
        }
        envelope.update({"verdict": verdict, "report": reference(report), "data": data})
        receipt = {
            "schema_version": 1,
            "receipt_type": "delivery-native-owner",
            **{key: envelope[key] for key in ("delivery_run", "lane", "stage", "scope", "ticket", "input_fingerprint", "verdict", "report")},
            "head": (
                runtime.git("rev-parse", "HEAD").decode().strip()
                if pending["stage"] == "checkpoint"
                else pending["snapshot"]["head"]
            ),
            "evidence": evidence_references(data),
            "data": data,
        }
        receipt_path = runtime.local / f"native-{pending['stage']}-{pending['ticket']}.json"
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        envelope["native_receipt"] = reference(receipt_path)
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps(envelope, indent=2) + "\n", encoding="utf-8")

    def _write_stage_result(self, stage: str) -> None:
        runtime = self._runtime()
        state = runtime.load()
        pending = state["pending"].get(stage)
        if not pending:
            raise AssertionError(f"fake owner called without pending {stage} ticket")
        run_dir = self.root / ".specify" / "delivery" / pending["delivery_run"]
        if stage == "quality":
            report = run_dir / f"native-quality-{len(self.calls)}.yml"
            evidence = run_dir / f"quality-check-{len(self.calls)}.txt"
            evidence.parent.mkdir(parents=True, exist_ok=True)
            evidence.write_text("real fake check: exit 0\n", encoding="utf-8")
            data = {
                "checks": [
                    {
                        "command": "python -m unittest",
                        "exit_code": 0,
                        "evidence": {
                            "path": runtime.relative(evidence),
                            "sha256": RUNTIME.digest(evidence.read_bytes()),
                        },
                    }
                ]
            }
            verdict = "pass"
        elif stage == "standards":
            report = run_dir / f"native-standards-{len(self.calls)}.yml"
            data = {"coverage": "complete"}
            verdict = "pass"
        elif stage == "simplify":
            report = run_dir / "simplifications.md"
            data = {"candidates": []}
            verdict = "none"
        elif stage == "converge":
            report = run_dir / "native-converge.yml"
            data = {"appended_tasks": []}
            verdict = "converged"
        elif stage == "review":
            self.review_calls += 1
            report = run_dir / f"reviews/outgoing-diff/review-{self.review_calls}.yml"
            should_pass = self.repair_calls >= self.repairs_to_resolve
            if self.stale_recheck_result and self.review_calls == 2:
                # Keep the first ticket/result on disk; record must reject it.
                return
            if should_pass:
                resolution = run_dir / f"review-resolution-{self.review_calls}.txt"
                resolution.parent.mkdir(parents=True, exist_ok=True)
                resolution.write_text("finding F-1 resolved by the independent re-review\n", encoding="utf-8")
                data = {
                    "dimensions": {key: "pass" for key in DIMENSIONS},
                    "coverage": "complete",
                    "independence": "independent",
                    "repairable": False,
                    "findings": (
                        []
                        if self.review_calls == 1
                        else [
                            {
                                "id": "F-1",
                                "status": "resolved",
                                "blocking": True,
                                "evidence": {
                                    "path": runtime.relative(resolution),
                                    "sha256": RUNTIME.digest(resolution.read_bytes()),
                                },
                            }
                        ]
                    ),
                }
                verdict = "pass"
            else:
                data = {
                    "dimensions": {
                        key: ("blocked" if key == "correctness" else "pass")
                        for key in DIMENSIONS
                    },
                    "coverage": "complete",
                    "independence": "independent",
                    "repairable": True,
                    "findings": [
                        {"id": "F-1", "status": "open", "blocking": True}
                    ],
                }
                verdict = "blocked"
        else:  # pragma: no cover - the fixture intentionally covers every stage
            raise AssertionError(f"unexpected runtime stage {stage}")

        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(f"NATIVE_VERDICT: {verdict}\nnative {stage} report\n", encoding="utf-8")
        self._save_result(runtime, pending, report, verdict, data, self.result_path)

    def dispatch(self, command, integration, model, args, context, *extra, **kwargs):
        self.current_args = args
        self.calls.append(command)
        if command in {"speckit.quality.check", "speckit.review.standards", "speckit.simplify.scan", "speckit.review.run", "speckit.converge"}:
            stage = self.token(args, "runtime_stage")
            result = self.token(args, "runtime_result")
            if not stage or not result:
                return {"exit_code": 1, "stdout": "", "stderr": "runtime stage/result missing"}
            self.result_path = self.root / result
            if command == "speckit.review.run" and self.review_calls == 0 and self.omit_first_review_result:
                # Emit a native report but deliberately omit the normalized result.
                runtime = self._runtime()
                pending = runtime.load()["pending"][stage]
                report = self.root / ".specify" / "delivery" / pending["delivery_run"] / "reviews/outgoing-diff/review.yml"
                report.parent.mkdir(parents=True, exist_ok=True)
                report.write_text("native report without normalized result\n", encoding="utf-8")
            else:
                self._write_stage_result(stage)
        elif command == "speckit.delivery.review-fix":
            self.repair_calls += 1
            source = self.root / "src/app.py"
            source.write_text(source.read_text(encoding="utf-8") + f"# repair {self.repair_calls}\n", encoding="utf-8")
        elif command == "speckit.evidence.collect":
            run = self.token(args, "delivery_run")
            evidence = self.root / ".specify" / "delivery" / str(run) / "evidence.md"
            evidence.parent.mkdir(parents=True, exist_ok=True)
            evidence.write_text(
                f"- **delivery_run**: {run}\n"
                "- **lane**: lightweight\n"
                f"- **evidence_path**: .specify/delivery/{run}/evidence.md\n"
                "- **pull_request**: pending\n",
                encoding="utf-8",
            )
        elif command == "speckit.delivery.handoff":
            run = self.token(args, "delivery_run")
            handoff = self.root / ".specify" / "delivery" / str(run) / "pull-request.md"
            handoff.parent.mkdir(parents=True, exist_ok=True)
            handoff.write_text("# Proposed handoff\n\nVerified bounded fixture change.\n", encoding="utf-8")
        elif command in {
            "speckit.delivery.doctor",
            "speckit.quality.brief",
            "speckit.delivery.lightweight",
            "speckit.docs-sync.package-readme",
            "speckit.simplify.verify",
        }:
            pass
        else:
            return {"exit_code": 1, "stdout": "", "stderr": f"unexpected fake command: {command}"}
        return {"exit_code": 0, "stdout": "", "stderr": ""}


class FullWorkflowConsumers(FakeConsumers):
    """Strict disk-bound consumers for the complete Feature and Bugfix lanes."""

    def __init__(
        self,
        root: Path,
        *,
        lane: str,
        repairs_to_resolve: int = 0,
        append_convergence: bool = False,
        never_converges: bool = False,
        clarify_needs_approval: bool = False,
        simplify_candidates: list[str] | None = None,
        mutate_after_review: bool = False,
        docs_change: bool = False,
        bug_slug: str = "actual-bug",
    ) -> None:
        super().__init__(root, repairs_to_resolve=repairs_to_resolve)
        self.lane = lane
        self.bug_slug = bug_slug
        self.append_convergence = append_convergence
        self.never_converges = never_converges
        self.clarify_needs_approval = clarify_needs_approval
        self.simplify_candidates = simplify_candidates or []
        self.mutate_after_review = mutate_after_review
        self.docs_change = docs_change
        self.dispatches: list[tuple[str, str]] = []
        self.stage_counts: dict[str, int] = {}
        self.analyze_calls = 0
        self.ralph_calls = 0
        self.converge_calls = 0
        self.simplify_verify_calls = 0
        self.apply_simplification_calls = 0
        self.planning_commits: list[str] = []
        self.checkpoint_stages: list[str] = []
        self.fix_report: Path | None = None
        self.test_report: Path | None = None
        self.assessment_path: Path | None = None
        self.adr_path: Path | None = None
        self.candidate_hash: str | None = None
        self.simplify_applied = False
        self.convergence_appended = False
        self.convergence_snapshots: list[tuple[bytes, bytes]] = []
        self.ralph_tasks: list[list[str]] = []
        self.checkpoint_records: list[dict[str, Any]] = []
        self.official_reports: dict[str, bytes] = {}
        self.simplification_proposal: bytes | None = None
        self.clarification_written = False
        self.had_blocked_review = False

    @staticmethod
    def _expect(condition: bool, message: str) -> None:
        if not condition:
            raise AssertionError(message)

    def _run_id(self, args: str | None = None) -> str:
        value = self.token(args or self.current_args, "delivery_run")
        self._expect(value is not None, f"missing delivery_run in {args or self.current_args}")
        return str(value)

    def _run_dir(self, args: str | None = None) -> Path:
        return self.root / ".specify" / "delivery" / self._run_id(args)

    def _feature_dir(self, args: str | None = None) -> Path:
        return self.root / ".specify" / "features" / f"feature-{self._run_id(args)}"

    def _relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def _git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            capture_output=True,
            text=True,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
        if result.returncode:
            raise AssertionError(
                "fake consumer git command failed: "
                + " ".join(arguments)
                + f"\nstdout={result.stdout}\nstderr={result.stderr}"
            )
        return result

    def _write(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def _ensure_adr(self, args: str | None = None) -> Path:
        if self.adr_path is None:
            slug = self._run_id(args) if self.lane == "feature" else self.bug_slug
            status = "Proposed" if self.mutate_after_review else "Accepted"
            self.adr_path = self.root / ".specify" / "decisions" / f"{slug}.md"
            self._write(self.adr_path, f"# ADR {slug}\n\nADR_STATUS: {status}\n")
        return self.adr_path

    def _write_exploration(self, args: str) -> None:
        run = self._run_id(args)
        packet = self.root / ".specify" / "delivery" / run / "exploration.md"
        if self.lane == "feature":
            text = (
                f"DELIVERY_RUN: {run}\n"
                "LANE: feature\n"
                "CURRENT_TREE: src/app.py\n"
                "CANDIDATE_TREE: .specify/features/<created-by-specify>\n"
                "SCOPE_APPROVAL: pending\n"
            )
        else:
            text = (
                f"DELIVERY_RUN: {run}\n"
                "LANE: bugfix\n"
                f"BUG_SLUG: {self.bug_slug}\n"
                f"ASSESSMENT_PATH: .specify/bugs/{self.bug_slug}/assessment.md\n"
                "SCOPE_APPROVAL: pending\n"
            )
        self._write(packet, text)

    def _write_specify(self, args: str) -> None:
        self._expect(self.lane == "feature", "Specify must not run in the Bugfix lane")
        packet = self.root / ".specify" / "delivery" / self._run_id(args) / "exploration.md"
        self._expect(packet.is_file(), "Specify did not receive the persisted exploration packet")
        self._expect(self.token(args, "exploration") == self._relative(packet), "Specify received a different exploration packet")
        self._expect(self.token(args, "scope_approval") == "approve", "Specify lost the actual scope gate choice")
        self._expect(self._runtime().load()["approvals"].get("scope", {}).get("choice") == "approve", "Specify bypassed the runtime scope receipt")
        feature = self._feature_dir(args)
        self._write(feature / "spec.md", "# Feature Spec\n\nApproved behavior and acceptance criteria.\n")
        with packet.open("a", encoding="utf-8") as stream:
            stream.write(f"FEATURE_DIR: {self._relative(feature)}\n")
        markers = [
            line for line in packet.read_text(encoding="utf-8").splitlines()
            if line.startswith("FEATURE_DIR:")
        ]
        self._expect(len(markers) == 1, "Core Specify must emit exactly one FEATURE_DIR marker")

    def _write_stage_result(self, stage: str) -> None:
        runtime = self._runtime()
        state = runtime.load()
        pending = state["pending"].get(stage)
        self._expect(pending is not None, f"fake owner called without pending {stage} ticket")
        run_dir = runtime.local
        count = self.stage_counts.get(stage, 0) + 1
        self.stage_counts[stage] = count

        if stage == "clarify" and self.clarify_needs_approval and not self.clarification_written:
            spec = runtime.bound_file(state, "spec")
            spec.write_text(
                spec.read_text(encoding="utf-8")
                + "\nMaterial clarification: acceptance boundary recorded.\n",
                encoding="utf-8",
            )
            self.clarification_written = True

        if stage == "converge":
            self.converge_calls += 1
            should_append = False
            append_reason = ""
            if self.never_converges or (self.append_convergence and not self.convergence_appended):
                should_append = True
                append_reason = "convergence gap"
                self.convergence_appended = True
            tasks = runtime.bound_file(state, "tasks")
            tasks_before = tasks.read_bytes()
            appended_ids: list[str] = []
            if should_append:
                existing = {
                    match[1]
                    for match in re.finditer(r"^\s*-\s*\[[ xX]\]\s+(T\d+)\b", tasks.read_text(encoding="utf-8"), re.MULTILINE)
                }
                number = 2
                while f"T{number:03d}" in existing:
                    number += 1
                task_id = f"T{number:03d}"
                text = tasks.read_text(encoding="utf-8")
                if text and not text.endswith("\n"):
                    text += "\n"
                text += f"- [ ] {task_id} {append_reason}\n"
                tasks.write_text(text, encoding="utf-8")
                appended_ids.append(task_id)
            self.convergence_snapshots.append((tasks_before, tasks.read_bytes()))
            report = run_dir / f"native-converge-{count}.yml"
            data = {"appended_tasks": appended_ids}
            verdict = "tasks-appended" if appended_ids else "converged"
        elif stage == "quality":
            report = run_dir / f"native-quality-{count}.yml"
            evidence = run_dir / f"quality-check-{count}.txt"
            self._write(evidence, "fake native check: exit 0\n")
            data = {
                "checks": [
                    {
                        "command": "python -m unittest",
                        "exit_code": 0,
                        "evidence": {
                            "path": runtime.relative(evidence),
                            "sha256": RUNTIME.digest(evidence.read_bytes()),
                        },
                    }
                ]
            }
            verdict = "pass"
        elif stage == "standards":
            report = run_dir / f"native-standards-{count}.yml"
            data = {"coverage": "complete"}
            verdict = "pass"
        elif stage == "analyze":
            self.analyze_calls += 1
            tasks = runtime.bound_file(state, "tasks").read_text(encoding="utf-8")
            mapping = (runtime.directory / "slices.md").read_text(encoding="utf-8")
            task_ids = re.findall(r"^\s*-\s*\[[ xX]\]\s+(T\d+)\b", tasks, re.MULTILINE)
            self._expect(all(task_id in mapping for task_id in task_ids), "Analyze received a stale slice mapping for the current Core task queue")
            report = run_dir / f"native-analyze-{count}.yml"
            data = {"coverage": "complete", "findings": []}
            verdict = "pass"
        elif stage == "clarify":
            report = run_dir / f"native-clarify-{count}.yml"
            data = {
                "needs_approval": self.clarify_needs_approval,
                "decision": "material-acceptance-boundary" if self.clarify_needs_approval else "none",
            }
            verdict = "ready"
        elif stage == "simplify":
            report = runtime.directory / "simplifications.md"
            candidates = list(self.simplify_candidates)
            self.candidate_hash = RUNTIME.digest(
                json.dumps(candidates, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            )
            self._write(
                report,
                "# Simplifications\n"
                + "".join(f"- {candidate}\n" for candidate in candidates)
                + f"CANDIDATE_HASH: {self.candidate_hash}\n",
            )
            self.simplification_proposal = report.read_bytes()
            data = {"candidates": candidates, "candidate_hash": self.candidate_hash}
            verdict = "candidates" if candidates else "none"
        elif stage == "simplify-verify":
            report = runtime.local / f"native-simplify-verify-{count}.yml"
            accepted = runtime.accepted_candidates(state)
            data = {"accepted_candidates": accepted}
            verdict = "pass" if accepted else "not-applicable"
        elif stage == "review":
            self.review_calls += 1
            report = runtime.directory / "reviews" / "outgoing-diff" / f"review-{self.review_calls}.yml"
            should_pass = self.repair_calls >= self.repairs_to_resolve
            if should_pass:
                findings: list[dict[str, Any]] = []
                if self.had_blocked_review:
                    resolution = run_dir / f"review-resolution-{self.review_calls}.txt"
                    self._write(resolution, "F-1 resolved by the bounded repair.\n")
                    findings = [
                        {
                            "id": "F-1",
                            "status": "resolved",
                            "blocking": True,
                            "evidence": {
                                "path": runtime.relative(resolution),
                                "sha256": RUNTIME.digest(resolution.read_bytes()),
                            },
                        }
                    ]
                data = {
                    "dimensions": {dimension: "pass" for dimension in DIMENSIONS},
                    "coverage": "complete",
                    "independence": "independent",
                    "repairable": False,
                    "findings": findings,
                }
                verdict = "pass"
            else:
                self.had_blocked_review = True
                data = {
                    "dimensions": {
                        dimension: ("blocked" if dimension == "correctness" else "pass")
                        for dimension in DIMENSIONS
                    },
                    "coverage": "complete",
                    "independence": "independent",
                    "repairable": True,
                    "findings": [{"id": "F-1", "status": "open", "blocking": True}],
                }
                verdict = "blocked"
        else:
            raise AssertionError(f"unexpected full-workflow stage {stage}")

        if stage != "simplify":
            self._write(report, f"NATIVE_VERDICT: {verdict}\nnative {stage} report {count}\n")
        result_path_text = self.token(self.current_args, "runtime_result")
        self._expect(result_path_text is not None, f"{stage} omitted runtime_result")
        self._save_result(runtime, pending, report, verdict, data, self.root / str(result_path_text))

    def _planning_paths(self, runtime: RUNTIME.Runtime) -> list[str]:
        state = runtime.load()
        paths = [
            value
            for key, value in state["bindings"].items()
            if key in {"spec", "plan", "tasks"} and isinstance(value, str)
        ]
        run = self._run_id()
        paths.extend(
            [
                f".specify/delivery/{run}/exploration.md",
                f".specify/delivery/{run}/code-context.md",
                f".specify/delivery/{run}/slices.md",
            ]
        )
        if self.adr_path is not None:
            paths.append(self._relative(self.adr_path))
        return sorted(set(paths))

    def _write_checkpoint(self, args: str) -> None:
        runtime = self._runtime()
        state = runtime.load()
        pending = state["pending"].get("checkpoint")
        self._expect(pending is not None, "checkpoint route called without a pending checkpoint ticket")
        planning_stage = (
            self.token(args, "planning_stage")
            or self.token(args, "checkpoint_stage")
            or self.token(args, "stage")
        )
        self._expect(
            planning_stage in {"initial", "converge", "simplify", "outgoing-repair"},
            f"checkpoint route omitted a valid planning stage: {args}",
        )
        approved_paths = self._planning_paths(runtime)
        policy = json.loads(
            (self.root / ".specify" / "memory" / "planning-authorization.json").read_text(encoding="utf-8")
        )
        branch_before = self._git("branch", "--show-current").stdout.strip()
        base_head = self._git("rev-parse", "HEAD").stdout.strip()
        self._expect(policy["delivery_run"] == self._run_id(), "planning authorization belongs to another run")
        self._expect(policy["branch"] == branch_before, "planning branch changed after project authorization")
        self._expect(base_head == pending["snapshot"]["head"], "planning HEAD changed before staging")
        self._expect(set(approved_paths) == set(policy["approved_paths"]), "planning paths exceed exact project authorization")
        self._expect(all((self.root / path).is_file() for path in approved_paths), "checkpoint approved a missing path")
        approved_bytes = {path: (self.root / path).read_bytes() for path in approved_paths}
        self._write(
            runtime.local / f"planning-inputs-{pending['ticket']}.json",
            json.dumps(
                {
                    "schema_version": 1,
                    "delivery_run": self._run_id(),
                    "lane": "feature",
                    "authorization": policy["statement"],
                    "paths": [
                        {"path": path, "source_owner": "decision" if path.startswith(".specify/decisions/") else "core"}
                        for path in approved_paths
                    ],
                },
                indent=2,
            ) + "\n",
        )
        status = self._git("status", "--short", "--untracked-files=all").stdout
        changed = {
            line[3:].strip().replace("\\", "/")
            for line in status.splitlines()
            if len(line) >= 4
        }
        unexpected = changed - set(approved_paths)
        self._expect(not unexpected, f"checkpoint would absorb unapproved paths: {sorted(unexpected)}")
        self._expect(bool(changed), "checkpoint must exercise an actual project-authorized planning commit")
        self._git("add", "--", *approved_paths)
        staged = {
            line.strip().replace("\\", "/")
            for line in self._git("diff", "--cached", "--name-only").stdout.splitlines()
            if line.strip()
        }
        self._expect(staged <= set(approved_paths), f"checkpoint staged an unapproved path: {sorted(staged - set(approved_paths))}")
        self._git("commit", "--quiet", "-m", f"planning checkpoint {planning_stage}")
        self._expect(self._git("status", "--porcelain").stdout == "", "planning commit left a dirty entry")
        self._expect(
            approved_bytes == {path: (self.root / path).read_bytes() for path in approved_paths},
            "planning commit changed displayed planning bytes",
        )
        commit = self._git("rev-parse", "HEAD").stdout.strip()
        committed_paths = self._git("diff", "--name-only", base_head, commit).stdout.splitlines()
        self._expect(set(committed_paths) <= set(approved_paths), "planning commit absorbed an unapproved path")
        self.checkpoint_records.append(
            {"planning_stage": planning_stage, "base_head": base_head, "commit": commit, "paths": committed_paths}
        )
        branch = self._git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        authorization_text = (
            f"PROJECT_AUTHORIZATION: {policy['statement']}\n"
            "SOURCE: .specify/memory/planning-authorization.json\n"
            f"EXACT_PATHS: {', '.join(approved_paths)}\n"
        )
        authorization_path = runtime.local / f"planning-authorization-{len(self.checkpoint_stages) + 1}.txt"
        self._write(authorization_path, authorization_text)
        report = runtime.local / f"native-checkpoint-{len(self.checkpoint_stages) + 1}.md"
        self._write(
            report,
            "SD_CORE_HANDOFF: PASS\n"
            f"core_stage: {planning_stage}\n"
            f"delivery_run: {self._run_id()}\n"
            f"approved_paths: {', '.join(approved_paths)}\n"
            f"branch: {branch}\n"
            f"base_head: {base_head}\n"
            f"planning_commit: {commit}\n"
            "authorization: PROJECT_AUTHORIZATION\n",
        )
        state_after = runtime.load()
        analyze_fingerprint = state_after["stages"].get("analyze", {}).get("output_fingerprint")
        data = {
            "planning_stage": planning_stage,
            "approved_paths": approved_paths,
            "branch": branch,
            "base_head": base_head,
            "planning_commit": commit,
            "authorization": authorization_text.strip(),
            "authorization_statement": authorization_text.strip(),
            "authorization_evidence": {
                "path": runtime.relative(authorization_path),
                "sha256": RUNTIME.digest(authorization_path.read_bytes()),
            },
            "content_fingerprint": pending["snapshot"]["fingerprint"],
            "analyze_fingerprint": analyze_fingerprint,
            "task_ids": re.findall(
                r"^\s*-\s*\[[ xX]\]\s+(T\d+)\b",
                runtime.bound_file(state_after, "tasks").read_text(encoding="utf-8"),
                re.MULTILINE,
            ),
            "slice_mapping": "S1:all-current-tasks",
            "approval_association": "unchanged Analyze snapshot associated with the exact planning commit",
        }
        result_path_text = self.token(args, "runtime_result")
        self._expect(result_path_text is not None, "checkpoint omitted runtime_result")
        self._save_result(runtime, pending, report, "pass", data, self.root / str(result_path_text))
        self.planning_commits.append(commit)
        self.checkpoint_stages.append(str(planning_stage))

    def _apply_simplification(self, args: str) -> None:
        self._expect(self.lane == "feature", "simplification application must be lane-owned by Feature")
        self._expect("action=apply-simplification" in args, "wrong simplification route action")
        runtime = self._runtime()
        state = runtime.load()
        accepted = runtime.accepted_candidates(state)
        simplify = state["stages"].get("simplify", {})
        candidates = simplify.get("data", {}).get("candidates", [])
        self._expect(candidates == accepted, "route did not receive the exact runtime-accepted candidate IDs")
        self._expect(state["approvals"]["simplify"]["choice"] == "approve", "route bypassed the recorded Simplify gate choice")
        candidate_hash = simplify.get("data", {}).get("candidate_hash")
        self._expect(isinstance(candidate_hash, str), "simplification result lacks canonical candidate_hash")
        self.candidate_hash = candidate_hash
        self.simplify_applied = True
        self.apply_simplification_calls += 1
        source = self.root / "src" / "app.py"
        self._write(
            source,
            source.read_text(encoding="utf-8") + "# accepted simplification: " + ", ".join(accepted) + "\n",
        )
        self._write(
            runtime.local / "simplification-application.txt",
            "Applied accepted candidates through the lane owner: " + ", ".join(candidates) + "\n",
        )

    def _verify_simplification(self, args: str) -> None:
        self._expect(self.simplify_applied, "Simplify verify ran before route application")
        runtime = self._runtime()
        accepted = runtime.accepted_candidates(runtime.load())
        self._expect(accepted == self.simplify_candidates, "Simplify verify scope differs from accepted candidate IDs")
        self._expect(
            (runtime.directory / "simplifications.md").read_bytes() == self.simplification_proposal,
            "Simplify application must preserve the immutable native proposal",
        )
        self.simplify_verify_calls += 1

    def _task_owners(self, runtime: Any, task: str) -> None:
        for stage in ("quality", "standards", "review"):
            pending = runtime.begin(stage, scope=f"task-{task}")
            report = runtime.local / f"task-{task}-{stage}.md"
            report.write_text(f"{stage.upper()}_VERDICT: pass\n", encoding="utf-8")
            if stage == "quality":
                log = runtime.local / f"check-{task}.txt"
                log.write_text("native task check passed\n", encoding="utf-8")
                data = {"checks": [{"command": "task-fixture-check", "exit_code": 0, "evidence": {"path": runtime.relative(log), "sha256": RUNTIME.digest(log.read_bytes())}}]}
            elif stage == "standards":
                data = {"coverage": "complete"}
            else:
                data = {"coverage": "complete", "dimensions": {key: "pass" for key in RUNTIME.DIMENSIONS}, "independence": "independent", "findings": [], "repairable": False}
            self._save_result(runtime, pending, report, "pass", data, runtime.local / f"result-{stage}.json")
            runtime.record(stage)

    def _ralph(self, args: str) -> None:
        self._expect(self.lane == "feature", "Ralph must run only for a Feature fixture")
        runtime = self._runtime()
        state = runtime.load()
        self._expect(self._git("status", "--porcelain").stdout == "", "Ralph entry was dirty")
        self._expect(state.get("execution_head") == self._git("rev-parse", "HEAD").stdout.strip(), "Ralph bypassed the helper planning gate")
        runtime.require("analyze")
        tasks = runtime.bound_file(state, "tasks")
        text = tasks.read_text(encoding="utf-8")
        pending_tasks = re.findall(r"^\s*-\s*\[ \]\s+(T\d+)\b", text, re.MULTILINE)
        self._expect(bool(pending_tasks), "Ralph dispatched without an unchecked Core task")
        self.ralph_tasks.append(pending_tasks)
        source = self.root / "src" / "app.py"
        for task_id in pending_tasks:
            branch = self._git("branch", "--show-current").stdout.strip()
            runtime.task_start(task_id, branch, [self._relative(source)])
            source.write_text(
                source.read_text(encoding="utf-8") + f"# green Ralph task {task_id}\n",
                encoding="utf-8",
            )
            self._task_owners(runtime, task_id)
            applicability = runtime.local / f"docs-refresh-{task_id}.json"
            applicability.write_text(json.dumps({"required": False, "reason": "Fixture changes only internal behavior."}), encoding="utf-8")
            runtime.task_gate(task_id, runtime.relative(applicability))
            text = re.sub(rf"(- \[) (\]\s+{re.escape(task_id)}\b)", r"\g<1>x\g<2>", tasks.read_text(encoding="utf-8"))
            tasks.write_text(text, encoding="utf-8")
            self._git("add", "--", self._relative(source), runtime.relative(tasks))
            self._git("commit", "--quiet", "-m", f"feat(ralph): {task_id} green task")
            runtime.task_record(task_id, self._git("rev-parse", "HEAD").stdout.strip())
        runtime.require("task-closure")
        self.ralph_calls += 1
        self._expect("- [ ]" not in tasks.read_text(encoding="utf-8"), "fake Ralph left an unchecked task")

    def _bug_assess(self, args: str) -> None:
        self._expect(self.lane == "bugfix", "Bug assessment used outside Bugfix")
        slug = self.token(args, "slug")
        self._expect(slug == self.bug_slug, f"assessment used wrong Bug slug: {args}")
        packet = self.root / ".specify" / "delivery" / self._run_id(args) / "exploration.md"
        packet_before = packet.read_bytes()
        assessment = self.root / ".specify" / "bugs" / self.bug_slug / "assessment.md"
        before = {
            self._relative(path): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file() and ".git" not in path.relative_to(self.root).parts
        }
        self._write(
            assessment,
            f"BUG_SLUG: {self.bug_slug}\nROOT_CAUSE: bounded fixture defect\n"
            "REPRODUCTION: native red evidence exists\nREPAIR_SCOPE: src/app.py\n",
        )
        after = {
            self._relative(path): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file() and ".git" not in path.relative_to(self.root).parts
        }
        changed = {path for path in set(before) | set(after) if before.get(path) != after.get(path)}
        self._expect(changed == {self._relative(assessment)}, f"Bug assess wrote outside its exact output: {changed}")
        self._expect(packet.read_bytes() == packet_before, "Bug assess must not edit the Delivery packet")
        self.assessment_path = assessment
        self.official_reports[self._relative(assessment)] = assessment.read_bytes()

    def _bug_fix(self, args: str) -> None:
        self._expect(self.lane == "bugfix", "Bug fix used outside Bugfix")
        self._expect(self.token(args, "slug") == self.bug_slug, "Bug fix lost the explicit native slug")
        runtime = self._runtime()
        state = runtime.load()
        assessment = runtime.bound_file(state, "assessment")
        self._expect(assessment == self.root / ".specify" / "bugs" / self.bug_slug / "assessment.md", "Bug fix used a guessed assessment")
        source = self.root / "src" / "app.py"
        source.write_text(source.read_text(encoding="utf-8") + "# official bug fix\n", encoding="utf-8")
        report = self.root / ".specify" / "bugs" / self.bug_slug / "fix-report.md"
        self._expect(not report.exists(), "official Bug fix report was unexpectedly overwritten")
        self._write(report, "OFFICIAL_FIX_REPORT: pass\nred reproduction fixed\n")
        self.fix_report = report
        self.official_reports[self._relative(report)] = report.read_bytes()

    def _bug_test(self, args: str) -> None:
        self._expect(self.lane == "bugfix", "Bug test used outside Bugfix")
        self._expect(self.token(args, "slug") == self.bug_slug, "Bug test lost the explicit native slug")
        self._expect(self.assessment_path is not None and self.assessment_path.is_file(), "Bug test lacks the exact assessment")
        report = self.root / ".specify" / "bugs" / self.bug_slug / "test-report.md"
        self._expect(not report.exists(), "official Bug test report was unexpectedly overwritten")
        self._write(report, "OFFICIAL_REGRESSION_REPORT: pass\nred and green evidence retained\n")
        self.test_report = report
        self.official_reports[self._relative(report)] = report.read_bytes()

    def dispatch(self, command, integration, model, args, context, *extra, **kwargs):
        self.current_args = args
        self.calls.append(command)
        self.dispatches.append((command, args))
        self._expect(context.project_root == str(self.root), "fake consumer received the wrong project root")
        self._expect("{{" not in args, f"command received unresolved template syntax: {args}")
        for relative, original in self.official_reports.items():
            self._expect((self.root / relative).read_bytes() == original, f"original Bug report changed: {relative}")

        if command == "speckit.delivery.explore":
            self._write_exploration(args)
        elif command == "speckit.specify":
            self._write_specify(args)
        elif command == "speckit.clarify":
            self._write_stage_result("clarify")
        elif command == "speckit.plan":
            self._write(self._feature_dir(args) / "plan.md", "# Plan\n\nApproved fixture design.\n")
        elif command == "speckit.tasks":
            self._write(
                self._feature_dir(args) / "tasks.md",
                "# Tasks\n\n- [ ] T001 Implement the approved behavior\n",
            )
        elif command == "speckit.delivery.context":
            self._write(
                self._run_dir(args) / "code-context.md",
                "CODE_CONTEXT: found\nENTRY_POINTS: src/app.py\n",
            )
        elif command == "speckit.decision.propose":
            if self.mutate_after_review:
                self._ensure_adr(args)
        elif command == "speckit.decision.context":
            if self.lane == "bugfix" and "mode=resolve" in args:
                self._ensure_adr(args)
        elif command == "speckit.delivery.slice":
            if "action=record-approval" in args:
                slices = self._run_dir(args) / "slices.md"
                self._expect(slices.is_file(), "slice approval record has no canonical slices.md")
                self._expect("slice_approval=approve" in args, "slice approval lost the gate choice")
                self._write(
                    slices,
                    slices.read_text(encoding="utf-8")
                    + "SLICE_APPROVAL: approved\nApproved by: fixture-user\n",
                )
            else:
                runtime = self._runtime()
                tasks = runtime.bound_file(runtime.load(), "tasks").read_text(encoding="utf-8")
                task_ids = re.findall(r"^\s*-\s*\[[ xX]\]\s+(T\d+)\b", tasks, re.MULTILINE)
                mapping = "S1: " + ", ".join(task_ids)
                self._write(
                    self._run_dir(args) / "slices.md",
                    f"SLICE_PLAN_FINGERPRINT: {RUNTIME.digest(mapping.encode('utf-8'))}\n"
                    + f"SLICE_APPROVAL: pending\n{mapping}\n",
                )
        elif command == "speckit.analyze":
            self._write_stage_result("analyze")
        elif command == "speckit.delivery.route":
            action = self.token(args, "action")
            if action == "checkpoint":
                self._write_checkpoint(args)
            elif action == "bind-assessment":
                self._expect(self.lane == "bugfix", "assessment binding used outside the Bugfix lane")
                runtime = self._runtime()
                state = runtime.load()
                assessment = runtime.bound_file(state, "assessment")
                receipt = state["approvals"].get("assessment", {})
                self._expect(self.token(args, "assessment_approval") == "approve", "assessment route lost the actual gate choice")
                self._expect(receipt.get("choice") == "approve", "assessment route bypassed its runtime gate receipt")
                self._expect(
                    receipt.get("inputs", {}).get(runtime.relative(assessment)) == RUNTIME.digest(assessment.read_bytes()),
                    "assessment route used different bytes from the approved native assessment",
                )
                packet = self._run_dir(args) / "exploration.md"
                self._write(
                    packet,
                    packet.read_text(encoding="utf-8")
                    + f"ASSESSMENT_SHA256: {RUNTIME.digest(assessment.read_bytes())}\n"
                    + "ASSESSMENT_APPROVAL: approve\n",
                )
            elif action == "apply-simplification":
                self._apply_simplification(args)
            else:
                raise AssertionError(f"unexpected route action: {args}")
        elif command == "speckit.ralph.run":
            self._ralph(args)
        elif command == "speckit.converge":
            self._write_stage_result("converge")
        elif command in {
            "speckit.quality.check",
            "speckit.review.standards",
            "speckit.review.run",
            "speckit.simplify.scan",
        }:
            stage = self.token(args, "runtime_stage")
            self._expect(stage is not None, f"{command} omitted runtime_stage")
            self._write_stage_result(str(stage))
        elif command == "speckit.simplify.verify":
            self._verify_simplification(args)
            stage = self.token(args, "runtime_stage")
            self._expect(stage == "simplify-verify", f"Simplify Verify omitted runtime_stage: {args}")
            self._write_stage_result("simplify-verify")
        elif command == "speckit.bug.assess":
            self._bug_assess(args)
        elif command == "speckit.bug.fix":
            self._bug_fix(args)
        elif command == "speckit.bug.test":
            self._bug_test(args)
        elif command == "speckit.delivery.review-fix":
            runtime = self._runtime()
            budget = runtime.load()["attempts"].get("review:outgoing-diff", {})
            expected_attempt = self.repair_calls + 1
            self._expect(self.token(args, "attempt") == str(expected_attempt), "repair owner lost its reserved attempt")
            self._expect(budget.get("used") == expected_attempt and budget.get("pending") == expected_attempt, "repair edited before the real helper reserved its attempt")
            self.repair_calls += 1
            source = self.root / "src" / "app.py"
            source.write_text(
                source.read_text(encoding="utf-8") + f"# bounded repair {self.repair_calls}\n",
                encoding="utf-8",
            )
            if self.lane == "bugfix":
                self._write(
                    self._run_dir(args) / "repairs" / f"attempt-{self.repair_calls}.md",
                    f"REPAIR_ATTEMPT: {self.repair_calls}\n",
                )
        elif command == "speckit.decision.finalize":
            if self.mutate_after_review:
                adr = self._ensure_adr(args)
                self._write(
                    adr,
                    adr.read_text(encoding="utf-8").replace("ADR_STATUS: Proposed", "ADR_STATUS: Accepted"),
                )
        elif command == "speckit.decision.check":
            if self.lane == "bugfix" and self.mutate_after_review:
                adr = self._ensure_adr(args)
                self._write(
                    adr,
                    adr.read_text(encoding="utf-8") + "ADR_CHECK: refreshed\n",
                )
        elif command == "speckit.evidence.collect":
            run = self._run_id(args)
            evidence = self._run_dir(args) / "evidence.md"
            text = (
                f"- **delivery_run**: {run}\n"
                f"- **lane**: {self.lane}\n"
                f"- **evidence_path**: .specify/delivery/{run}/evidence.md\n"
            )
            if self.lane == "bugfix":
                text += (
                    f"- **bug_slug**: {self.bug_slug}\n"
                    f"- **assessment_path**: .specify/bugs/{self.bug_slug}/assessment.md\n"
                )
            text += "- **pull_request**: pending\n"
            self._write(evidence, text)
        elif command == "speckit.delivery.handoff":
            self._write(
                self._run_dir(args) / "pull-request.md",
                f"# Proposed {self.lane} handoff\n\nVerified full workflow fixture.\n",
            )
        elif command == "speckit.docs-sync.package-readme":
            if self.docs_change:
                self._write(
                    self.root / "README.md",
                    f"# Fixture package\n\nUpdated {self.lane} documentation.\n",
                )
        elif command in {
            "speckit.delivery.doctor",
            "speckit.quality.brief",
            "speckit.docs-sync.run",
        }:
            pass
        else:
            return {"exit_code": 1, "stdout": "", "stderr": f"unexpected full fake command: {command}"}
        return {"exit_code": 0, "stdout": "", "stderr": ""}


class WorkflowRuntimeTest(unittest.TestCase):
    def temporary_project(
        self, cap: int = 3, convergence_cap: int = 3
    ) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory(
            prefix="workflow-runtime-",
            dir=os.environ.get("TMP") or os.environ.get("TEMP"),
        )
        root = Path(temporary.name)
        self.addCleanup(temporary.cleanup)
        self.git(root, "init", "--quiet")
        self.git(root, "config", "user.email", "workflow-runtime@example.invalid")
        self.git(root, "config", "user.name", "Workflow Runtime Tests")
        exclude = root / ".git" / "info" / "exclude"
        previous_exclude = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
        if "/.specify/workflows/runs/" not in previous_exclude.splitlines():
            exclude.write_text(
                previous_exclude
                + ("\n" if previous_exclude and not previous_exclude.endswith("\n") else "")
                + "/.specify/workflows/runs/\n",
                encoding="utf-8",
            )
        (root / ".specify/extensions/delivery/scripts").mkdir(parents=True)
        for helper in HELPER_SOURCE.parent.glob("delivery_*.py"):
            shutil.copy2(helper, root / ".specify/extensions/delivery/scripts" / helper.name)
        config = root / ".specify/extensions/delivery/delivery-config.yml"
        config.write_text(
            "schema_version: \"1.0\"\n"
            f"max_review_fix_rounds: {cap}\n"
            f"max_convergence_rounds: {convergence_cap}\n",
            encoding="utf-8",
        )
        (root / "src").mkdir(parents=True)
        (root / "src/app.py").write_text("VALUE = 1\n", encoding="utf-8")
        self.git(root, "add", ".")
        self.git(root, "commit", "-m", "fixture")
        return temporary, root

    @staticmethod
    def git(root: Path, *args: str) -> None:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
        if result.returncode:
            raise AssertionError(result.stderr)

    @staticmethod
    def runtime_python() -> str:
        return "py -3" if os.name == "nt" else "python"

    @contextlib.contextmanager
    def shell_transport(self):
        """Adapt real shell execution and tolerate a host file-scanner race.

        The cmd /d adapter bypasses this host's broken AutoRun hook. The narrow
        engine atomic-write retry covers only a transient Windows PermissionError
        from ``os.replace`` while the host scanner holds the destination; product
        helper/workflow logic is not retried or masked.
        """
        shell_module = importlib.import_module("specify_cli.workflows.step.shell")
        engine_module = importlib.import_module("specify_cli.workflows.engine")
        real_subprocess = subprocess
        original_atomic = engine_module.RunState._atomic_write_json

        def run(command, *args, **kwargs):
            if os.name == "nt" and kwargs.get("shell"):
                command_text = str(command)
                kwargs = {**kwargs, "shell": False, "encoding": "mbcs"}
                command = ["cmd.exe", "/d", "/c", command_text]
            return real_subprocess.run(command, *args, **kwargs)

        def atomic(path, data):
            for attempt in range(5):
                try:
                    return original_atomic(path, data)
                except PermissionError:
                    if os.name != "nt" or attempt == 4:
                        raise
                    time.sleep(0.05 * (attempt + 1))

        proxy = types.SimpleNamespace(run=run, TimeoutExpired=subprocess.TimeoutExpired)
        with (
            patch.object(shell_module, "subprocess", proxy),
            patch.object(engine_module.RunState, "_atomic_write_json", staticmethod(atomic)),
        ):
            yield

    def run_lightweight(self, fake: FakeConsumers, *, run: str = "runtime-run"):
        definition = WorkflowDefinition.from_yaml(ROOT / "workflows/lightweight-delivery/workflow.yml")
        temporary, root = self.temporary_project()
        # Move the fake's root binding after the project is known.
        fake.root = root
        engine = WorkflowEngine(root)
        self.assertEqual(engine.validate(definition), [])
        inputs = {
            "delivery_run": run,
            "change": "change one mechanical behavior",
            "integration": "generic",
            "runtime_python": self.runtime_python(),
        }
        with (
            self.shell_transport(),
            patch.object(engine, "_load_integrations", return_value=None),
            patch.object(CommandStep, "_try_dispatch", side_effect=fake.dispatch),
            patch.object(GateStep, "_prompt", return_value="approve"),
            patch("sys.stdin.isatty", return_value=True),
        ):
            state = engine.execute(definition, inputs=inputs, run_id="host-run")
        return temporary, root, state

    def _run_full_workflow(
        self,
        workflow_id: str,
        fake: FullWorkflowConsumers,
        inputs: dict[str, Any],
        *,
        cap: int = 3,
        convergence_cap: int = 3,
    ):
        definition = WorkflowDefinition.from_yaml(
            ROOT / "workflows" / workflow_id / "workflow.yml"
        )
        temporary, root = self.temporary_project(
            cap=cap, convergence_cap=convergence_cap
        )
        fake.root = root
        if fake.lane == "feature":
            run = inputs["delivery_run"]
            feature_prefix = f".specify/features/feature-{run}"
            run_prefix = f".specify/delivery/{run}"
            authorization = {
                "delivery_run": run,
                "branch": fake._git("branch", "--show-current").stdout.strip(),
                "statement": "Fixture project policy authorizes exact declared planning commits before each clean execution entry.",
                "approved_paths": [
                    f"{feature_prefix}/spec.md",
                    f"{feature_prefix}/plan.md",
                    f"{feature_prefix}/tasks.md",
                    f"{run_prefix}/exploration.md",
                    f"{run_prefix}/code-context.md",
                    f"{run_prefix}/slices.md",
                ],
            }
            if fake.mutate_after_review:
                authorization["approved_paths"].append(f".specify/decisions/{run}.md")
            policy = root / ".specify" / "memory" / "planning-authorization.json"
            fake._write(policy, json.dumps(authorization, indent=2) + "\n")
            self.git(root, "add", "--", ".specify/memory/planning-authorization.json")
            self.git(root, "commit", "--quiet", "-m", "project authorizes exact planning paths")
        engine = WorkflowEngine(root)
        self.assertEqual(engine.validate(definition), [])
        with (
            self.shell_transport(),
            patch.object(engine, "_load_integrations", return_value=None),
            patch.object(CommandStep, "_try_dispatch", side_effect=fake.dispatch),
            patch.object(GateStep, "_prompt", return_value="approve"),
            patch("sys.stdin.isatty", return_value=True),
        ):
            state = engine.execute(
                definition,
                inputs=inputs,
                run_id=f"host-{inputs['delivery_run']}",
            )
        return temporary, root, state

    def run_feature(
        self,
        fake: FullWorkflowConsumers,
        *,
        run: str = "feature-full",
        cap: int = 3,
        convergence_cap: int = 3,
    ):
        return self._run_full_workflow(
            "feature-delivery",
            fake,
            {
                "delivery_run": run,
                "spec": "add bounded feature behavior",
                "integration": "generic",
                "runtime_python": self.runtime_python(),
                "with_docs_sync": True,
            },
            cap=cap,
            convergence_cap=convergence_cap,
        )

    def run_bugfix(
        self,
        fake: FullWorkflowConsumers,
        *,
        run: str = "bugfix-full",
        bug_slug: str = "actual-bug",
        cap: int = 3,
    ):
        fake.bug_slug = bug_slug
        return self._run_full_workflow(
            "bugfix-delivery",
            fake,
            {
                "bug_slug": bug_slug,
                "delivery_run": run,
                "report": "repair bounded fixture defect",
                "integration": "generic",
                "runtime_python": self.runtime_python(),
            },
            cap=cap,
        )

    def assert_workflow_status(self, state, expected: str) -> None:
        failures = {
            key: result
            for key, result in state.step_results.items()
            if result.get("status") == "failed"
        }
        self.assertEqual(
            state.status.value,
            expected,
            f"workflow error={state.error!r}\nfailed step results:\n"
            + json.dumps(failures, indent=2, ensure_ascii=False),
        )

    def assert_failed_at(self, state, step_id: str) -> None:
        failed = {
            key: result
            for key, result in state.step_results.items()
            if result.get("status") == "failed"
        }
        self.assertTrue(
            any(key == step_id or key.endswith(":" + step_id) for key in failed),
            f"expected failure at {step_id}; actual failed step results:\n"
            + json.dumps(failed, indent=2, ensure_ascii=False),
        )

    def assert_runtime_finished(self, root: Path, run: str) -> dict[str, Any]:
        runtime = RUNTIME.Runtime(root, run)
        status = runtime.status()
        self.assertEqual(status["status"], "handoff-ready")
        self.assertEqual(status["pending_stages"], [])
        self.assertTrue(all(value["pending"] is None for value in status["attempts"].values()))
        runtime.require("review")
        self.assertTrue((runtime.directory / "pull-request.md").is_file())
        return runtime.load()

    @staticmethod
    def step_keys(state, suffix: str) -> list[str]:
        return [
            key
            for key in state.step_results
            if key == suffix or key.endswith(f":{suffix}")
        ]

    def test_initial_pass_dispatches_no_repair(self):
        fake = FakeConsumers(Path("."), repairs_to_resolve=0)
        _, root, state = self.run_lightweight(fake)
        self.assert_workflow_status(state, "completed")
        self.assertEqual(fake.calls.count("speckit.review.run"), 1)
        self.assertEqual(fake.repair_calls, 0)
        self.assertIn("speckit.evidence.collect", fake.calls)
        self.assertIn("speckit.delivery.handoff", fake.calls)
        self.assertTrue((root / ".specify/delivery/runtime-run/evidence.md").is_file())

    def test_one_repair_stops_after_passing_rereview(self):
        fake = FakeConsumers(Path("."), repairs_to_resolve=1)
        _, _, state = self.run_lightweight(fake)
        self.assert_workflow_status(state, "completed")
        self.assertEqual(fake.calls.count("speckit.review.run"), 2)
        self.assertEqual(fake.repair_calls, 1)

    def test_configured_and_hard_caps_fail_without_handoff(self):
        for cap in (1, 3):
            with self.subTest(cap=cap):
                fake = FakeConsumers(Path("."), repairs_to_resolve=999)
                state = self.run_lightweight_with_cap(fake, cap)
                self.assert_workflow_status(state, "failed")
                self.assertEqual(fake.calls.count("speckit.review.run"), cap + 1)
                self.assertEqual(fake.repair_calls, cap)
                self.assertNotIn("speckit.evidence.collect", fake.calls)
                self.assertNotIn("speckit.delivery.handoff", fake.calls)

    def run_lightweight_with_cap(self, fake: FakeConsumers, cap: int):
        definition = WorkflowDefinition.from_yaml(ROOT / "workflows/lightweight-delivery/workflow.yml")
        temporary, root = self.temporary_project(cap=cap)
        fake.root = root
        engine = WorkflowEngine(root)
        self.assertEqual(engine.validate(definition), [])
        with (
            self.shell_transport(),
            patch.object(engine, "_load_integrations", return_value=None),
            patch.object(CommandStep, "_try_dispatch", side_effect=fake.dispatch),
            patch.object(GateStep, "_prompt", return_value="approve"),
            patch("sys.stdin.isatty", return_value=True),
        ):
            return engine.execute(
                definition,
                inputs={
                    "delivery_run": "runtime-run",
                    "change": "bounded change",
                    "integration": "generic",
                    "runtime_python": self.runtime_python(),
                },
                run_id="host-run",
            )

    def test_missing_or_stale_review_result_blocks_before_repair(self):
        for stale in (False, True):
            with self.subTest(stale=stale):
                fake = FakeConsumers(
                    Path("."),
                    repairs_to_resolve=1,
                    omit_first_review_result=not stale,
                    stale_recheck_result=stale,
                )
                if stale:
                    # Make the first result valid and leave it in place on the re-review.
                    fake.omit_first_review_result = False
                _, _, state = self.run_lightweight(fake, run=f"result-{stale}")
                self.assert_workflow_status(state, "failed")
                self.assertEqual(fake.calls.count("speckit.review.run"), 2 if stale else 1)
                self.assertEqual(fake.repair_calls, 1 if stale else 0)
                self.assertNotIn("speckit.evidence.collect", fake.calls)

    def test_converged_checkbox_only_result_cannot_skip_closure_audit(self):
        temporary, root = self.temporary_project()
        feature = root / ".specify/features/converged"
        feature.mkdir(parents=True)
        for name in ("spec.md", "plan.md", "tasks.md"):
            (feature / name).write_text(
                "# fixture\n" if name != "tasks.md" else "- [x] T001 fixture\n",
                encoding="utf-8",
            )
        self.git(root, "add", ".")
        self.git(root, "commit", "-m", "feature planning")
        tasks_before = (feature / "tasks.md").read_bytes()
        runtime_python = self.runtime_python()
        workflow = {
            "schema_version": "1.0",
            "workflow": {"id": "convergence-probe", "name": "Convergence probe", "version": "1.0.0"},
            "inputs": {"delivery_run": {"type": "string", "required": True}},
            "steps": [
                {"id": "init", "type": "shell", "run": runtime_python + " .specify/extensions/delivery/scripts/delivery_runtime.py init --run {{ inputs.delivery_run }} --lane feature"},
                {"id": "bind", "type": "shell", "run": runtime_python + " .specify/extensions/delivery/scripts/delivery_runtime.py bind --run {{ inputs.delivery_run }} --feature-dir .specify/features/converged"},
                {"id": "begin", "type": "shell", "run": runtime_python + " .specify/extensions/delivery/scripts/delivery_runtime.py begin --run {{ inputs.delivery_run }} --stage converge"},
                {"id": "converge", "command": "speckit.converge", "integration": "generic", "input": {"args": "delivery_run={{ inputs.delivery_run }} runtime_stage=converge runtime_result=.specify/delivery/{{ inputs.delivery_run }}/runtime/result-converge.json"}},
                {"id": "record", "type": "shell", "run": runtime_python + " .specify/extensions/delivery/scripts/delivery_runtime.py record --run {{ inputs.delivery_run }} --stage converge"},
                {"id": "needs", "type": "shell", "run": runtime_python + " .specify/extensions/delivery/scripts/delivery_runtime.py needs --run {{ inputs.delivery_run }} --kind convergence"},
                {"id": "conditional-work", "type": "if", "condition": "{{ steps.needs.output.stdout == 'true' }}", "then": [
                    {"id": "analyze", "command": "speckit.analyze", "integration": "generic", "input": {"args": "delivery_run={{ inputs.delivery_run }}"}},
                    {"id": "ralph", "command": "speckit.ralph.run", "integration": "generic", "input": {"args": "delivery_run={{ inputs.delivery_run }} lane=feature"}},
                ]},
                {"id": "require", "type": "shell", "run": runtime_python + " .specify/extensions/delivery/scripts/delivery_runtime.py require --run {{ inputs.delivery_run }} --kind convergence"},
            ],
        }
        workflow_path = root / "convergence-probe.yml"
        workflow_path.write_text(yaml.safe_dump(workflow, sort_keys=False), encoding="utf-8")
        definition = WorkflowDefinition.from_yaml(workflow_path)
        fake = FakeConsumers(root)
        engine = WorkflowEngine(root)
        self.assertEqual(engine.validate(definition), [])
        with (
            self.shell_transport(),
            patch.object(engine, "_load_integrations", return_value=None),
            patch.object(CommandStep, "_try_dispatch", side_effect=fake.dispatch),
        ):
            state = engine.execute(definition, inputs={"delivery_run": "converged-run"}, run_id="host-converged")
        self.assert_workflow_status(state, "failed")
        self.assertEqual(fake.calls, ["speckit.converge"])
        self.assertNotIn("speckit.ralph.run", fake.calls)
        self.assertEqual((root / ".specify/features/converged/tasks.md").read_bytes(), tasks_before)

    def test_full_feature_initial_pass_has_one_converge_and_no_repair(self):
        fake = FullWorkflowConsumers(Path("."), lane="feature")
        _, root, state = self.run_feature(fake, run="feature-initial")
        self.assert_workflow_status(state, "completed")
        self.assert_runtime_finished(root, "feature-initial")
        self.assertEqual(fake.converge_calls, 1)
        self.assertEqual(len(fake.convergence_snapshots), 1)
        self.assertEqual(*fake.convergence_snapshots[0])
        self.assertEqual(fake.ralph_tasks, [["T001"]])
        self.assertEqual(fake.analyze_calls, 1)
        self.assertEqual(fake.ralph_calls, 1)
        self.assertEqual(fake.review_calls, 1)
        self.assertEqual(fake.repair_calls, 0)
        self.assertEqual(fake.stage_counts.get("quality"), 1)
        self.assertEqual(fake.stage_counts.get("standards"), 1)
        self.assertEqual(fake.checkpoint_stages, ["initial"])
        self.assertNotIn("speckit.quality.brief", fake.calls)
        self.assertIn("speckit.evidence.collect", fake.calls)
        self.assertIn("speckit.delivery.handoff", fake.calls)
        packet = root / ".specify" / "delivery" / "feature-initial" / "exploration.md"
        markers = [
            line
            for line in packet.read_text(encoding="utf-8").splitlines()
            if line.startswith("FEATURE_DIR:")
        ]
        self.assertEqual(len(markers), 1)
        runtime = RUNTIME.Runtime(root, "feature-initial")
        bindings = runtime.load()["bindings"]
        self.assertTrue((root / bindings["spec"]).is_file())
        self.assertTrue((root / bindings["plan"]).is_file())
        self.assertTrue((root / bindings["tasks"]).is_file())
        self.assertNotIn("- [ ]", (root / bindings["tasks"]).read_text(encoding="utf-8"))

    def test_feature_docs_change_refreshes_quality_and_standards_before_review(self):
        fake = FullWorkflowConsumers(Path("."), lane="feature", docs_change=True)
        _, _, state = self.run_feature(fake, run="feature-docs-refresh")
        self.assert_workflow_status(state, "completed")
        self.assertEqual(fake.stage_counts.get("quality"), 2)
        self.assertEqual(fake.stage_counts.get("standards"), 2)
        self.assertEqual(fake.review_calls, 1)
        quality_calls = [
            index
            for index, command in enumerate(fake.calls)
            if command == "speckit.quality.check"
        ]
        standards_calls = [
            index
            for index, command in enumerate(fake.calls)
            if command == "speckit.review.standards"
        ]
        review_index = fake.calls.index("speckit.review.run")
        self.assertEqual(len(quality_calls), 2)
        self.assertEqual(len(standards_calls), 2)
        self.assertLess(quality_calls[-1], review_index)
        self.assertLess(standards_calls[-1], review_index)
        self.assertIn("speckit.delivery.handoff", fake.calls)

    def test_full_feature_one_appended_convergence_runs_one_append_analyze_and_ralph(self):
        fake = FullWorkflowConsumers(
            Path("."), lane="feature", append_convergence=True
        )
        _, root, state = self.run_feature(fake, run="feature-appended")
        self.assert_workflow_status(state, "completed")
        stored = self.assert_runtime_finished(root, "feature-appended")
        self.assertEqual(stored["attempts"]["convergence:outgoing-diff"]["used"], 1)
        self.assertEqual(fake.ralph_tasks, [["T001"], ["T002"]])
        self.assertEqual(len(fake.convergence_snapshots), 2)
        before_append, after_append = fake.convergence_snapshots[0]
        self.assertTrue(after_append.startswith(before_append))
        self.assertNotEqual(before_append, after_append)
        self.assertEqual(*fake.convergence_snapshots[1])
        self.assertEqual(fake.converge_calls, 2)
        self.assertEqual(fake.analyze_calls, 2)
        self.assertEqual(fake.ralph_calls, 2)
        self.assertEqual(fake.review_calls, 1)
        self.assertEqual(fake.repair_calls, 0)
        self.assertEqual(fake.checkpoint_stages, ["initial", "converge"])
        runtime = RUNTIME.Runtime(root, "feature-appended")
        tasks = root / runtime.load()["bindings"]["tasks"]
        self.assertIn("T002", tasks.read_text(encoding="utf-8"))
        self.assertNotIn("- [ ]", tasks.read_text(encoding="utf-8"))
        self.assertEqual(fake.calls.count("speckit.analyze"), 2)
        self.assertEqual(fake.calls.count("speckit.ralph.run"), 2)
        self.assertIn("speckit.delivery.handoff", fake.calls)

    def test_full_feature_configured_review_cap_exhaustion_has_no_handoff(self):
        fake = FullWorkflowConsumers(
            Path("."), lane="feature", repairs_to_resolve=999
        )
        _, root, state = self.run_feature(fake, run="feature-review-cap", cap=1)
        self.assert_workflow_status(state, "failed")
        self.assert_failed_at(state, "review-final")
        self.assertEqual(fake.review_calls, 2)
        self.assertEqual(fake.repair_calls, 1)
        stored = RUNTIME.Runtime(root, "feature-review-cap").load()
        self.assertEqual(stored["attempts"]["review:outgoing-diff"]["used"], 1)
        self.assertIsNone(stored["attempts"]["review:outgoing-diff"]["pending"])
        self.assertEqual(stored["stages"]["review"]["verdict"], "blocked")
        self.assertEqual(stored["stages"]["review"]["data"]["findings"][0]["id"], "F-1")
        self.assertNotIn("speckit.evidence.collect", fake.calls)
        self.assertNotIn("speckit.delivery.handoff", fake.calls)

    def test_full_feature_configured_convergence_cap_leaves_work_open_without_handoff(self):
        fake = FullWorkflowConsumers(Path("."), lane="feature", never_converges=True)
        _, root, state = self.run_feature(
            fake, run="feature-convergence-cap", convergence_cap=1
        )
        self.assert_workflow_status(state, "failed")
        self.assert_failed_at(state, "convergence-require")
        self.assertEqual(fake.converge_calls, 2)
        self.assertEqual(fake.analyze_calls, 2)
        self.assertEqual(fake.ralph_calls, 2)
        self.assertEqual(fake.review_calls, 0)
        runtime = RUNTIME.Runtime(root, "feature-convergence-cap")
        stored = runtime.load()
        self.assertEqual(stored["attempts"]["convergence:outgoing-diff"]["used"], 1)
        self.assertIsNone(stored["attempts"]["convergence:outgoing-diff"]["pending"])
        tasks = root / stored["bindings"]["tasks"]
        self.assertIn("- [ ] T003", tasks.read_text(encoding="utf-8"))
        self.assertNotIn("speckit.evidence.collect", fake.calls)
        self.assertNotIn("speckit.delivery.handoff", fake.calls)
        self.assertFalse((runtime.directory / "evidence.md").exists())

    def test_feature_clarification_gate_only_exists_for_material_decision(self):
        for needs_approval in (False, True):
            with self.subTest(needs_approval=needs_approval):
                run = "feature-clarify-material" if needs_approval else "feature-clarify-none"
                fake = FullWorkflowConsumers(
                    Path("."),
                    lane="feature",
                    clarify_needs_approval=needs_approval,
                )
                _, root, state = self.run_feature(fake, run=run)
                self.assert_workflow_status(state, "completed")
                runtime = RUNTIME.Runtime(root, run)
                approvals = runtime.load()["approvals"]
                if needs_approval:
                    self.assertIn("clarification", approvals)
                    self.assertEqual(approvals["clarification"]["choice"], "approve")
                    self.assertIn(
                        runtime.load()["bindings"]["spec"],
                        approvals["clarification"]["inputs"],
                    )
                    self.assertTrue(self.step_keys(state, "clarify-gate"))
                    self.assertTrue(
                        any(
                            "clarification_choice=approve" in args
                            for command, args in fake.dispatches
                            if command == "speckit.decision.context"
                        )
                    )
                else:
                    self.assertNotIn("clarification", approvals)
                    self.assertFalse(self.step_keys(state, "clarify-gate"))
                    self.assertTrue(
                        any(
                            "clarification_choice=not-required" in args
                            for command, args in fake.dispatches
                            if command == "speckit.decision.context"
                        )
                    )

    def test_feature_simplification_without_candidates_skips_verify_and_application(self):
        fake = FullWorkflowConsumers(Path("."), lane="feature")
        _, _, state = self.run_feature(fake, run="feature-simplify-none")
        self.assert_workflow_status(state, "completed")
        self.assertEqual(fake.simplify_verify_calls, 0)
        self.assertEqual(fake.apply_simplification_calls, 0)
        self.assertNotIn("speckit.simplify.verify", fake.calls)
        self.assertFalse(
            any(
                command == "speckit.delivery.route"
                and "action=apply-simplification" in args
                for command, args in fake.dispatches
            )
        )

    def test_feature_simplification_routes_accepted_candidates_before_verification(self):
        fake = FullWorkflowConsumers(
            Path("."),
            lane="feature",
            simplify_candidates=["S-1"],
        )
        _, root, state = self.run_feature(fake, run="feature-simplify-accepted")
        self.assert_workflow_status(state, "completed")
        self.assertEqual(fake.apply_simplification_calls, 1)
        self.assertEqual(fake.simplify_verify_calls, 1)
        self.assertEqual(fake.converge_calls, 1)
        self.assertEqual(fake.analyze_calls, 1)
        self.assertEqual(fake.ralph_calls, 1)
        self.assertIn("# accepted simplification: S-1", (root / "src/app.py").read_text(encoding="utf-8"))
        apply_args = [
            args
            for command, args in fake.dispatches
            if command == "speckit.delivery.route"
            and "action=apply-simplification" in args
        ]
        self.assertEqual(len(apply_args), 1)
        self.assertIn("action=apply-simplification", apply_args[0])
        runtime = RUNTIME.Runtime(root, "feature-simplify-accepted")
        state_after = runtime.load()
        self.assertEqual(state_after["approvals"]["simplify"]["candidate_ids"], ["S-1"])
        self.assertEqual(
            state_after["stages"]["simplify-verify"]["data"]["accepted_candidates"],
            ["S-1"],
        )
        self.assertEqual(fake.calls.count("speckit.simplify.verify"), 1)
        application_index = next(
            index for index, (command, args) in enumerate(fake.dispatches)
            if command == "speckit.delivery.route" and "action=apply-simplification" in args
        )
        self.assertLess(application_index, fake.calls.index("speckit.simplify.verify"))
        self.assertEqual(fake.calls.count("speckit.delivery.handoff"), 1)

    def test_full_bugfix_initial_pass_uses_exact_assessment_and_no_repair(self):
        fake = FullWorkflowConsumers(
            Path("."), lane="bugfix", bug_slug="bug-exact"
        )
        _, root, state = self.run_bugfix(
            fake, run="bugfix-initial", bug_slug="bug-exact"
        )
        self.assert_workflow_status(state, "completed")
        self.assert_runtime_finished(root, "bugfix-initial")
        self.assertEqual(fake.calls.count("speckit.bug.fix"), 1)
        self.assertEqual(fake.calls.count("speckit.bug.test"), 1)
        self.assertEqual(fake.review_calls, 1)
        self.assertEqual(fake.repair_calls, 0)
        self.assertEqual(
            fake.assessment_path,
            root / ".specify" / "bugs" / "bug-exact" / "assessment.md",
        )
        self.assertTrue(fake.assessment_path.is_file())
        self.assertIn("speckit.delivery.handoff", fake.calls)
        self.assertFalse((root / ".specify" / "features").exists())

    def test_full_bugfix_bounded_repair_preserves_original_fix_and_test_reports(self):
        fake = FullWorkflowConsumers(
            Path("."), lane="bugfix", repairs_to_resolve=1, bug_slug="bug-repair"
        )
        _, root, state = self.run_bugfix(
            fake, run="bugfix-repair", bug_slug="bug-repair"
        )
        self.assert_workflow_status(state, "completed")
        stored = self.assert_runtime_finished(root, "bugfix-repair")
        self.assertEqual(stored["attempts"]["review:outgoing-diff"]["used"], 1)
        self.assertEqual(fake.calls.count("speckit.bug.fix"), 1)
        self.assertEqual(fake.calls.count("speckit.bug.test"), 1)
        self.assertEqual(fake.review_calls, 2)
        self.assertEqual(fake.repair_calls, 1)
        self.assertIsNotNone(fake.fix_report)
        self.assertIsNotNone(fake.test_report)
        self.assertEqual(
            fake.fix_report.read_text(encoding="utf-8"),
            "OFFICIAL_FIX_REPORT: pass\nred reproduction fixed\n",
        )
        self.assertEqual(
            fake.test_report.read_text(encoding="utf-8"),
            "OFFICIAL_REGRESSION_REPORT: pass\nred and green evidence retained\n",
        )
        self.assertIn("speckit.delivery.handoff", fake.calls)
        self.assertIn("speckit.evidence.collect", fake.calls)

    def test_full_bugfix_review_cap_retains_original_reports_and_blocks_handoff(self):
        fake = FullWorkflowConsumers(
            Path("."), lane="bugfix", repairs_to_resolve=999, bug_slug="bug-capped"
        )
        _, root, state = self.run_bugfix(
            fake, run="bugfix-capped", bug_slug="bug-capped", cap=1
        )
        self.assert_workflow_status(state, "failed")
        self.assert_failed_at(state, "review-final")
        self.assertEqual(fake.review_calls, 2)
        self.assertEqual(fake.repair_calls, 1)
        self.assertEqual(fake.calls.count("speckit.bug.fix"), 1)
        self.assertEqual(fake.calls.count("speckit.bug.test"), 1)
        self.assertTrue(fake.official_reports)
        for relative, original in fake.official_reports.items():
            self.assertEqual((root / relative).read_bytes(), original)
        runtime = RUNTIME.Runtime(root, "bugfix-capped")
        stored = runtime.load()
        self.assertEqual(stored["attempts"]["review:outgoing-diff"]["used"], 1)
        self.assertIsNone(stored["attempts"]["review:outgoing-diff"]["pending"])
        self.assertNotIn("speckit.evidence.collect", fake.calls)
        self.assertNotIn("speckit.delivery.handoff", fake.calls)
        self.assertFalse((runtime.directory / "evidence.md").exists())
        self.assertFalse((root / ".specify" / "features").exists())

    def test_post_review_adr_mutation_refreshes_quality_standards_then_reviews_once(self):
        cases = ("feature", "bugfix")
        for lane in cases:
            with self.subTest(lane=lane):
                run = f"{lane}-adr-refresh"
                fake = FullWorkflowConsumers(
                    Path("."),
                    lane=lane,
                    mutate_after_review=True,
                    bug_slug=f"{lane}-bug",
                )
                if lane == "feature":
                    _, _, state = self.run_feature(fake, run=run)
                else:
                    _, _, state = self.run_bugfix(
                        fake, run=run, bug_slug=f"{lane}-bug"
                    )
                self.assert_workflow_status(state, "completed")
                self.assertEqual(fake.review_calls, 2)
                self.assertEqual(fake.repair_calls, 0)
                self.assertEqual(fake.stage_counts.get("quality"), 2)
                self.assertEqual(fake.stage_counts.get("standards"), 2)
                first_review = fake.calls.index("speckit.review.run")
                decision_check = fake.calls.index("speckit.decision.check")
                review_calls = [
                    index
                    for index, command in enumerate(fake.calls)
                    if command == "speckit.review.run"
                ]
                second_review = review_calls[-1]
                self.assertLess(first_review, decision_check)
                self.assertLess(decision_check, second_review)
                self.assertLess(
                    fake.calls.index("speckit.quality.check", decision_check),
                    second_review,
                )
                self.assertLess(
                    fake.calls.index("speckit.review.standards", decision_check),
                    second_review,
                )
                self.assertIn("speckit.delivery.handoff", fake.calls)


if __name__ == "__main__":
    unittest.main()
