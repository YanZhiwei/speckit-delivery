#!/usr/bin/env python3
"""Validate release catalogs, manifests, workflows, and the bundle as one contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a mapping")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected an object")
    return data


def _release_tag(version: str) -> str:
    return f"v{version}"


def _check_release_url(
    errors: list[str], label: str, value: object, version: str
) -> None:
    if not isinstance(value, str) or f"/{_release_tag(version)}/" not in value:
        errors.append(
            f"{label}: URL must be pinned to /{_release_tag(version)}/ (got {value!r})"
        )


def _mapping(value: object, label: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{label}: expected a mapping")
        return {}
    return value


def _list(value: object, label: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{label}: expected a list")
        return []
    return value


def _check_exploration_workflow(
    workflow_id: str, workflow: dict[str, Any], errors: list[str]
) -> None:
    """Check portable step order/gates, not the agent's semantic conclusions."""
    required = {
        "feature-delivery": [
            ("delivery-doctor", "speckit.delivery.doctor"),
            ("decision-discover", "speckit.decision.context"),
            ("explore", "speckit.delivery.explore"),
            ("scope-gate", "gate"),
            ("specify", "speckit.specify"),
            ("clarify", "speckit.clarify"),
            ("clarify-gate", "gate"),
            ("decision-resolve", "speckit.decision.context"),
            ("plan", "speckit.plan"),
            ("decision-propose", "speckit.decision.propose"),
            ("plan-gate", "gate"),
            ("tasks", "speckit.tasks"),
            ("slice", "speckit.delivery.slice"),
            ("slice-gate", "gate"),
        ],
        "bugfix-delivery": [
            ("delivery-doctor", "speckit.delivery.doctor"),
            ("decision-discover", "speckit.decision.context"),
            ("explore", "speckit.delivery.explore"),
            ("assess", "speckit.bug.assess"),
            ("assessment-gate", "gate"),
            ("decision-context", "speckit.decision.context"),
            ("quality-brief-before-fix", "speckit.quality.brief"),
            ("fix", "speckit.bug.fix"),
        ],
    }.get(workflow_id)
    if required is None:
        return
    label = f"workflows/{workflow_id}/workflow.yml"
    steps = _list(workflow.get("steps"), f"{label}:steps", errors)
    previous = -1
    for step_id, expected in required:
        matches = [
            (index, step)
            for index, step in enumerate(steps)
            if isinstance(step, dict) and step.get("id") == step_id
        ]
        if len(matches) != 1:
            errors.append(f"{label}: expected exactly one {step_id} step")
            continue
        index, step = matches[0]
        if index <= previous:
            errors.append(f"{label}: {step_id} violates exploration/approval order")
        previous = index
        if expected == "gate":
            if (
                step.get("type") != "gate"
                or step.get("options") != ["approve", "reject"]
                or step.get("on_reject") != "abort"
            ):
                errors.append(f"{label}: {step_id} must abort on rejected approval")
        elif step.get("command") != expected:
            errors.append(f"{label}: {step_id} must invoke {expected}")
        if step.get("continue_on_error"):
            errors.append(f"{label}: {step_id} cannot continue on error")


