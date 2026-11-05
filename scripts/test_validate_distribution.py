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
        for name in ("README.md", "README.en.md"):
            shutil.copy2(ROOT / name, root / name)
        return root

    def test_repository_contract_is_valid(self) -> None:
        self.assertEqual(validator.validate(ROOT), [])

    def test_feature_task_closure_guards_cannot_be_omitted_or_waived(self) -> None:
        for action in ("remove-after-ralph", "waive-before-evidence", "remove-convergence-guard"):
            with self.subTest(action=action):
                root = self.fixture()
                path = root / "workflows/feature-delivery/workflow.yml"
                workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                if action == "remove-after-ralph":
                    workflow["steps"] = [step for step in workflow["steps"] if step["id"] != "task-closure-after-ralph"]
                elif action == "waive-before-evidence":
                    next(step for step in workflow["steps"] if step["id"] == "task-closure-before-evidence")["continue_on_error"] = True
                else:
                    loop = next(step for step in workflow["steps"] if step["id"] == "convergence-if-needed")["then"][0]
                    loop["steps"] = [step for step in loop["steps"] if step["id"] != "convergence-task-closure"]
                path.write_text(yaml.safe_dump(workflow, sort_keys=False), encoding="utf-8")
                errors = validator.validate(root)
                self.assertTrue(any("task-closure audit" in error for error in errors), errors)

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

    def test_each_workflow_requires_metadata_must_match_yaml(self) -> None:
        for workflow_id in (
            "feature-delivery",
            "bugfix-delivery",
            "lightweight-delivery",
        ):
            with self.subTest(workflow_id=workflow_id):
                root = self.fixture()
                workflow_path = root / "workflows" / workflow_id / "workflow.yml"
                workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
                workflow["requires"]["speckit_version"] = ">=0.16.4"
                workflow_path.write_text(
                    yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )
                errors = validator.validate(root)
                self.assertTrue(
                    any(f"{workflow_id}: requires" in error for error in errors),
                    errors,
                )

    def test_workflow_requirement_floor_cannot_be_lowered_in_both_metadata_copies(self) -> None:
        for workflow_id in (
            "feature-delivery",
            "bugfix-delivery",
            "lightweight-delivery",
        ):
            with self.subTest(workflow_id=workflow_id):
                root = self.fixture()
                workflow_path = root / "workflows" / workflow_id / "workflow.yml"
                workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
                workflow["requires"]["speckit_version"] = ">=1.2.2"
                workflow_path.write_text(
                    yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )
                catalog_path = root / "catalogs" / "workflows.json"
                catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
                catalog["workflows"][workflow_id]["requires"]["speckit_version"] = ">=1.2.2"
                catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
                errors = validator.validate(root)
                self.assertTrue(
                    any(
                        workflow_id in error
                        and "1.2.3" in error
                        and "speckit_version" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_release_urls_must_match_expected_version(self) -> None:
        root = self.fixture()
        errors = validator.validate(root, expected_version=self.target)
        self.assertTrue(any("catalog_url" in error for error in errors), errors)

    def test_sd_alias_must_belong_to_the_delivery_router(self) -> None:
        for other_command in (None, "speckit.delivery.doctor"):
            with self.subTest(other_command=other_command):
                root = self.fixture()
                path = root / "extensions/delivery/extension.yml"
                manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
                for command in manifest["provides"]["commands"]:
                    if command["name"] == "speckit.delivery.route":
                        command.pop("aliases", None)
                    elif command["name"] == other_command:
                        command["aliases"] = ["sd"]
                path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
                errors = validator.validate(root)
                self.assertTrue(
                    any("speckit.delivery.route must declare the sd alias" in error for error in errors),
                    errors,
                )

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

    def test_runtime_resources_must_ship(self) -> None:
        for relative in (
            "extensions/delivery/scripts/delivery_runtime.py",
            "extensions/delivery/templates/runtime.md",
            "extensions/delivery/templates/core-adapter.md",
        ):
            with self.subTest(relative=relative):
                root = self.fixture()
                (root / relative).unlink()
                errors = validator.validate(root)
                self.assertTrue(any("runtime" in error or "core-adapter" in error for error in errors), errors)

    def test_runtime_templates_must_keep_stage_and_handoff_contracts(self) -> None:
        for relative, needle in (
            ("extensions/delivery/templates/runtime.md", "runtime_stage"),
            ("extensions/delivery/templates/core-adapter.md", "SD_CORE_HANDOFF: PASS"),
        ):
            with self.subTest(relative=relative):
                root = self.fixture()
                path = root / relative
                path.write_text(
                    path.read_text(encoding="utf-8").replace(needle, "removed-contract"),
                    encoding="utf-8",
                )
                errors = validator.validate(root)
                self.assertTrue(any(relative.split("/")[-1] in error for error in errors), errors)

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

    def test_method_command_and_templates_must_ship(self) -> None:
        for relative in (
            "extensions/delivery/commands/speckit.delivery.method.md",
            "extensions/delivery/templates/method-adapter.md",
            "extensions/delivery/templates/method-design.md",
            "extensions/delivery/templates/method-diagnose.md",
            "extensions/delivery/templates/method-review.md",
        ):
            with self.subTest(relative=relative):
                root = self.fixture()
                (root / relative).unlink()
                errors = validator.validate(root)
                self.assertTrue(
                    any("method" in error for error in errors), errors
                )

    def test_method_config_defaults_to_builtin(self) -> None:
        root = self.fixture()
        path = root / "extensions/delivery/config-template.yml"
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(
            config["method_adapters"],
            {
                "design": {"provider": "builtin"},
                "diagnose": {"provider": "builtin"},
                "review": {"provider": "builtin"},
            },
        )
        path.write_text(
            path.read_text(encoding="utf-8").replace("method_adapters:", "methods:"),
            encoding="utf-8",
        )
        errors = validator.validate(root)
        self.assertTrue(any("method_adapters" in error for error in errors), errors)

    def test_review_fix_must_wire_repair_docs(self) -> None:
        root = self.fixture()
        path = root / "extensions/delivery/commands/speckit.delivery.review-fix.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("templates/repair-docs.md", "templates/other.md"),
            encoding="utf-8",
        )
        errors = validator.validate(root)
        self.assertTrue(any("documentation refresh" in error for error in errors), errors)

    def test_package_readme_repair_contract_must_ship(self) -> None:
        root = self.fixture()
        path = root / "extensions/docs-sync/commands/speckit.docs-sync.package-readme.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("INPUT_IDENTITY", "IDENTITY"),
            encoding="utf-8",
        )
        errors = validator.validate(root)
        self.assertTrue(any("INPUT_IDENTITY" in error for error in errors), errors)

    def test_repair_docs_template_must_ship(self) -> None:
        root = self.fixture()
        (root / "extensions/delivery/templates/repair-docs.md").unlink()
        errors = validator.validate(root)
        self.assertTrue(any("repair-docs" in error for error in errors), errors)

    def test_package_readme_must_carry_lane(self) -> None:
        root = self.fixture()
        path = root / "workflows/bugfix-delivery/workflow.yml"
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        node = next(step for step in workflow["steps"] if step.get("id") == "package-readme")
        node["input"]["args"] = node["input"]["args"].replace("lane=bugfix ", "")
        path.write_text(
            yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        errors = validator.validate(root)
        self.assertTrue(any("package-readme must pass lane=bugfix" in error for error in errors), errors)

    def test_slice_approval_writer_must_follow_the_gate(self) -> None:
        root = self.fixture()
        path = root / "workflows/feature-delivery/workflow.yml"
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        workflow["steps"] = [
            step for step in workflow["steps"] if step.get("id") != "slice-approval"
        ]
        path.write_text(
            yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        errors = validator.validate(root)
        self.assertTrue(any("slice-approval" in error for error in errors), errors)

    def test_slice_approval_contract_must_ship(self) -> None:
        root = self.fixture()
        path = root / "extensions/delivery/commands/speckit.delivery.slice.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("SLICE_APPROVAL_RECORD", "APPROVAL"),
            encoding="utf-8",
        )
        errors = validator.validate(root)
        self.assertTrue(any("approval contract" in error for error in errors), errors)

    def test_ralph_task_closure_must_carry_docs_gate(self) -> None:
        root = self.fixture()
        path = root / "extensions/ralph/commands/speckit.ralph.run.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("DOCS_REFRESH", "DOCS_STATUS"),
            encoding="utf-8",
        )
        errors = validator.validate(root)
        self.assertTrue(any("task-closure gate" in error for error in errors), errors)

    def test_ralph_must_keep_the_task_scoped_quality_brief(self) -> None:
        root = self.fixture()
        path = root / "extensions/ralph/commands/speckit.ralph.run.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "speckit.quality.brief", "speckit.quality.check"
            ),
            encoding="utf-8",
        )
        errors = validator.validate(root)
        self.assertTrue(
            any("speckit.quality.brief" in error for error in errors), errors
        )

    def test_reviewer_report_must_carry_method_receipt(self) -> None:
        root = self.fixture()
        path = root / "extensions/review/templates/reviewer.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("method_receipt:", "method:"),
            encoding="utf-8",
        )
        errors = validator.validate(root)
        self.assertTrue(any("method_receipt" in error for error in errors), errors)

    def test_close_command_must_ship(self) -> None:
        root = self.fixture()
        (root / "extensions/delivery/commands/speckit.delivery.close.md").unlink()
        errors = validator.validate(root)
        self.assertTrue(
            any("speckit.delivery.close" in error for error in errors), errors
        )

    def test_package_readme_node_runs_before_review_in_every_lane(self) -> None:
        for workflow_id in (
            "feature-delivery",
            "bugfix-delivery",
            "lightweight-delivery",
        ):
            with self.subTest(workflow_id=workflow_id):
                root = self.fixture()
                path = root / "workflows" / workflow_id / "workflow.yml"
                workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                workflow["steps"] = [
                    step
                    for step in workflow["steps"]
                    if step.get("id") != "package-readme"
                ]
                path.write_text(
                    yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )
                errors = validator.validate(root)
                self.assertTrue(
                    any("package-readme" in error for error in errors), errors
                )

    def test_package_readme_must_precede_quality_checks(self) -> None:
        root = self.fixture()
        path = root / "workflows/lightweight-delivery/workflow.yml"
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        steps = workflow["steps"]
        node = next(step for step in steps if step.get("id") == "package-readme")
        steps.remove(node)
        quality_index = next(
            index for index, step in enumerate(steps) if step.get("id") == "quality"
        )
        steps.insert(quality_index + 1, node)
        path.write_text(
            yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        errors = validator.validate(root)
        self.assertTrue(
            any("package-readme must run before quality" in error for error in errors),
            errors,
        )

    def test_package_readme_must_not_run_after_review(self) -> None:
        root = self.fixture()
        path = root / "workflows" / "feature-delivery" / "workflow.yml"
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        steps = workflow["steps"]
        node = next(step for step in steps if step.get("id") == "package-readme")
        steps.remove(node)
        steps.append(node)
        path.write_text(
            yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        errors = validator.validate(root)
        self.assertTrue(
            any("before review-loop" in error for error in errors), errors
        )

    def test_package_readme_command_and_template_must_ship(self) -> None:
        for relative in (
            "extensions/docs-sync/commands/speckit.docs-sync.package-readme.md",
            "extensions/docs-sync/templates/package-readme.md",
        ):
            with self.subTest(relative=relative):
                root = self.fixture()
                (root / relative).unlink()
                errors = validator.validate(root)
                self.assertTrue(
                    any("package-readme" in error for error in errors), errors
                )

    def test_readme_release_urls_must_match_version(self) -> None:
        root = self.fixture()
        version = yaml.safe_load(
            (root / "bundle" / "bundle.yml").read_text(encoding="utf-8")
        )["bundle"]["version"]
        path = root / "README.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                f"/v{version}/", "/v999.999.999/"
            ),
            encoding="utf-8",
        )
        errors = validator.validate(root)
        self.assertTrue(any("release URL" in error for error in errors), errors)

    def test_bilingual_readme_pair_must_ship(self) -> None:
        for name in ("README.md", "README.en.md"):
            with self.subTest(name=name):
                root = self.fixture()
                (root / name).unlink()
                errors = validator.validate(root)
                self.assertTrue(
                    any("bilingual README" in error for error in errors), errors
                )

    def test_delivery_fallback_template_is_chinese(self) -> None:
        text = (
            ROOT / "extensions/delivery/templates/pull-request.md"
        ).read_text(encoding="utf-8")
        self.assertIn("## 摘要", text)
        self.assertIn("Closes #", text)
        self.assertNotIn("## Summary", text)

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

    def test_native_runtime_stage_requires_adjacent_begin_and_record(self) -> None:
        for workflow_id, stage_step_id in (
            ("feature-delivery", "analyze"),
            ("feature-delivery", "convergence-analyze"),
            ("bugfix-delivery", "simplify"),
            ("lightweight-delivery", "simplify"),
        ):
            for operation in ("begin", "record"):
                with self.subTest(
                    workflow=workflow_id, stage=stage_step_id, operation=operation
                ):
                    root = self.fixture()
                    path = root / "workflows" / workflow_id / "workflow.yml"
                    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                    stage = next(
                        step for step in validator._walk_steps(workflow["steps"])
                        if step.get("id") == stage_step_id
                    )
                    stage_name = re.search(
                        r"runtime_stage=([a-z-]+)",
                        str(stage.get("input", {}).get("args", "")),
                    )
                    self.assertIsNotNone(stage_name)
                    adjacent_id = f"{stage_step_id}-runtime-{operation}"
                    if stage_step_id == "convergence-analyze":
                        adjacent_id = f"convergence-analyze-runtime-{operation}"
                    steps = validator._walk_steps(workflow["steps"])
                    adjacent = next(step for step in steps if step.get("id") == adjacent_id)
                    container = workflow["steps"]
                    if adjacent not in container:
                        container = next(
                            parent["steps"]
                            for parent in steps
                            if isinstance(parent.get("steps"), list)
                            and adjacent in parent["steps"]
                        )
                    container.remove(adjacent)
                    path.write_text(
                        yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
                        encoding="utf-8",
                    )
                    errors = validator.validate(root)
                    self.assertTrue(
                        any(
                            stage_step_id in error and operation in error
                            for error in errors
                        ),
                        errors,
                    )

    def test_runtime_result_path_must_match_its_stage(self) -> None:
        root = self.fixture()
        path = root / "workflows/feature-delivery/workflow.yml"
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        analyze = next(step for step in workflow["steps"] if step.get("id") == "analyze")
        analyze["input"]["args"] = str(analyze["input"]["args"]).replace(
            ".specify/delivery/{{ inputs.delivery_run }}/runtime/result-analyze.json",
            ".specify/delivery/other-run/runtime/result-analyze.json",
        )
        path.write_text(
            yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        errors = validator.validate(root)
        self.assertTrue(
            any("analyze" in error and "result path" in error for error in errors),
            errors,
        )

    def test_review_and_convergence_guards_cannot_dispatch_unconditionally(self) -> None:
        for guard_id, loop_id in (
            ("review-repair-if-needed", "review-repair-loop"),
            ("convergence-if-needed", "convergence-loop"),
        ):
            for target_id in (guard_id, loop_id):
                with self.subTest(target=target_id):
                    root = self.fixture()
                    path = root / "workflows/feature-delivery/workflow.yml"
                    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                    target = next(
                        step for step in validator._walk_steps(workflow["steps"])
                        if step.get("id") == target_id
                    )
                    target["condition"] = "true"
                    path.write_text(
                        yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
                        encoding="utf-8",
                    )
                    errors = validator.validate(root)
                    expected_signal = {
                        "review-repair-if-needed": "runtime need result",
                        "review-repair-loop": "review-repair-loop",
                        "convergence-if-needed": "convergence work",
                        "convergence-loop": "convergence-loop",
                    }[target_id]
                    self.assertTrue(
                        any(expected_signal in error for error in errors), errors
                    )

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

    def test_review_repair_loop_requires_reserve_and_complete(self) -> None:
        for workflow_id in (
            "feature-delivery",
            "bugfix-delivery",
            "lightweight-delivery",
        ):
            for removed_id in ("review-reserve", "review-complete"):
                with self.subTest(workflow=workflow_id, removed=removed_id):
                    root = self.fixture()
                    path = root / "workflows" / workflow_id / "workflow.yml"
                    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                    loop = next(
                        step for step in validator._walk_steps(workflow["steps"])
                        if step.get("id") == "review-repair-loop"
                    )
                    loop["steps"] = [
                        step for step in loop["steps"] if step.get("id") != removed_id
                    ]
                    path.write_text(
                        yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
                        encoding="utf-8",
                    )
                    errors = validator.validate(root)
                    self.assertTrue(
                        any(removed_id in error for error in errors), errors
                    )

    def test_feature_convergence_require_cannot_be_removed(self) -> None:
        root = self.fixture()
        path = root / "workflows/feature-delivery/workflow.yml"
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        workflow["steps"] = [
            step for step in workflow["steps"] if step.get("id") != "convergence-require"
        ]
        path.write_text(
            yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        errors = validator.validate(root)
        self.assertTrue(any("convergence-require" in error for error in errors), errors)

    def test_initial_analyze_must_require_before_combined_slice_gate(self) -> None:
        for mutation in ("remove", "after-gate", "wrong-kind"):
            with self.subTest(mutation=mutation):
                root = self.fixture()
                path = root / "workflows/feature-delivery/workflow.yml"
                workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                steps = workflow["steps"]
                analyze_require = next(
                    step for step in steps if step.get("id") == "analyze-require"
                )
                if mutation == "remove":
                    steps.remove(analyze_require)
                elif mutation == "after-gate":
                    steps.remove(analyze_require)
                    gate_index = next(
                        index
                        for index, step in enumerate(steps)
                        if step.get("id") == "slice-gate"
                    )
                    steps.insert(gate_index + 1, analyze_require)
                else:
                    analyze_require["run"] = str(analyze_require["run"]).replace(
                        "--kind analyze", "--kind review"
                    )
                path.write_text(
                    yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )
                errors = validator.validate(root)
                self.assertTrue(
                    any("analyze-require" in error or "slice planning" in error for error in errors),
                    errors,
                )

    def test_convergence_slice_owners_and_gate_must_precede_ralph(self) -> None:
        for target_id, mutation in (
            ("convergence-slice", "remove"),
            ("convergence-slice-gate", "remove"),
            ("convergence-slice-approval", "remove"),
            ("convergence-slice", "after-ralph"),
            ("convergence-slice", "wrong-owner"),
            ("convergence-slice-gate", "wrong-owner"),
            ("convergence-slice-gate", "after-ralph"),
            ("convergence-slice-approval", "after-ralph"),
            ("convergence-slice-approval", "wrong-owner"),
        ):
            with self.subTest(target=target_id, mutation=mutation):
                root = self.fixture()
                path = root / "workflows/feature-delivery/workflow.yml"
                workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                loop = next(
                    step for step in validator._walk_steps(workflow["steps"])
                    if step.get("id") == "convergence-loop"
                )
                loop_steps = loop["steps"]
                target = next(step for step in loop_steps if step.get("id") == target_id)
                if mutation == "remove":
                    loop_steps.remove(target)
                elif mutation == "after-ralph":
                    loop_steps.remove(target)
                    ralph_index = next(
                        index
                        for index, step in enumerate(loop_steps)
                        if step.get("id") == "convergence-ralph"
                    )
                    loop_steps.insert(ralph_index + 1, target)
                else:
                    if target_id == "convergence-slice-gate":
                        target["type"] = "shell"
                    else:
                        target["command"] = "speckit.ralph.run"
                path.write_text(
                    yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )
                errors = validator.validate(root)
                self.assertTrue(
                    any(
                        "convergence" in error
                        and ("slice" in error.lower() or "ralph" in error.lower())
                        for error in errors
                    ),
                    errors,
                )

    def test_decision_context_must_forward_the_active_lane(self) -> None:
        for workflow_id, step_ids, lane in (
            (
                "feature-delivery",
                ("decision-discover", "decision-resolve"),
                "feature",
            ),
            (
                "bugfix-delivery",
                ("decision-discover", "decision-context"),
                "bugfix",
            ),
        ):
            for step_id in step_ids:
                with self.subTest(workflow=workflow_id, step=step_id):
                    root = self.fixture()
                    path = root / "workflows" / workflow_id / "workflow.yml"
                    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                    step = next(
                        item for item in workflow["steps"] if item.get("id") == step_id
                    )
                    step["input"]["args"] = str(step["input"]["args"]).replace(
                        f"lane={lane} ", ""
                    )
                    path.write_text(
                        yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
                        encoding="utf-8",
                    )
                    errors = validator.validate(root)
                    self.assertTrue(
                        any(step_id in error and "lane" in error for error in errors),
                        errors,
                    )

    def test_runtime_handoff_phase_must_follow_handoff(self) -> None:
        for workflow_id in (
            "feature-delivery",
            "bugfix-delivery",
            "lightweight-delivery",
        ):
            with self.subTest(workflow=workflow_id):
                root = self.fixture()
                path = root / "workflows" / workflow_id / "workflow.yml"
                workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                steps = workflow["steps"]
                phase = next(step for step in steps if step.get("id") == "runtime-phase-handoff")
                steps.remove(phase)
                handoff_index = next(
                    index for index, step in enumerate(steps) if step.get("id") == "handoff"
                )
                steps.insert(handoff_index, phase)
                path.write_text(
                    yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )
                errors = validator.validate(root)
                self.assertTrue(
                    any("runtime-phase-handoff" in error for error in errors), errors
                )

    def test_optional_simplify_rejection_skips_but_mandatory_gates_abort(self) -> None:
        for workflow_id in (
            "feature-delivery",
            "bugfix-delivery",
            "lightweight-delivery",
        ):
            with self.subTest(workflow=workflow_id, gate="simplify-gate"):
                root = self.fixture()
                path = root / "workflows" / workflow_id / "workflow.yml"
                workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                simplify_gate = next(
                    step for step in validator._walk_steps(workflow["steps"])
                    if step.get("id") == "simplify-gate"
                )
                self.assertEqual(simplify_gate.get("on_reject"), "skip")
                simplify_gate["on_reject"] = "abort"
                path.write_text(
                    yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )
                errors = validator.validate(root)
                self.assertTrue(
                    any("simplify-gate" in error for error in errors), errors
                )

        for gate_id in ("scope-gate", "plan-gate", "review-gate"):
            with self.subTest(workflow="feature-delivery", gate=gate_id):
                root = self.fixture()
                path = root / "workflows/feature-delivery/workflow.yml"
                workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
                gate = next(step for step in workflow["steps"] if step.get("id") == gate_id)
                self.assertEqual(gate.get("on_reject"), "abort")
                gate["on_reject"] = "skip"
                path.write_text(
                    yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True),
                    encoding="utf-8",
                )
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
                    repair_guard = steps["review-repair-if-needed"]
                    repair_loop = next(
                        child for child in repair_guard["then"]
                        if child.get("id") == "review-repair-loop"
                    )
                    if mutation == "missing-final":
                        workflow["steps"].remove(steps["review-final"])
                    elif mutation == "bypass-gate":
                        steps["review-gate"]["on_reject"] = "continue"
                    elif mutation == "unbounded":
                        repair_loop["max_iterations"] = 100
                    elif mutation == "repair-first":
                        repair_loop["steps"].reverse()
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
