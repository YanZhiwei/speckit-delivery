#!/usr/bin/env python3
"""Regression fixtures for the distribution release contract."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
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
    def setUp(self) -> None:
        current = yaml.safe_load(
            (ROOT / "bundle" / "bundle.yml").read_text(encoding="utf-8")
        )["bundle"]["version"]
        # Keep fixture versions different from the checkout so the tests also
        # run on an already-stamped release-preparation branch.
        self.target = "9.9.9" if current != "9.9.9" else "9.9.10"

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
        bundle["provides"]["workflows"][0]["version"] = self.target
        bundle_path.write_text(yaml.safe_dump(bundle), encoding="utf-8")
        errors = validator.validate(root)
        self.assertTrue(
            any("workflow 'feature-delivery'" in error for error in errors), errors
        )

    def test_release_urls_must_match_expected_version(self) -> None:
        root = self.fixture()
        errors = validator.validate(root, expected_version=self.target)
        self.assertTrue(any("catalog_url" in error for error in errors), errors)

    def test_explore_command_must_be_declared(self) -> None:
        root = self.fixture()
        path = root / "extensions/delivery/extension.yml"
        manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
        manifest["provides"]["commands"] = [
            command for command in manifest["provides"]["commands"]
            if command["name"] != "speckit.delivery.explore"
        ]
        path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
        errors = validator.validate(root)
        self.assertTrue(any("missing speckit.delivery.explore" in error for error in errors), errors)

    def test_explore_command_and_template_must_ship(self) -> None:
        for relative in (
            "extensions/delivery/commands/speckit.delivery.explore.md",
            "extensions/delivery/templates/exploration.md",
        ):
            with self.subTest(relative=relative):
                root = self.fixture()
                (root / relative).unlink()
                errors = validator.validate(root)
                self.assertTrue(any("missing" in error and "explor" in error for error in errors), errors)

    def test_slice_command_and_template_must_ship(self) -> None:
        for relative in (
            "extensions/delivery/commands/speckit.delivery.slice.md",
            "extensions/delivery/templates/slices.md",
        ):
            with self.subTest(relative=relative):
                root = self.fixture()
                (root / relative).unlink()
                errors = validator.validate(root)
                self.assertTrue(any("slice" in error for error in errors), errors)

    def test_handoff_must_emit_usable_body_path(self) -> None:
        root = self.fixture()
        path = root / "extensions/delivery/commands/speckit.delivery.handoff.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("PR_BODY_PATH", "PR_BODY"),
            encoding="utf-8",
        )
        errors = validator.validate(root)
        self.assertTrue(any("PR_BODY_PATH" in error for error in errors), errors)

    def test_slice_gate_and_downstream_path_cannot_be_removed(self) -> None:
        for mutation in ("remove_gate", "drop_ralph_path", "drop_approval"):
            with self.subTest(mutation=mutation):
                root = self.fixture()
                path = root / "workflows/feature-delivery/workflow.yml"
                workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                if mutation == "remove_gate":
                    workflow["steps"] = [
                        step for step in workflow["steps"]
                        if step.get("id") != "slice-gate"
                    ]
                else:
                    ralph = next(
                        step for step in workflow["steps"] if step.get("id") == "ralph"
                    )
                    needle = (
                        "slices=.specify/delivery/{{ inputs.delivery_run }}/slices.md"
                        if mutation == "drop_ralph_path"
                        else "slice_approval={{ steps.slice-gate.output.choice }}"
                    )
                    ralph["input"]["args"] = str(ralph["input"]["args"]).replace(
                        needle, ""
                    )
                path.write_text(yaml.safe_dump(workflow), encoding="utf-8")
                errors = validator.validate(root)
                self.assertTrue(any("slice" in error for error in errors), errors)

    def test_feature_scope_gate_cannot_follow_specify(self) -> None:
        root = self.fixture()
        path = root / "workflows/feature-delivery/workflow.yml"
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        steps = workflow["steps"]
        scope = next(step for step in steps if step["id"] == "scope-gate")
        steps.remove(scope)
        steps.append(scope)
        path.write_text(yaml.safe_dump(workflow), encoding="utf-8")
        errors = validator.validate(root)
        self.assertTrue(any("exploration/approval order" in error for error in errors), errors)

    def test_required_scope_and_plan_gates_cannot_be_removed_or_bypassed(self) -> None:
        for workflow_id, gate_id in (
            ("feature-delivery", "scope-gate"),
            ("feature-delivery", "plan-gate"),
            ("bugfix-delivery", "assessment-gate"),
        ):
            for mutation in ("remove", "continue"):
                with self.subTest(workflow=workflow_id, gate=gate_id, mutation=mutation):
                    root = self.fixture()
                    path = root / "workflows" / workflow_id / "workflow.yml"
                    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                    gate = next(step for step in workflow["steps"] if step["id"] == gate_id)
                    if mutation == "remove":
                        workflow["steps"].remove(gate)
                    else:
                        gate["on_reject"] = "continue"
                    path.write_text(yaml.safe_dump(workflow), encoding="utf-8")
                    errors = validator.validate(root)
                    self.assertTrue(any(gate_id in error for error in errors), errors)

    def test_bugfix_exploration_must_precede_assessment(self) -> None:
        root = self.fixture()
        path = root / "workflows/bugfix-delivery/workflow.yml"
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        explore = next(step for step in workflow["steps"] if step["id"] == "explore")
        workflow["steps"].remove(explore)
        workflow["steps"].append(explore)
        path.write_text(yaml.safe_dump(workflow), encoding="utf-8")
        errors = validator.validate(root)
        self.assertTrue(any("exploration/approval order" in error for error in errors), errors)

    def test_lightweight_does_not_require_full_exploration(self) -> None:
        workflow = yaml.safe_load(
            (ROOT / "workflows/lightweight-delivery/workflow.yml").read_text(encoding="utf-8")
        )
        self.assertNotIn(
            "speckit.delivery.explore",
            [step.get("command") for step in workflow["steps"]],
        )

    def test_exploration_cannot_be_optional_or_an_unrelated_command(self) -> None:
        for mutation in ("optional", "wrong-command", "duplicate"):
            with self.subTest(mutation=mutation):
                root = self.fixture()
                path = root / "workflows/feature-delivery/workflow.yml"
                workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                explore = next(step for step in workflow["steps"] if step["id"] == "explore")
                if mutation == "optional":
                    explore["continue_on_error"] = True
                elif mutation == "wrong-command":
                    explore["command"] = "speckit.specify"
                else:
                    workflow["steps"].append(explore.copy())
                path.write_text(yaml.safe_dump(workflow), encoding="utf-8")
                errors = validator.validate(root)
                self.assertTrue(any("explore" in error for error in errors), errors)

    def test_downstream_prompts_consume_exploration(self) -> None:
        # Prompt text is the distributed product. This checks explicit handoff,
        # not whether an agent's eventual investigation or design is correct.
        for workflow_id, step_ids in (
            ("feature-delivery", ("specify", "clarify", "plan", "tasks")),
            ("bugfix-delivery", ("assess", "fix")),
        ):
            workflow = yaml.safe_load(
                (ROOT / "workflows" / workflow_id / "workflow.yml").read_text(encoding="utf-8")
            )
            for step_id in step_ids:
                with self.subTest(workflow=workflow_id, step=step_id):
                    step = next(step for step in workflow["steps"] if step["id"] == step_id)
                    self.assertIn("exploration", step["input"]["args"])

    def test_doctor_reviewer_reference_must_name_review_extension(self) -> None:
        root = self.fixture()
        path = root / "extensions/delivery/commands/speckit.delivery.doctor.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace(
                ".specify/extensions/review/templates/reviewer.md",
                "`templates/reviewer.md`",
            ).replace("``", "`"),
            encoding="utf-8",
        )
        errors = validator.validate(root)
        self.assertTrue(
            any("extension-relative Reviewer path" in error for error in errors), errors
        )

    def test_reviewer_template_must_ship(self) -> None:
        root = self.fixture()
        (root / "extensions/review/templates/reviewer.md").unlink()
        errors = validator.validate(root)
        self.assertTrue(any("missing templates/reviewer.md" in error for error in errors), errors)

    def test_review_repair_command_must_be_declared(self) -> None:
        root = self.fixture()
        path = root / "extensions/delivery/extension.yml"
        manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
        manifest["provides"]["commands"] = [
            command for command in manifest["provides"]["commands"]
            if command["name"] != "speckit.delivery.review-fix"
        ]
        path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
        errors = validator.validate(root)
        self.assertTrue(any("missing speckit.delivery.review-fix" in error for error in errors), errors)

    def test_all_lanes_require_bounded_review_and_final_gate(self) -> None:
        for workflow_id in ("feature-delivery", "bugfix-delivery", "lightweight-delivery"):
            for mutation in ("missing-final", "bypass-gate", "unbounded", "repair-first", "handoff-first"):
                with self.subTest(workflow=workflow_id, mutation=mutation):
                    root = self.fixture()
                    path = root / "workflows" / workflow_id / "workflow.yml"
                    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                    steps = {step["id"]: step for step in workflow["steps"]}
                    if mutation == "missing-final":
                        workflow["steps"].remove(steps["review-final"])
                    elif mutation == "bypass-gate":
                        steps["review-gate"]["on_reject"] = "continue"
                    elif mutation == "unbounded":
                        steps["review-loop"]["max_iterations"] = 100
                    elif mutation == "repair-first":
                        steps["review-loop"]["steps"].reverse()
                    else:
                        workflow["steps"].remove(steps["handoff"])
                        workflow["steps"].insert(0, steps["handoff"])
                    path.write_text(yaml.safe_dump(workflow), encoding="utf-8")
                    errors = validator.validate(root)
                    self.assertTrue(any("review" in error for error in errors), errors)

    def test_review_output_has_six_dimensions_and_snapshot_coverage(self) -> None:
        text = (ROOT / "extensions/review/templates/reviewer.md").read_text(encoding="utf-8")
        match = re.search(r"```yaml\n(.*?)\n```", text, re.DOTALL)
        self.assertIsNotNone(match)
        report = yaml.safe_load(match.group(1))
        self.assertEqual(set(report["dimensions"]), {
            "requirements", "code_quality", "architecture", "correctness",
            "security_compatibility", "test_effectiveness",
        })
        self.assertIn("incomplete", report["REVIEW_VERDICT"])
        self.assertIn("content_fingerprint", report["snapshot"])
        self.assertIn("requirements_fingerprint", report["snapshot"])
        self.assertEqual(set(report["coverage"]), {"reviewed", "partial", "unreviewed", "excluded"})
        self.assertIn("prior_findings_accounted_for", report)

    def test_ralph_requires_task_review_before_checkbox_transition(self) -> None:
        text = (ROOT / "extensions/ralph/commands/speckit.ralph.run.md").read_text(encoding="utf-8")
        review = text.index("speckit.review.run scope=task")
        transition = text.index("Update the matching task to `[X]`")
        self.assertLess(review, transition)
        self.assertIn("REVIEW_VERDICT=pass", text)
        self.assertIn("content/requirements", text)

    def test_catalog_command_count_matches_manifest(self) -> None:
        root = self.fixture()
        path = root / "catalogs/extensions.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        catalog["extensions"]["delivery"]["provides"]["commands"] = 5
        path.write_text(json.dumps(catalog), encoding="utf-8")
        self.assertTrue(any("command count" in error for error in validator.validate(root)))

    def test_workflow_packet_path_and_gate_choice_cannot_be_dropped(self) -> None:
        for workflow_id, consumer, gate in (
            ("feature-delivery", "specify", "scope-gate"),
            ("bugfix-delivery", "decision-context", "assessment-gate"),
        ):
            for mutation in ("packet", "choice", "run", "display"):
                with self.subTest(workflow=workflow_id, mutation=mutation):
                    root = self.fixture()
                    path = root / "workflows" / workflow_id / "workflow.yml"
                    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                    steps = {step["id"]: step for step in workflow["steps"]}
                    if mutation == "run":
                        del workflow["inputs"]["delivery_run"]
                    elif mutation == "display":
                        del steps[gate]["show_file"]
                    else:
                        args = steps[consumer]["input"]["args"]
                        needle = ".specify/delivery/{{ inputs.delivery_run }}/exploration.md" if mutation == "packet" else "{{ steps." + gate + ".output.choice }}"
                        steps[consumer]["input"]["args"] = args.replace(needle, "missing")
                    path.write_text(yaml.safe_dump(workflow), encoding="utf-8")
                    self.assertTrue(validator.validate(root))

    def test_bugfix_continuation_adapter_must_ship(self) -> None:
        root = self.fixture()
        (root / "extensions/delivery/templates/bugfix-review-repair.md").unlink()
        self.assertTrue(any("missing templates/bugfix-review-repair.md" in error for error in validator.validate(root)))

    def test_quality_and_standards_produce_original_snapshot_evidence(self) -> None:
        quality = (ROOT / "extensions/quality/commands/speckit.quality.check.md").read_text(encoding="utf-8")
        standards = (ROOT / "extensions/review/commands/speckit.review.standards.md").read_text(encoding="utf-8")
        for field in ("CONTENT_FINGERPRINT:", "CHECK_CONFIG_FINGERPRINT:", "CHECK_RECEIPTS:"):
            self.assertIn(field, quality)
        self.assertIn("HEAD/path-only receipt", quality)
        self.assertIn("CONTENT_FINGERPRINT:", standards)
        self.assertIn("POLICY_FINGERPRINT:", standards)

    def test_bug_identity_is_explicit_in_official_commands_and_coordinator(self) -> None:
        for step_id in ("assess", "fix", "regression-test", "decision-context"):
            with self.subTest(step=step_id):
                root = self.fixture()
                path = root / "workflows/bugfix-delivery/workflow.yml"
                workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                step = next(item for item in workflow["steps"] if item["id"] == step_id)
                step["input"]["args"] = step["input"]["args"].replace("{{ inputs.bug_slug }}", "missing")
                path.write_text(yaml.safe_dump(workflow), encoding="utf-8")
                self.assertTrue(any("slug" in error or "assessment reference" in error for error in validator.validate(root)))

    def test_continuation_includes_current_round_pre_and_post_hooks(self) -> None:
        text = (ROOT / "extensions/delivery/templates/bugfix-review-repair.md").read_text(encoding="utf-8")
        positions = [text.index(f"`{phase}`") for phase in (
            "before_bug_fix", "after_bug_fix", "before_bug_test", "after_bug_test",
        )]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Actually", text)
        self.assertIn("available round-local fix/test report paths", text)
        self.assertIn("unavailable mandatory hook", text)


if __name__ == "__main__":
    unittest.main()