def _check_review_workflow(
    workflow_id: str, workflow: dict[str, Any], errors: list[str]
) -> None:
    """Verify bounded repair dispatch and closure order, not semantic verdicts."""
    if workflow_id not in {"feature-delivery", "bugfix-delivery", "lightweight-delivery"}:
        return
    label = f"workflows/{workflow_id}/workflow.yml"
    run_input = workflow.get("inputs", {}).get("delivery_run", {})
    if run_input.get("type") != "string" or run_input.get("required") is not True:
        errors.append(f"{label}: delivery_run must be an explicit required string input")
    steps = _list(workflow.get("steps"), f"{label}:steps", errors)
    by_id = {}
    for index, step in enumerate(steps):
        if isinstance(step, dict):
            by_id.setdefault(step.get("id"), []).append((index, step))
    previous = -1
    required = ["review-loop", "review-final", "review-gate"]
    if workflow_id != "lightweight-delivery":
        required.append("review-close")
    required.extend(["evidence", "handoff"])
    for step_id in required:
        matches = by_id.get(step_id, [])
        if len(matches) != 1:
            errors.append(f"{label}: expected exactly one {step_id} review-closure step")
            continue
        index, step = matches[0]
        if index <= previous:
            errors.append(f"{label}: {step_id} violates review-closure order")
        previous = index
        if step.get("continue_on_error"):
            errors.append(f"{label}: {step_id} cannot bypass review closure on error")
        if step_id == "review-loop":
            cap = step.get("max_iterations")
            if (
                step.get("type") != "do-while"
                or step.get("condition") != "true"
                or type(cap) is not int
                or not 1 <= cap <= 3
            ):
                errors.append(f"{label}: review-loop must have 1-3 safe bounded slots")
            children = step.get("steps", [])
            if not isinstance(children, list) or [
                child.get("command") if isinstance(child, dict) else None
                for child in children
            ] != ["speckit.review.run", "speckit.delivery.review-fix"]:
                errors.append(f"{label}: review-loop must review then dispatch one repair pass")
            elif any(child.get("continue_on_error") for child in children):
                errors.append(f"{label}: review-loop cannot continue on command error")
            else:
                args = children[1].get("input", {}).get("args", "")
                if f"repair_slots={cap}" not in str(args):
                    errors.append(f"{label}: repair_slots must match the YAML slot ceiling")
        elif step_id == "review-gate":
            if (
                step.get("type") != "gate"
                or step.get("options") != ["approve", "reject"]
                or step.get("on_reject") != "abort"
            ):
                errors.append(f"{label}: review-gate must abort on rejection")
        elif step_id in {"review-final", "review-close"}:
            if step.get("command") != "speckit.review.run":
                errors.append(f"{label}: {step_id} must invoke speckit.review.run")

    def check_dispatch(step: dict[str, Any]) -> None:
        command = step.get("command", "")
        if command in {
            "speckit.delivery.doctor", "speckit.delivery.explore",
            "speckit.delivery.slice", "speckit.ralph.run", "speckit.review.run",
            "speckit.delivery.review-fix", "speckit.delivery.handoff",
        }:
            if "delivery_run={{ inputs.delivery_run }}" not in str(step.get("input", {}).get("args", "")):
                errors.append(f"{label}: {step.get('id')} must forward the canonical delivery_run")
        for key in ("steps", "then", "else"):
            for child in step.get(key, []):
                if isinstance(child, dict):
                    check_dispatch(child)

    for step in steps:
        if isinstance(step, dict):
            check_dispatch(step)
    packet = ".specify/delivery/{{ inputs.delivery_run }}/exploration.md"
    if workflow_id in {"feature-delivery", "bugfix-delivery"}:
        for step_id in ("explore", "specify", "clarify", "plan", "tasks") if workflow_id == "feature-delivery" else ("explore", "assess", "decision-context", "fix", "regression-test"):
            for _, step in by_id.get(step_id, []):
                if packet not in str(step.get("input", {}).get("args", "")):
                    errors.append(f"{label}: {step_id} must pass the exact exploration packet path")
        gate_id, consumer, choice = (
            ("scope-gate", "specify", "scope_approval") if workflow_id == "feature-delivery"
            else ("assessment-gate", "decision-context", "assessment_approval")
        )
        for _, gate in by_id.get(gate_id, []):
            if gate.get("show_file") != packet:
                errors.append(f"{label}: {gate_id} must display the persisted packet")
        for _, step in by_id.get(consumer, []):
            if f"{choice}={{{{ steps.{gate_id}.output.choice }}}}" not in str(step.get("input", {}).get("args", "")):
                errors.append(f"{label}: {consumer} must forward the actual {gate_id} choice")
    if workflow_id == "bugfix-delivery":
        slug_input = workflow.get("inputs", {}).get("bug_slug", {})
        if slug_input.get("type") != "string" or slug_input.get("required") is not True:
            errors.append(f"{label}: bug_slug must be an explicit required string input")
        for step_id in ("assess", "fix", "regression-test"):
            for _, step in by_id.get(step_id, []):
                if "slug={{ inputs.bug_slug }}" not in str(step.get("input", {}).get("args", "")):
                    errors.append(f"{label}: {step_id} must pass the explicit official Bug slug")
        for _, step in by_id.get("decision-context", []):
            if "assessment=.specify/bugs/{{ inputs.bug_slug }}/assessment.md" not in str(step.get("input", {}).get("args", "")):
                errors.append(f"{label}: coordinator must verify the exact assessment reference")


