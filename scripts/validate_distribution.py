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


def _minimum_version(value: object) -> tuple[int, int, int] | None:
    """Parse a single supported ``>=X.Y.Z`` requirement floor."""
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r">=\s*(\d+)\.(\d+)\.(\d+)", value)
    return tuple(int(part) for part in match.groups()) if match else None


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


def _check_readme_docs(root: Path, version: str, errors: list[str]) -> None:
    """Require the bilingual README pair with release-pinned catalog URLs."""
    expected = f"v{version}"
    for name in ("README.md", "README.en.md"):
        path = root / name
        if not path.is_file():
            errors.append(f"{name}: missing bilingual README")
            continue
        text = path.read_text(encoding="utf-8")
        tags = sorted(set(re.findall(r"speckit-delivery/(v\d+\.\d+\.\d+)/", text)))
        if not tags:
            errors.append(f"{name}: no versioned release URL")
            continue
        for tag in tags:
            if tag != expected:
                errors.append(f"{name}: release URL {tag} != {expected}")


def _walk_steps(steps: list[Any]) -> list[dict[str, Any]]:
    """Return all declared steps, including guarded/loop children."""
    found: list[dict[str, Any]] = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        found.append(step)
        for key in ("steps", "then", "else"):
            children = step.get(key, [])
            if isinstance(children, list):
                found.extend(_walk_steps(children))
    return found


def _check_gate(label: str, step_id: str, step: dict[str, Any], errors: list[str]) -> None:
    if (
        step.get("type") != "gate"
        or step.get("options") != ["approve", "reject"]
        or step.get("on_reject") != "abort"
    ):
        errors.append(f"{label}: {step_id} must abort on rejected approval")


