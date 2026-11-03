#!/usr/bin/env python3
"""Probe actual Spec Kit command/gate dispatch with isolated fake host consumers.

Requires a Python environment containing specify_cli (verified with 1.2.3).
This tests process-boundary argument/disk transport, not live model semantics.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import yaml
from specify_cli.workflows.base import StepContext, StepStatus
from specify_cli.workflows.step.command import CommandStep
from specify_cli.workflows.step.gate import GateStep


ROOT = Path(__file__).resolve().parents[1]


class WorkflowHandoffTest(unittest.TestCase):
    def probe(self, workflow_id: str, *, omit_packet: bool = False, wrong_bug_output: bool = False) -> None:
        workflow = yaml.safe_load((ROOT / "workflows" / workflow_id / "workflow.yml").read_text(encoding="utf-8"))
        steps = {step["id"]: step for step in workflow["steps"]}
        feature = workflow_id == "feature-delivery"
        gate_id = "scope-gate" if feature else "assessment-gate"
        consumer_id = "specify" if feature else "decision-context"
        choice_key = "scope_approval" if feature else "assessment_approval"
        inputs = {"delivery_run": "probe-run-1", "bug_slug": "actual-bug-not-run-id", "integration": "opencode", "spec": "probe feature", "report": "probe defect"}
        history: dict = {}
        seen = []
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            packet = root / ".specify/delivery/probe-run-1/exploration.md"
            sentinel = "Evidence survives a new host process: custom-route consumer traced."
            assessment = root / ".specify/bugs/actual-bug-not-run-id/assessment.md"
            # Multiple unrelated assessments prevent single-candidate guessing.
            for slug in ("unrelated-one", "unrelated-two"):
                unrelated = root / f".specify/bugs/{slug}/assessment.md"
                unrelated.parent.mkdir(parents=True)
                unrelated.write_text("unrelated bug", encoding="utf-8")

            def dispatch(command, integration, model, args, context, *extra, **kwargs):
                # There is no conversation handoff, captured stdout, or global
                # packet object available to the next consumer: only argv/disk.
                seen.append((command, args))
                self.assertEqual(context.project_root, str(root))
                if command == "speckit.delivery.explore":
                    self.assertIn("delivery_run=probe-run-1", args)
                    self.assertIn(str(packet.relative_to(root)).replace("\\", "/"), args)
                    if not omit_packet:
                        packet.parent.mkdir(parents=True)
                        packet.write_text(sentinel + "\nSCOPE_APPROVAL: pending\n", encoding="utf-8")
                else:
                    match = re.search(r"\bexploration=(\S+)", args)
                    self.assertIsNotNone(match, "Consumer lacks exact packet reference")
                    reference = root / match.group(1)
                    self.assertEqual(reference, packet)
                    if not reference.is_file():
                        return {"exit_code": 1, "stdout": "", "stderr": "missing persisted packet"}
                    text = reference.read_text(encoding="utf-8")
                    self.assertIn(sentinel, text)
                    if command == "speckit.bug.assess":
                        self.assertTrue(args.startswith("slug=actual-bug-not-run-id "))
                        original_packet = reference.read_bytes()
                        # Respect the actual official assessment write boundary:
                        # no external Delivery packet write by this consumer.
                        output = root / ".specify/bugs/unexpected-slug/assessment.md" if wrong_bug_output else assessment
                        output.parent.mkdir(parents=True)
                        output.write_text("Assessed actual-bug-not-run-id: approved repair contract", encoding="utf-8")
                        self.assertEqual(reference.read_bytes(), original_packet)
                    elif command in {"speckit.specify", "speckit.decision.context"}:
                        self.assertIn(f"{choice_key}=approve", args)
                        self.assertNotIn("{{", args)
                        if not feature:
                            self.assertIn("bug_slug=actual-bug-not-run-id", args)
                            self.assertIn("assessment=.specify/bugs/actual-bug-not-run-id/assessment.md", args)
                            if not assessment.is_file():
                                return {"exit_code": 1, "stdout": "", "stderr": "expected assessment missing; do not guess another Bug"}
                        with reference.open("a", encoding="utf-8") as stream:
                            if not feature:
                                stream.write("BUG_SLUG: actual-bug-not-run-id\n")
                            stream.write(f"{choice_key}: approve\n")
                return {"exit_code": 0, "stdout": "", "stderr": ""}

            def fresh_context():
                return StepContext(
                    inputs=json.loads(json.dumps(inputs)),
                    steps=json.loads(json.dumps(history)),
                    project_root=str(root), run_id="engine-run-not-delivery-id",
                )

            with patch.object(CommandStep, "_try_dispatch", side_effect=dispatch):
                result = CommandStep().execute(steps["explore"], fresh_context())
                self.assertEqual(result.status, StepStatus.COMPLETED)
                self.assertEqual(result.output["stdout"], "")
                history["explore"] = {"output": result.output}
                if not feature:
                    result = CommandStep().execute(steps["assess"], fresh_context())
                    if omit_packet:
                        self.assertEqual(result.status, StepStatus.FAILED)
                        return
                    self.assertEqual(result.status, StepStatus.COMPLETED)
                old_cwd = Path.cwd()
                try:
                    os.chdir(root)
                    with patch("sys.stdin.isatty", return_value=True), patch.object(GateStep, "_prompt", return_value="approve") as prompt:
                        gate = GateStep().execute(steps[gate_id], fresh_context())
                        self.assertEqual(gate.status, StepStatus.COMPLETED)
                        if not omit_packet:
                            self.assertIn(sentinel, prompt.call_args.args[0])
                finally:
                    os.chdir(old_cwd)
                history[gate_id] = {"output": gate.output}
                result = CommandStep().execute(steps[consumer_id], fresh_context())
                if omit_packet or wrong_bug_output:
                    self.assertEqual(result.status, StepStatus.FAILED)
                    return
                self.assertEqual(result.status, StepStatus.COMPLETED)
                self.assertIn(f"{choice_key}: approve", packet.read_text(encoding="utf-8"))
                self.assertGreaterEqual(len(seen), 2)

    def test_feature_packet_and_real_gate_choice_survive_fresh_dispatch(self):
        self.probe("feature-delivery")

    def test_bug_packet_slug_and_real_gate_choice_survive_fresh_dispatch(self):
        self.probe("bugfix-delivery")

    def test_missing_feature_packet_fails_instead_of_using_context(self):
        self.probe("feature-delivery", omit_packet=True)

    def test_missing_bug_packet_fails_instead_of_using_context(self):
        self.probe("bugfix-delivery", omit_packet=True)

    def test_unexpected_assessment_cannot_be_guessed_from_other_bugs(self):
        self.probe("bugfix-delivery", wrong_bug_output=True)

    def test_evidence_steps_bind_fresh_dispatch_to_canonical_run_records(self):
        cases = {
            "feature-delivery": {
                "lane": "feature",
                "request": "feature evidence transport",
                "needs_exploration": True,
            },
            "bugfix-delivery": {
                "lane": "bugfix",
                "request": "bug evidence transport",
                "needs_exploration": True,
            },
            "lightweight-delivery": {
                "lane": "lightweight",
                "request": "lightweight evidence transport",
                "needs_exploration": False,
            },
        }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            def token(args: str, name: str) -> str | None:
                match = re.search(rf"(?<!\S){re.escape(name)}=(\S+)", args)
                return match.group(1) if match else None

            def run_evidence(workflow_id: str, run_id: str) -> Path:
                case = cases[workflow_id]
                workflow = yaml.safe_load(
                    (ROOT / "workflows" / workflow_id / "workflow.yml").read_text(
                        encoding="utf-8"
                    )
                )
                evidence_step = next(
                    step for step in workflow["steps"] if step["id"] == "evidence"
                )
                inputs = {
                    "delivery_run": run_id,
                    "bug_slug": f"bug-{run_id}",
                    "integration": "opencode",
                    "spec": case["request"],
                    "report": case["request"],
                    "change": case["request"],
                }
                expected_relative = (
                    Path(".specify") / "delivery" / run_id / "evidence.md"
                ).as_posix()
                expected_path = root / expected_relative

                # Install a new consumer for every dispatch. It can recover only
                # from the canonical disk record, never from this test's process
                # state or a previous CommandStep result.
                def fresh_consumer(
                    command, integration, model, args, context, *extra, **kwargs
                ):
                    self.assertEqual(command, "speckit.evidence.collect")
                    self.assertEqual(context.project_root, str(root))
                    self.assertEqual(token(args, "lane"), case["lane"])
                    self.assertEqual(token(args, "delivery_run"), run_id)
                    self.assertEqual(token(args, "evidence"), expected_relative)
                    if case["needs_exploration"]:
                        self.assertEqual(
                            token(args, "exploration"),
                            f".specify/delivery/{run_id}/exploration.md",
                        )
                    else:
                        self.assertIsNone(token(args, "exploration"))
                        self.assertNotIn("spec=", args)
                        self.assertNotIn("assessment=", args)
                    if case["lane"] == "bugfix":
                        self.assertNotIn("spec=", args)
                        self.assertEqual(token(args, "bug_slug"), f"bug-{run_id}")
                        self.assertEqual(
                            token(args, "assessment"),
                            f".specify/bugs/bug-{run_id}/assessment.md",
                        )

                    path = root / (token(args, "evidence") or "")
                    if path != expected_path:
                        return {
                            "exit_code": 1,
                            "stdout": "",
                            "stderr": "non-canonical evidence path",
                        }
                    if path.exists():
                        text = path.read_text(encoding="utf-8")
                        self.assertIn(f"- **delivery_run**: {run_id}", text)
                        self.assertIn(f"- **lane**: {case['lane']}", text)
                        self.assertIn(f"- **evidence_path**: {expected_relative}", text)
                        if case["lane"] == "bugfix":
                            self.assertIn(f"- **bug_slug**: bug-{run_id}", text)
                            self.assertIn(
                                "- **assessment_path**: "
                                f".specify/bugs/bug-{run_id}/assessment.md",
                                text,
                            )
                        text += "\nUPDATE: same-run evidence refresh\n"
                    else:
                        path.parent.mkdir(parents=True)
                        text = (
                            f"- **delivery_run**: {run_id}\n"
                            f"- **lane**: {case['lane']}\n"
                            f"- **evidence_path**: {expected_relative}\n"
                        )
                        if case["lane"] == "bugfix":
                            text += (
                                f"- **bug_slug**: bug-{run_id}\n"
                                "- **assessment_path**: "
                                f".specify/bugs/bug-{run_id}/assessment.md\n"
                            )
                    path.write_text(text, encoding="utf-8")
                    return {"exit_code": 0, "stdout": "", "stderr": ""}

                context = StepContext(
                    inputs=json.loads(json.dumps(inputs)),
                    steps={},
                    project_root=str(root),
                    # Deliberately differ from delivery_run: transport must use
                    # the substituted workflow input, not the engine run id.
                    run_id=f"host-{run_id}",
                )
                with patch.object(CommandStep, "_try_dispatch", side_effect=fresh_consumer):
                    result = CommandStep().execute(evidence_step, context)
                self.assertEqual(result.status, StepStatus.COMPLETED)
                self.assertTrue(expected_path.is_file())
                return expected_path

            for workflow_id, case in cases.items():
                with self.subTest(workflow=workflow_id):
                    first = run_evidence(workflow_id, f"{case['lane']}-run-a")
                    resumed = run_evidence(workflow_id, f"{case['lane']}-run-a")
                    second = run_evidence(workflow_id, f"{case['lane']}-run-b")
                    self.assertEqual(first, resumed)
                    self.assertNotEqual(first, second)
                    self.assertIn(
                        "UPDATE: same-run evidence refresh",
                        first.read_text(encoding="utf-8"),
                    )
                    self.assertIn(
                        f"- **delivery_run**: {case['lane']}-run-b",
                        second.read_text(encoding="utf-8"),
                    )


    def test_slice_approval_writer_receives_gate_choice_in_fresh_process(self):
        workflow = yaml.safe_load(
            (ROOT / "workflows/feature-delivery/workflow.yml").read_text(encoding="utf-8")
        )
        step = next(
            item for item in workflow["steps"] if item.get("id") == "slice-approval"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            relative = ".specify/delivery/slice-run-1/slices.md"
            slices = root / relative
            slices.parent.mkdir(parents=True)
            fingerprint = "sha256:presented-plan"
            slices.write_text(
                "SLICE_PLAN_FINGERPRINT: " + fingerprint + "\nSLICE_APPROVAL: pending\n",
                encoding="utf-8",
            )

            def fresh_consumer(command, integration, model, args, context, *extra, **kwargs):
                self.assertEqual(command, "speckit.delivery.slice")
                self.assertIn("action=record-approval", args)
                self.assertIn("delivery_run=slice-run-1", args)
                self.assertIn(f"slices={relative}", args)
                self.assertIn("slice_approval=approve", args)
                text = slices.read_text(encoding="utf-8")
                self.assertIn(fingerprint, text)
                text += "SLICE_APPROVAL: approved\nApproved by: probe-user\n"
                slices.write_text(text, encoding="utf-8")
                return {"exit_code": 0, "stdout": "", "stderr": ""}

            context = StepContext(
                inputs={"delivery_run": "slice-run-1", "spec": "probe slices"},
                steps={
                    "plan-gate": {"output": {"choice": "approve"}},
                    "slice-gate": {"output": {"choice": "approve"}},
                },
                project_root=str(root),
                run_id="host-run",
            )
            with patch.object(CommandStep, "_try_dispatch", side_effect=fresh_consumer):
                result = CommandStep().execute(step, context)
            self.assertEqual(result.status, StepStatus.COMPLETED)
            self.assertIn(
                "SLICE_APPROVAL: approved", slices.read_text(encoding="utf-8")
            )


if __name__ == "__main__":
    unittest.main()