def _check_slice_workflow(
    workflow_id: str, workflow: dict[str, Any], errors: list[str]
) -> None:
    """Verify the feature slice gate and its downstream consumers are present."""
    if workflow_id != "feature-delivery":
        return
    label = f"workflows/{workflow_id}/workflow.yml"
    steps = _list(workflow.get("steps"), f"{label}:steps", errors)
    by_id: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for index, step in enumerate(steps):
        if isinstance(step, dict):
            by_id.setdefault(str(step.get("id")), []).append((index, step))

    ordered = ("tasks", "slice", "slice-gate", "analyze", "ralph")
    positions: dict[str, int] = {}
    for step_id in ordered:
        matches = by_id.get(step_id, [])
        if len(matches) != 1:
            errors.append(f"{label}: expected exactly one {step_id} slice step")
            continue
        index, step = matches[0]
        positions[step_id] = index
        if step_id in {"slice", "slice-gate", "ralph"} and step.get("continue_on_error"):
            errors.append(f"{label}: {step_id} cannot continue on error")
        if step_id == "slice" and step.get("command") != "speckit.delivery.slice":
            errors.append(f"{label}: slice must invoke speckit.delivery.slice")
        if step_id == "slice-gate":
            expected_file = ".specify/delivery/{{ inputs.delivery_run }}/slices.md"
            if step.get("show_file") != expected_file:
                errors.append(f"{label}: slice-gate must display {expected_file}")
            if (
                step.get("type") != "gate"
                or step.get("options") != ["approve", "reject"]
                or step.get("on_reject") != "abort"
            ):
                errors.append(f"{label}: slice-gate must abort on rejection")

    if len(positions) == len(ordered):
        order = [positions[step_id] for step_id in ordered]
        if order != sorted(order):
            errors.append(f"{label}: slice planning violates tasks/gate/analysis order")

    args_by_id = {
        step_id: str(matches[0][1].get("input", {}).get("args", ""))
        for step_id, matches in by_id.items()
        if matches and isinstance(matches[0][1], dict)
    }
    slice_args = args_by_id.get("slice", "")
    for needle in (
        "delivery_run={{ inputs.delivery_run }}",
        "slices=.specify/delivery/{{ inputs.delivery_run }}/slices.md",
        "design_approval={{ steps.plan-gate.output.choice }}",
    ):
        if needle not in slice_args:
            errors.append(f"{label}: slice must pass {needle}")
    for step_id in ("analyze", "ralph", "review-final", "review-close", "handoff"):
        args = args_by_id.get(step_id, "")
        if "slices=.specify/delivery/{{ inputs.delivery_run }}/slices.md" not in args:
            errors.append(f"{label}: {step_id} must consume the exact slices path")
    for step_id in ("analyze", "ralph"):
        if "slice_approval={{ steps.slice-gate.output.choice }}" not in args_by_id.get(step_id, ""):
            errors.append(f"{label}: {step_id} must forward the actual slice-gate choice")
    if "mode=auto" not in args_by_id.get("handoff", ""):
        errors.append(f"{label}: handoff must resolve slice versus rollup mode")