def _check_exploration_workflow(
    workflow_id: str, workflow: dict[str, Any], errors: list[str]
) -> None:
    """Check portable step order/gates, including conditionally nested gates."""
    required = {
        "feature-delivery": [
            ("delivery-doctor", "speckit.delivery.doctor"),
            ("decision-discover", "speckit.decision.context"),
            ("explore", "speckit.delivery.explore"),
            ("scope-gate", "gate"),
            ("specify", "speckit.specify"),
            ("clarify", "speckit.clarify"),
            ("clarification-approval", "if"),
            ("decision-resolve", "speckit.decision.context"),
            ("plan", "speckit.plan"),
            ("decision-propose", "speckit.decision.propose"),
            ("plan-gate", "gate"),
            ("tasks", "speckit.tasks"),
            ("slice", "speckit.delivery.slice"),
            ("analyze", "speckit.analyze"),
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
    top_by_id = {step.get("id"): (index, step) for index, step in enumerate(steps) if isinstance(step, dict)}
    all_by_id: dict[str, list[dict[str, Any]]] = {}
    for step in _walk_steps(steps):
        all_by_id.setdefault(str(step.get("id")), []).append(step)
    previous = -1
    for step_id, expected in required:
        if len(all_by_id.get(step_id, [])) != 1:
            errors.append(f"{label}: expected exactly one {step_id} step")
            continue
        matches = [(top_by_id[step_id][0], top_by_id[step_id][1])] if step_id in top_by_id else []
        if not matches and step_id in all_by_id:
            matches = [(top_by_id.get("clarification-approval", (0, {}))[0], all_by_id[step_id][0])]
        if len(matches) != 1:
            errors.append(f"{label}: expected exactly one {step_id} step")
            continue
        index, step = matches[0]
        if index <= previous:
            errors.append(f"{label}: {step_id} violates exploration/approval order")
        previous = index
        if expected == "gate":
            _check_gate(label, step_id, step, errors)
        elif expected == "if":
            if step.get("type") != "if":
                errors.append(f"{label}: {step_id} must conditionally guard its approval gate")
            nested_gates = [child for child in _walk_steps(step.get("then", [])) if child.get("type") == "gate"]
            if not nested_gates:
                errors.append(f"{label}: {step_id} must contain an aborting approval gate")
            else:
                _check_gate(label, f"{step_id}.gate", nested_gates[0], errors)
        elif step.get("command") != expected:
            errors.append(f"{label}: {step_id} must invoke {expected}")
        if step.get("continue_on_error"):
            errors.append(f"{label}: {step_id} cannot continue on error")


def _check_review_workflow(
    workflow_id: str, workflow: dict[str, Any], errors: list[str]
) -> None:
    """Verify conditional, bounded repair dispatch and closure order."""
    if workflow_id not in {"feature-delivery", "bugfix-delivery", "lightweight-delivery"}:
        return
    label = f"workflows/{workflow_id}/workflow.yml"
    run_input = workflow.get("inputs", {}).get("delivery_run", {})
    if run_input.get("type") != "string" or run_input.get("required") is not True:
        errors.append(f"{label}: delivery_run must be an explicit required string input")
    steps = _list(workflow.get("steps"), f"{label}:steps", errors)
    top_by_id = {step.get("id"): (index, step) for index, step in enumerate(steps) if isinstance(step, dict)}
    all_steps = _walk_steps(steps)
    by_id: dict[str, list[dict[str, Any]]] = {}
    for step in all_steps:
        by_id.setdefault(str(step.get("id")), []).append(step)
    for loop in all_steps:
        if loop.get("type") == "do-while" and loop.get("condition") == "true":
            errors.append(f"{label}: do-while {loop.get('id')} cannot unconditionally dispatch model work")
        if loop.get("type") == "do-while" and (type(loop.get("max_iterations")) is not int or not 1 <= loop.get("max_iterations") <= 3):
            errors.append(f"{label}: do-while {loop.get('id')} must have a literal cap from 1 through 3")

    required = ["review-repair-if-needed", "review-final", "review-gate"]
    if workflow_id != "lightweight-delivery":
        required.append("review-close-if-stale")
    required.extend(["evidence", "handoff"])
    previous = -1
    for step_id in required:
        matches = [top_by_id[step_id]] if step_id in top_by_id else []
        if len(matches) != 1:
            errors.append(f"{label}: expected exactly one {step_id} review-closure step")
            continue
        index, step = matches[0]
        if index <= previous:
            errors.append(f"{label}: {step_id} violates review-closure order")
        previous = index
        if step.get("continue_on_error"):
            errors.append(f"{label}: {step_id} cannot bypass review closure on error")

    repair_guards = top_by_id.get("review-repair-if-needed")
    if repair_guards:
        guard = repair_guards[1]
        if guard.get("type") != "if" or "steps.review-needs-repair.output.stdout == 'true'" not in str(guard.get("condition")):
            errors.append(f"{label}: review-repair-if-needed must guard repair dispatch with the runtime need result")
    loops = by_id.get("review-repair-loop", [])
    if len(loops) != 1:
        errors.append(f"{label}: expected exactly one review-loop bounded repair body")
    else:
        loop = loops[0]
        cap = loop.get("max_iterations")
        if (
            loop.get("type") != "do-while"
            or "steps.review-next.output.stdout == 'true'" not in str(loop.get("condition"))
            or type(cap) is not int
            or not 1 <= cap <= 3
        ):
            errors.append(f"{label}: review-loop must recheck runtime need state with 1-3 safe slots")
        loop_steps = loop.get("steps", []) if isinstance(loop.get("steps", []), list) else []
        descendants = _walk_steps(loop_steps)
        commands = [child.get("command") for child in descendants]
        if "speckit.delivery.review-fix" not in commands or "speckit.review.run" not in commands:
            errors.append(f"{label}: review-loop must re-review and dispatch one repair pass")
        direct_ids = [child.get("id") for child in loop_steps if isinstance(child, dict)]
        if "review-fix" not in direct_ids or "review-recheck" not in direct_ids or direct_ids.index("review-fix") >= direct_ids.index("review-recheck"):
            errors.append(f"{label}: review-loop must repair before its independent re-review")
        repair = next((child for child in descendants if child.get("command") == "speckit.delivery.review-fix"), None)
        if repair is not None and f"repair_slots={cap}" not in str(repair.get("input", {}).get("args", "")):
            errors.append(f"{label}: repair_slots must match the YAML slot ceiling")
        if any(child.get("continue_on_error") for child in descendants):
            errors.append(f"{label}: review-loop cannot continue on command error")
        indexed = {child.get("id"): (index, child) for index, child in enumerate(loop_steps) if isinstance(child, dict)}
        for step_id, operation in (("review-reserve", "reserve"), ("review-complete", "complete")):
            node = indexed.get(step_id, (None, {}))[1]
            run = str(node.get("run", ""))
            if node.get("type") != "shell" or "delivery_runtime.py" not in run or f" {operation} " not in run or "--kind review" not in run:
                errors.append(f"{label}: review-loop requires a persisted runtime {step_id}")
        if indexed.get("review-reserve", (999, {}))[0] >= indexed.get("review-fix", (0, {}))[0]:
            errors.append(f"{label}: review-loop must reserve before editing")
        if indexed.get("review-complete", (0, {}))[0] <= indexed.get("review-recheck-record", (999, {}))[0]:
            errors.append(f"{label}: review-loop must complete only after fresh independent review recording")
        if not loop_steps or loop_steps[-1].get("id") != "review-next":
            errors.append(f"{label}: review-loop must finish by rechecking runtime needs")
        if repair and "attempt={{ steps.review-reserve.output.stdout }}" not in str(repair.get("input", {}).get("args", "")):
            errors.append(f"{label}: review repair must consume the reserved attempt")

    for step_id in ("review-final", "review-close"):
        for step in by_id.get(step_id, []):
            if step_id == "review-final":
                run = str(step.get("run", ""))
                if step.get("type") != "shell" or "--kind review" not in run or "require" not in run:
                    errors.append(f"{label}: review-final must be the runtime require guard")
            elif step.get("command") != "speckit.review.run":
                errors.append(f"{label}: {step_id} must invoke speckit.review.run")
    for step in by_id.get("review-gate", []):
        _check_gate(label, "review-gate", step, errors)

    def check_dispatch(step: dict[str, Any]) -> None:
        command = step.get("command", "")
        if command in {
            "speckit.delivery.doctor", "speckit.delivery.explore",
            "speckit.delivery.slice", "speckit.ralph.run", "speckit.review.run",
            "speckit.delivery.review-fix", "speckit.delivery.handoff",
            "speckit.delivery.method", "speckit.decision.context",
        }:
            args = str(step.get("input", {}).get("args", ""))
            if "delivery_run={{ inputs.delivery_run }}" not in args:
                errors.append(f"{label}: {step.get('id')} must forward the canonical delivery_run")
            if f"lane={workflow_id.removesuffix('-delivery')}" not in args:
                errors.append(f"{label}: {step.get('id')} must forward the actual lane")
        for key in ("steps", "then", "else"):
            children = step.get(key, [])
            if isinstance(children, list):
                for child in children:
                    if isinstance(child, dict):
                        check_dispatch(child)

    for step in steps:
        if isinstance(step, dict):
            check_dispatch(step)
    packet = ".specify/delivery/{{ inputs.delivery_run }}/exploration.md"
    if workflow_id in {"feature-delivery", "bugfix-delivery"}:
        wanted = ("explore", "specify", "clarify", "plan", "tasks") if workflow_id == "feature-delivery" else ("explore", "assess", "decision-context", "fix", "regression-test")
        for step_id in wanted:
            for step in by_id.get(step_id, []):
                if packet not in str(step.get("input", {}).get("args", "")):
                    errors.append(f"{label}: {step_id} must pass the exact exploration packet path")
        gate_id, consumer, choice = (
            ("scope-gate", "specify", "scope_approval") if workflow_id == "feature-delivery"
            else ("assessment-gate", "decision-context", "assessment_approval")
        )
        for gate in by_id.get(gate_id, []):
            if gate.get("show_file") != packet:
                errors.append(f"{label}: {gate_id} must display the persisted packet")
        for step in by_id.get(consumer, []):
            if f"{choice}={{{{ steps.{gate_id}.output.choice }}}}" not in str(step.get("input", {}).get("args", "")):
                errors.append(f"{label}: {consumer} must forward the actual {gate_id} choice")
    if workflow_id == "bugfix-delivery":
        slug_input = workflow.get("inputs", {}).get("bug_slug", {})
        if slug_input.get("type") != "string" or slug_input.get("required") is not True:
            errors.append(f"{label}: bug_slug must be an explicit required string input")
        for step_id in ("assess", "fix", "regression-test"):
            for step in by_id.get(step_id, []):
                if "slug={{ inputs.bug_slug }}" not in str(step.get("input", {}).get("args", "")):
                    errors.append(f"{label}: {step_id} must pass the explicit official Bug slug")
        for step in by_id.get("decision-context", []):
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

    ordered = (
        "tasks",
        "slice",
        "analyze",
        "analyze-require",
        "slice-gate",
        "slice-approval",
        "runtime-require-planning",
        "ralph",
    )
    positions: dict[str, int] = {}
    for step_id in ordered:
        matches = by_id.get(step_id, [])
        if len(matches) != 1:
            errors.append(f"{label}: expected exactly one {step_id} slice step")
            continue
        index, step = matches[0]
        positions[step_id] = index
        if step_id in {"slice", "slice-gate", "slice-approval", "ralph"} and step.get("continue_on_error"):
            errors.append(f"{label}: {step_id} cannot continue on error")
        if step_id in {"slice", "slice-approval"} and step.get("command") != "speckit.delivery.slice":
            errors.append(f"{label}: {step_id} must invoke speckit.delivery.slice")
        if step_id == "slice-approval":
            approval_args = str(step.get("input", {}).get("args", ""))
            for needle in (
                "action=record-approval",
                "delivery_run={{ inputs.delivery_run }}",
                "slices=.specify/delivery/{{ inputs.delivery_run }}/slices.md",
                "slice_approval={{ steps.slice-gate.output.choice }}",
            ):
                if needle not in approval_args:
                    errors.append(f"{label}: slice-approval must pass {needle}")
        if step_id == "analyze-require":
            run = str(step.get("run", ""))
            if step.get("type") != "shell" or "delivery_runtime.py" not in run or " require " not in run or "--kind analyze" not in run:
                errors.append(f"{label}: analyze-require must block before the combined execution/slice gate")
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
    for step in _walk_steps(steps):
        step_id = str(step.get("id"))
        args_by_id.setdefault(step_id, str(step.get("input", {}).get("args", "")))
    slice_args = args_by_id.get("slice", "")
    for needle in (
        "delivery_run={{ inputs.delivery_run }}",
        "slices=.specify/delivery/{{ inputs.delivery_run }}/slices.md",
        "design_approval={{ steps.plan-gate.output.choice }}",
    ):
        if needle not in slice_args:
            errors.append(f"{label}: slice must pass {needle}")
    for step_id in ("analyze", "ralph", "review-close", "handoff"):
        args = args_by_id.get(step_id, "")
        if "slices=.specify/delivery/{{ inputs.delivery_run }}/slices.md" not in args:
            errors.append(f"{label}: {step_id} must consume the exact slices path")
    if "slice_approval={{ steps.slice-gate.output.choice }}" not in args_by_id.get("ralph", ""):
        errors.append(f"{label}: ralph must forward the actual slice-gate choice")
    if "mode=auto" not in args_by_id.get("handoff", ""):
        errors.append(f"{label}: handoff must resolve slice versus rollup mode")


def _check_runtime_guards(
    workflow_id: str, workflow: dict[str, Any], errors: list[str]
) -> None:
    """Require explicit runtime initialization, need guards, and final requires."""
    if workflow_id not in {"feature-delivery", "bugfix-delivery", "lightweight-delivery"}:
        return
    label = f"workflows/{workflow_id}/workflow.yml"
    steps = _list(workflow.get("steps"), f"{label}:steps", errors)
    top = {step.get("id"): step for step in steps if isinstance(step, dict)}
    all_steps = _walk_steps(steps)
    by_id: dict[str, list[dict[str, Any]]] = {}
    for step in all_steps:
        by_id.setdefault(str(step.get("id")), []).append(step)

    def needs_shell(step_id: str, kind: str) -> None:
        matches = by_id.get(step_id, [])
        if len(matches) != 1 or matches[0].get("type") != "shell" or f"--kind {kind}" not in str(matches[0].get("run", "")):
            errors.append(f"{label}: {step_id} must call runtime needs --kind {kind}")

    if "runtime-init" not in top or "delivery_runtime.py" not in str(top["runtime-init"].get("run", "")) or " init " not in str(top["runtime-init"].get("run", "")):
        errors.append(f"{label}: runtime-init must initialize the Delivery runtime")
    python_input = workflow.get("inputs", {}).get("runtime_python", {})
    if python_input.get("type") != "string" or not python_input.get("default"):
        errors.append(f"{label}: runtime_python must select a verified Python 3.11+ invocation")

    def check_transport(sequence: list[Any]) -> None:
        for index, node in enumerate(sequence):
            if not isinstance(node, dict):
                continue
            args = str(node.get("input", {}).get("args", ""))
            match = re.search(r"\bruntime_stage=([a-z-]+)", args)
            if match:
                stage = match[1]
                result_path = f"runtime_result=.specify/delivery/{{{{ inputs.delivery_run }}}}/runtime/result-{stage}.json"
                if result_path not in args:
                    errors.append(f"{label}: {node.get('id')} must preserve its exact normalized runtime result path")
                before = sequence[index - 1] if index else {}
                after = sequence[index + 1] if index + 1 < len(sequence) else {}
                for adjacent, operation in ((before, "begin"), (after, "record")):
                    if not isinstance(adjacent, dict) or adjacent.get("type") != "shell" or "delivery_runtime.py" not in str(adjacent.get("run", "")) or f" {operation} " not in str(adjacent.get("run", "")) or f"--stage {stage}" not in str(adjacent.get("run", "")) or adjacent.get("continue_on_error"):
                        errors.append(f"{label}: {node.get('id')} needs an aborting runtime {operation} for {stage}")
            if node.get("type") == "shell" and "delivery_runtime.py" in str(node.get("run", "")):
                if "{{ inputs.runtime_python }}" not in str(node.get("run")):
                    errors.append(f"{label}: {node.get('id')} must use the selected runtime_python interpreter")
                if "--workflow-run {{ context.run_id }}" not in str(node.get("run")):
                    errors.append(f"{label}: {node.get('id')} must bind helper replay to the active engine occurrence")
            for key in ("steps", "then", "else"):
                children = node.get(key, [])
                if isinstance(children, list):
                    check_transport(children)

    check_transport(steps)
    top_ids = [step.get("id") for step in steps if isinstance(step, dict)]
    if "runtime-phase-handoff" not in top_ids or "handoff" not in top_ids or top_ids.index("runtime-phase-handoff") < top_ids.index("handoff"):
        errors.append(f"{label}: runtime-phase-handoff must follow a successful native handoff")
    for gate in by_id.get("simplify-gate", []):
        if gate.get("type") != "gate" or gate.get("on_reject") != "skip":
            errors.append(f"{label}: optional simplify-gate must let a recorded rejection skip application")
    for step_id in ("simplify-present", "simplify-decide", "simplify-accepted", "simplify-apply", "simplify-verify-require"):
        if len(by_id.get(step_id, [])) != 1:
            errors.append(f"{label}: simplification candidates need {step_id} before closure")
    needs_shell("review-needs-repair", "repair")
    guard = top.get("review-repair-if-needed")
    if not guard or guard.get("type") != "if" or "steps.review-needs-repair.output.stdout == 'true'" not in str(guard.get("condition")):
        errors.append(f"{label}: review repair must be conditionally guarded by runtime needs")
    final = top.get("review-final")
    if not final or final.get("type") != "shell" or "require" not in str(final.get("run", "")) or "--kind review" not in str(final.get("run", "")):
        errors.append(f"{label}: review-final must be the runtime review requirement")
    if workflow_id == "feature-delivery":
        needs_shell("convergence-needs", "convergence")
        convergence_if = top.get("convergence-if-needed")
        if not convergence_if or convergence_if.get("type") != "if" or "steps.convergence-needs.output.stdout == 'true'" not in str(convergence_if.get("condition")):
            errors.append(f"{label}: convergence work must be conditionally guarded")
        loops = by_id.get("convergence-loop", [])
        if len(loops) != 1 or "steps.convergence-next.output.stdout == 'true'" not in str(loops[0].get("condition")):
            errors.append(f"{label}: convergence-loop must recheck the runtime need result")
        elif isinstance(loops[0].get("steps"), list):
            convergence_steps = loops[0]["steps"]
            ordered_ids = [child.get("id") for child in convergence_steps if isinstance(child, dict)]
            required_order = ["convergence-reserve", "convergence-slice", "convergence-analyze", "convergence-analyze-require", "convergence-slice-gate", "convergence-slice-approval", "convergence-checkpoint", "convergence-planning-checkpoint", "convergence-ralph", "convergence-recheck", "convergence-complete", "convergence-next"]
            if any(item not in ordered_ids for item in required_order) or [ordered_ids.index(item) for item in required_order if item in ordered_ids] != sorted(ordered_ids.index(item) for item in required_order if item in ordered_ids):
                errors.append(f"{label}: convergence-loop must preserve Slice/Analyze/renewed gate/checkpoint/Ralph and reserved reassessment order")
            nodes = {child.get("id"): child for child in convergence_steps if isinstance(child, dict)}
            for item in ("convergence-slice", "convergence-slice-approval"):
                if nodes.get(item, {}).get("command") != "speckit.delivery.slice":
                    errors.append(f"{label}: {item} must remain Delivery Slice-owned")
            if "convergence-slice-gate" in nodes:
                _check_gate(label, "convergence-slice-gate", nodes["convergence-slice-gate"], errors)
            if "slice_approval={{ steps.convergence-slice-gate.output.choice }}" not in str(nodes.get("convergence-ralph", {}).get("input", {}).get("args", "")):
                errors.append(f"{label}: convergence Ralph must use the renewed slice-gate choice")
        required = top.get("convergence-require")
        if not required or required.get("type") != "shell" or "--kind convergence" not in str(required.get("run", "")):
            errors.append(f"{label}: convergence-require must reject unresolved convergence")
        needs_shell("simplify-needs", "simplification")
        simplify_if = top.get("simplify-if-needed")
        if not simplify_if or simplify_if.get("type") != "if" or "steps.simplify-needs.output.stdout == 'true'" not in str(simplify_if.get("condition")):
            errors.append(f"{label}: simplification verification must be conditional")
    else:
        needs_shell("simplify-needs", "simplification")
        simplify_if = top.get("simplify-if-needed")
        if not simplify_if or simplify_if.get("type") != "if" or "steps.simplify-needs.output.stdout == 'true'" not in str(simplify_if.get("condition")):
            errors.append(f"{label}: simplification verification must be conditional")


def _check_package_readme_workflow(
    workflow_id: str, workflow: dict[str, Any], errors: list[str]
) -> None:
    """Require the package README judgment before review in every lane."""
    prerequisites = {
        "feature-delivery": "docs-sync",
        "bugfix-delivery": "regression-test",
        "lightweight-delivery": "implement",
    }
    if workflow_id not in prerequisites:
        return
    label = f"workflows/{workflow_id}/workflow.yml"
    steps = _list(workflow.get("steps"), f"{label}:steps", errors)
    by_id: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for index, step in enumerate(steps):
        if isinstance(step, dict):
            by_id.setdefault(str(step.get("id")), []).append((index, step))

    matches = by_id.get("package-readme", [])
    if len(matches) != 1:
        errors.append(f"{label}: expected exactly one package-readme step")
        return
    index, step = matches[0]
    if step.get("command") != "speckit.docs-sync.package-readme":
        errors.append(
            f"{label}: package-readme must invoke speckit.docs-sync.package-readme"
        )
    if step.get("continue_on_error"):
        errors.append(f"{label}: package-readme cannot continue on error")
    args = str(step.get("input", {}).get("args", ""))
    lane = workflow_id.removesuffix("-delivery")
    for needle in (
        "delivery_run={{ inputs.delivery_run }}",
        f"lane={lane}",
        "scope=outgoing-diff",
    ):
        if needle not in args:
            errors.append(f"{label}: package-readme must pass {needle}")

    reviews = by_id.get("review-repair-if-needed", [])
    if len(reviews) != 1:
        errors.append(f"{label}: expected exactly one review-loop step")
    elif index >= reviews[0][0]:
        errors.append(f"{label}: package-readme must run before review-loop")
    for step_id in (
        "quality",
        "standards",
        "quality-after-simplify",
        "standards-after-simplify",
    ):
        for later_index, _ in by_id.get(step_id, []):
            if later_index < index:
                errors.append(
                    f"{label}: package-readme must run before {step_id} so docs are covered by current checks"
                )

    prerequisite = prerequisites[workflow_id]
    before = by_id.get(prerequisite, [])
    if len(before) != 1:
        errors.append(f"{label}: expected exactly one {prerequisite} step")
    elif index <= before[0][0]:
        errors.append(
            f"{label}: package-readme must run after {prerequisite} and the final code change"
        )


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
    _check_readme_docs(root, version, errors)

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
            route = next(
                (command for command in commands if command.get("name") == "speckit.delivery.route"),
                {},
            )
            if "sd" not in (route.get("aliases") or []):
                errors.append(f"{manifest_path}: speckit.delivery.route must declare the sd alias")
            for required in (
                "speckit.delivery.explore",
                "speckit.delivery.review-fix",
                "speckit.delivery.slice",
                "speckit.delivery.close",
                "speckit.delivery.method",
            ):
                if required not in command_names:
                    errors.append(f"{manifest_path}: missing {required} command")
            template = manifest_path.parent / "templates" / "exploration.md"
            if not template.is_file():
                errors.append(f"{manifest_path}: missing templates/exploration.md")
            slices_template = manifest_path.parent / "templates" / "slices.md"
            if not slices_template.is_file():
                errors.append(f"{manifest_path}: missing templates/slices.md")
            elif "SLICE_PLAN_FINGERPRINT" not in slices_template.read_text(encoding="utf-8"):
                errors.append(f"{slices_template}: missing slice plan fingerprint record")
            for required_runtime_resource in (
                "templates/runtime.md",
                "templates/core-adapter.md",
                "scripts/delivery_runtime.py",
            ):
                resource = manifest_path.parent / required_runtime_resource
                if not resource.is_file():
                    errors.append(f"{manifest_path}: missing {required_runtime_resource}")
            runtime_template = manifest_path.parent / "templates" / "runtime.md"
            if runtime_template.is_file() and "runtime_stage" not in runtime_template.read_text(encoding="utf-8"):
                errors.append(f"{runtime_template}: missing runtime_stage result contract")
            core_adapter = manifest_path.parent / "templates" / "core-adapter.md"
            if core_adapter.is_file() and "SD_CORE_HANDOFF: PASS" not in core_adapter.read_text(encoding="utf-8"):
                errors.append(f"{core_adapter}: missing planning checkpoint handoff marker")
            slice_command = manifest_path.parent / "commands" / "speckit.delivery.slice.md"
            if slice_command.is_file():
                slice_text = slice_command.read_text(encoding="utf-8")
                for needle in (
                    "action=record-approval",
                    "SLICE_PLAN_FINGERPRINT",
                    "SLICE_APPROVAL_RECORD",
                ):
                    if needle not in slice_text:
                        errors.append(f"{slice_command}: missing {needle!r} approval contract")
            for required_template in (
                "bugfix-review-repair.md",
                "repair-docs.md",
                "method-adapter.md",
                "method-design.md",
                "method-diagnose.md",
                "method-review.md",
            ):
                if not (
                    manifest_path.parent / "templates" / required_template
                ).is_file():
                    errors.append(
                        f"{manifest_path}: missing templates/{required_template}"
                    )
            method_config = manifest_path.parent / "config-template.yml"
            if (
                method_config.is_file()
                and "method_adapters:" not in method_config.read_text(encoding="utf-8")
            ):
                errors.append(f"{method_config}: missing method_adapters settings")
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
                for needle in (
                    "scripts/delivery_runtime.py",
                    "templates/runtime.md",
                    "templates/core-adapter.md",
                ):
                    if needle not in doctor_text:
                        errors.append(
                            f"{doctor}: Doctor must verify the guarded runtime resource {needle!r}"
                        )
            review_fix = manifest_path.parent / "commands" / "speckit.delivery.review-fix.md"
            if review_fix.is_file():
                text = review_fix.read_text(encoding="utf-8")
                for needle in ("templates/repair-docs.md", "DOCS_REFRESH"):
                    if needle not in text:
                        errors.append(
                            f"{review_fix}: repair must handle documentation refresh ({needle!r})"
                        )
            close = manifest_path.parent / "commands" / "speckit.delivery.close.md"
            if close.is_file():
                close_text = close.read_text(encoding="utf-8")
                if "never delete `evidence.md`" not in close_text.lower():
                    errors.append(
                        f"{close}: close must define the outcome contract ('never delete `evidence.md`')"
                    )
                for needle in (
                    "DELIVERY_STATUS:",
                    "outcome=merged|closed|superseded",
                ):
                    if needle not in close_text:
                        errors.append(
                            f"{close}: close must define the outcome contract ({needle!r})"
                        )
        if extension_id == "docs-sync":
            if "speckit.docs-sync.package-readme" not in command_names:
                errors.append(
                    f"{manifest_path}: missing speckit.docs-sync.package-readme command"
                )
            package_readme = (
                manifest_path.parent / "commands" / "speckit.docs-sync.package-readme.md"
            )
            if package_readme.is_file():
                text = package_readme.read_text(encoding="utf-8")
                for needle in ("repair=1", "INPUT_IDENTITY"):
                    if needle not in text:
                        errors.append(
                            f"{package_readme}: package README repair contract missing {needle!r}"
                        )
            template = manifest_path.parent / "templates" / "package-readme.md"
            if not template.is_file():
                errors.append(f"{manifest_path}: missing templates/package-readme.md")
            config_template = manifest_path.parent / "config-template.yml"
            if (
                config_template.is_file()
                and "package_readme:" not in config_template.read_text(encoding="utf-8")
            ):
                errors.append(
                    f"{config_template}: missing package_readme setting"
                )
        if extension_id == "ralph":
            template = manifest_path.parent / "templates" / "slice-execution.md"
            if not template.is_file():
                errors.append(f"{manifest_path}: missing templates/slice-execution.md")
            ralph_command = manifest_path.parent / "commands" / "speckit.ralph.run.md"
            if ralph_command.is_file():
                text = ralph_command.read_text(encoding="utf-8")
                for needle in ("DOCS_REFRESH", "with_docs_sync"):
                    if needle not in text:
                        errors.append(
                            f"{ralph_command}: missing task-closure documentation gate {needle!r}"
                        )
        if extension_id == "review":
            template = manifest_path.parent / "templates" / "reviewer.md"
            if not template.is_file():
                errors.append(f"{manifest_path}: missing templates/reviewer.md")
            elif "method_receipt:" not in template.read_text(encoding="utf-8"):
                errors.append(f"{template}: missing method_receipt report field")

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
        _check_runtime_guards(workflow_id, workflow, errors)
        _check_slice_workflow(workflow_id, workflow, errors)
        _check_package_readme_workflow(workflow_id, workflow, errors)
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
        floor_value = (
            definition_requires.get("speckit_version")
            if isinstance(definition_requires, dict)
            else None
        )
        floor = _minimum_version(floor_value)
        if floor is None or floor < (1, 2, 3):
            errors.append(
                f"workflows/{workflow_id}/workflow.yml: requires.speckit_version "
                f"must be >=1.2.3 for the guarded 0.4.x control flow "
                f"(got {floor_value!r})"
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