def validate(root: Path, expected_version: str | None = None) -> list[str]:
    """Return contract errors; an empty list means the distribution is coherent."""
    errors: list[str] = []
    catalogs = root / "catalogs"
    extension_catalog = _load_json(catalogs / "extensions.json")
    workflow_catalog = _load_json(catalogs / "workflows.json")
    bundle_catalog = _load_json(catalogs / "bundles.json")
    bundle_manifest = _load_yaml(root / "bundle" / "bundle.yml")

    bundle = _mapping(bundle_manifest.get("bundle"), "bundle/bundle.yml:bundle", errors)
    bundle_version = str(bundle.get("version", ""))
    version = expected_version or bundle_version
    if not version:
        return [*errors, "bundle/bundle.yml: missing bundle.version"]
    if bundle_version != version:
        errors.append(
            f"bundle/bundle.yml: version {bundle_version!r} != expected {version!r}"
        )

    for name, data in (
        ("extensions", extension_catalog),
        ("workflows", workflow_catalog),
        ("bundles", bundle_catalog),
    ):
        _check_release_url(
            errors,
            f"catalogs/{name}.json:catalog_url",
            data.get("catalog_url"),
            version,
        )

    extension_entries = _mapping(
        extension_catalog.get("extensions"),
        "catalogs/extensions.json:extensions",
        errors,
    )
    for extension_id, entry in extension_entries.items():
        entry = _mapping(
            entry, f"catalogs/extensions.json:{extension_id}", errors
        )
        if entry.get("id") != extension_id:
            errors.append(
                f"catalogs/extensions.json:{extension_id}: id {entry.get('id')!r} "
                "does not match catalog key"
            )
        manifest_path = root / "extensions" / extension_id / "extension.yml"
        if not manifest_path.is_file():
            errors.append(
                f"catalogs/extensions.json:{extension_id}: missing {manifest_path}"
            )
            continue
        manifest = _load_yaml(manifest_path)
        extension = _mapping(
            manifest.get("extension"), f"{manifest_path}:extension", errors
        )
        manifest_version = str(extension.get("version", ""))
        if str(entry.get("version", "")) != manifest_version:
            errors.append(
                f"catalogs/extensions.json:{extension_id}: version "
                f"{entry.get('version')!r} != manifest {manifest_version!r}"
            )
        _check_release_url(
            errors,
            f"catalogs/extensions.json:{extension_id}:download_url",
            entry.get("download_url"),
            version,
        )
        extension_requires = _mapping(
            manifest.get("requires"), f"{manifest_path}:requires", errors
        )
        if entry.get("requires") != extension_requires:
            errors.append(
                f"catalogs/extensions.json:{extension_id}: requires "
                f"{entry.get('requires')!r} != manifest {extension_requires!r}"
            )
        provides = _mapping(
            manifest.get("provides"), f"{manifest_path}:provides", errors
        )
        commands = _list(
            provides.get("commands"), f"{manifest_path}:commands", errors
        )
        command_names = []
        for command in commands:
            command = _mapping(command, f"{manifest_path}:commands[]", errors)
            command_names.append(command.get("name"))
            relative = command.get("file")
            if (
                not isinstance(relative, str)
                or not (manifest_path.parent / relative).is_file()
            ):
                errors.append(f"{manifest_path}: missing command file {relative!r}")
        catalog_provides = _mapping(entry.get("provides"), f"{extension_id}:provides", errors)
        if type(catalog_provides.get("commands")) is not int or catalog_provides["commands"] != len(commands):
            errors.append(f"catalogs/extensions.json:{extension_id}: command count differs from manifest")
        if extension_id == "delivery":
            for required in (
                "speckit.delivery.explore",
                "speckit.delivery.review-fix",
                "speckit.delivery.slice",
            ):
                if required not in command_names:
                    errors.append(f"{manifest_path}: missing {required} command")
            template = manifest_path.parent / "templates" / "exploration.md"
            if not template.is_file():
                errors.append(f"{manifest_path}: missing templates/exploration.md")
            if not (manifest_path.parent / "templates" / "slices.md").is_file():
                errors.append(f"{manifest_path}: missing templates/slices.md")
            if not (manifest_path.parent / "templates" / "bugfix-review-repair.md").is_file():
                errors.append(f"{manifest_path}: missing templates/bugfix-review-repair.md")
            handoff = manifest_path.parent / "commands" / "speckit.delivery.handoff.md"
            if handoff.is_file():
                handoff_text = handoff.read_text(encoding="utf-8")
                for needle in ("PR_BODY_PATH", "gh pr create", "--body-file"):
                    if needle not in handoff_text:
                        errors.append(
                            f"{handoff}: handoff must emit {needle!r} for a usable PR body"
                        )
            doctor = manifest_path.parent / "commands" / "speckit.delivery.doctor.md"
            if doctor.is_file():
                doctor_text = doctor.read_text(encoding="utf-8")
                if (
                    ".specify/extensions/review/templates/reviewer.md"
                    not in doctor_text
                ):
                    errors.append(
                        f"{doctor}: Doctor must reference Review's installed "
                        "templates/reviewer.md path"
                    )
                if re.search(r"`(?:\./)?templates/reviewer\.md`", doctor_text):
                    errors.append(
                        f"{doctor}: Doctor must not use an extension-relative "
                        "Reviewer path that the host rewrites to Delivery"
                    )
        if extension_id == "review":
            template = manifest_path.parent / "templates" / "reviewer.md"
            if not template.is_file():
                errors.append(f"{manifest_path}: missing templates/reviewer.md")

    workflow_entries = _mapping(
        workflow_catalog.get("workflows"),
        "catalogs/workflows.json:workflows",
        errors,
    )
    for workflow_id, entry in workflow_entries.items():
        entry = _mapping(entry, f"catalogs/workflows.json:{workflow_id}", errors)
        if entry.get("id") != workflow_id:
            errors.append(
                f"catalogs/workflows.json:{workflow_id}: id {entry.get('id')!r} "
                "does not match catalog key"
            )
        workflow_path = root / "workflows" / workflow_id / "workflow.yml"
        if not workflow_path.is_file():
            errors.append(
                f"catalogs/workflows.json:{workflow_id}: missing {workflow_path}"
            )
            continue
        workflow = _load_yaml(workflow_path)
        _check_exploration_workflow(workflow_id, workflow, errors)
        _check_review_workflow(workflow_id, workflow, errors)
        _check_slice_workflow(workflow_id, workflow, errors)
        definition = _mapping(
            workflow.get("workflow"), f"{workflow_path}:workflow", errors
        )
        manifest_version = str(definition.get("version", ""))
        if str(entry.get("version", "")) != manifest_version:
            errors.append(
                f"catalogs/workflows.json:{workflow_id}: version "
                f"{entry.get('version')!r} != workflow {manifest_version!r}"
            )
        _check_release_url(
            errors,
            f"catalogs/workflows.json:{workflow_id}:url",
            entry.get("url"),
            version,
        )
        catalog_requires = entry.get("requires")
        definition_requires = workflow.get("requires")
        if catalog_requires != definition_requires:
            errors.append(
                f"catalogs/workflows.json:{workflow_id}: requires "
                f"{catalog_requires!r} != workflow {definition_requires!r}"
            )

    bundle_entries = _mapping(
        bundle_catalog.get("bundles"), "catalogs/bundles.json:bundles", errors
    )
    bundle_entry = _mapping(
        bundle_entries.get(str(bundle.get("id", ""))),
        "catalogs/bundles.json:bundle",
        errors,
    )
    if str(bundle_entry.get("version", "")) != version:
        errors.append(
            f"catalogs/bundles.json: version {bundle_entry.get('version')!r} "
            f"!= {version!r}"
        )
    _check_release_url(
        errors,
        "catalogs/bundles.json:download_url",
        bundle_entry.get("download_url"),
        version,
    )
    manifest_requires = _mapping(
        bundle_manifest.get("requires"), "bundle/bundle.yml:requires", errors
    )
    catalog_requires = _mapping(
        bundle_entry.get("requires"),
        "catalogs/bundles.json:requires",
        errors,
    )
    if catalog_requires.get("speckit_version") != manifest_requires.get(
        "speckit_version"
    ):
        errors.append(
            "catalogs/bundles.json: requires.speckit_version does not match "
            "bundle/bundle.yml"
        )
    provides = _mapping(
        bundle_manifest.get("provides"), "bundle/bundle.yml:provides", errors
    )
    expected_provides = {
        "extensions": len(_list(provides.get("extensions"), "bundle.extensions", errors)),
        "presets": len(_list(provides.get("presets", []), "bundle.presets", errors)),
        "steps": len(_list(provides.get("steps", []), "bundle.steps", errors)),
        "workflows": len(_list(provides.get("workflows"), "bundle.workflows", errors)),
    }
    if bundle_entry.get("provides") != expected_provides:
        errors.append(
            f"catalogs/bundles.json: provides {bundle_entry.get('provides')!r} "
            f"!= bundle {expected_provides!r}"
        )

    for reference in _list(
        provides.get("extensions"), "bundle.extensions", errors
    ):
        reference = _mapping(reference, "bundle.extensions[]", errors)
        extension_id = str(reference.get("id", ""))
        if extension_id == "bug":
            # Bug ships with Spec Kit; its CLI version is not duplicated here.
            continue
        entry = extension_entries.get(extension_id)
        if not isinstance(entry, dict):
            errors.append(
                f"bundle/bundle.yml: extension {extension_id!r} is absent from catalog"
            )
        elif str(entry.get("version", "")) != str(reference.get("version", "")):
            errors.append(
                f"bundle/bundle.yml: extension {extension_id!r} version "
                f"{reference.get('version')!r} != catalog {entry.get('version')!r}"
            )
    for reference in _list(
        provides.get("workflows"), "bundle.workflows", errors
    ):
        reference = _mapping(reference, "bundle.workflows[]", errors)
        workflow_id = str(reference.get("id", ""))
        entry = workflow_entries.get(workflow_id)
        if not isinstance(entry, dict):
            errors.append(
                f"bundle/bundle.yml: workflow {workflow_id!r} is absent from catalog"
            )
        elif str(entry.get("version", "")) != str(reference.get("version", "")):
            errors.append(
                f"bundle/bundle.yml: workflow {workflow_id!r} version "
                f"{reference.get('version')!r} != catalog {entry.get('version')!r}"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--version", help="expected release version")
    parser.add_argument(
        "--print-version", action="store_true", help="print the bundle version"
    )
    args = parser.parse_args()
    if args.print_version:
        bundle = _load_yaml(
            args.root.resolve() / "bundle" / "bundle.yml"
        ).get("bundle", {})
        print(bundle.get("version", "") if isinstance(bundle, dict) else "")
        return 0
    try:
        errors = validate(args.root.resolve(), args.version)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"Distribution validation failed: {exc}")
        return 1
    if errors:
        print("Distribution validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Distribution catalogs, manifests, workflows, and bundle are coherent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
