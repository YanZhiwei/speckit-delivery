#!/usr/bin/env python3
"""Validate Delivery coordinator state and dispatch decisions, without model calls.

Native owners judge quality; this module checks transport, identity, freshness,
completeness, and bounded transitions. See ../templates/runtime.md.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import uuid
from typing import Any


SCHEMA = 1
NATIVE_RECEIPT_SCHEMA = 1
TASK_CLOSURE_SCHEMA = 1
LANES = {"feature", "bugfix", "lightweight"}
PHASES = {"intake", "exploration", "planning", "tasks", "execution", "verification", "handoff"}
DIMENSIONS = {
    "requirements", "code_quality", "architecture", "correctness",
    "security_compatibility", "test_effectiveness",
}
VERDICTS = {
    "quality": {"pass", "blocked"},
    "standards": {"pass", "blocked", "incomplete"},
    "review": {"pass", "blocked", "incomplete"},
    "converge": {"converged", "tasks-appended", "blocked"},
    "clarify": {"ready", "blocked"},
    "analyze": {"pass", "blocked", "incomplete"},
    "simplify": {"none", "candidates", "blocked"},
    "simplify-verify": {"pass", "fail", "not-applicable", "blocked"},
    "checkpoint": {"pass", "blocked"},
}
TERMINAL = {"delivered", "abandoned", "superseded"}
TASK = re.compile(r"^\s*-\s*\[([ xX])\]\s+(T\d+)\b", re.MULTILINE)
CHECKBOX = re.compile(
    r"^(?P<prefix>\s*(?:[-*+]\s+|\d+[.)]\s+))\[(?P<mark>[ xX])\](?P<suffix>.*?)(?P<newline>\r?\n)?$"
)
OPERATION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/=+,-]{0,159}$")
GIT_OBJECT = re.compile(r"^[0-9a-fA-F]{40,64}$")
HASH = re.compile(r"^[0-9a-f]{64}$")
NATIVE_RECEIPT_KEYS = {
    "schema_version", "receipt_type", "delivery_run", "lane", "stage", "scope",
    "head", "input_fingerprint", "ticket", "verdict", "report", "evidence", "data",
}
RESULT_INPUT_KEYS = {
    "schema_version", "delivery_run", "lane", "stage", "scope", "ticket",
    "input_fingerprint", "verdict", "report", "native_receipt", "data",
}
PLANNING_OUTPUT_NAMES = {"research.md", "data-model.md", "quickstart.md"}
PLANNING_RUN_NAMES = {"exploration.md", "code-context.md", "decision-context.md", "slices.md"}
CANONICAL_RUN_INPUT_NAMES = {"exploration.md", "slices.md", "decision-context.md", "code-context.md", "simplifications.md"}


class ProtocolError(ValueError):
    """An unsafe, incomplete, or stale coordinator transition."""


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def encoded(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def safe_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", value) or ".." in value or value.endswith(".") or value.endswith(" "):
        raise ProtocolError("Use a single safe run/scope segment without '..', a trailing dot/space, or path separators.")
    # Windows device names remain special even when an extension is appended.
    stem = value.split(".", 1)[0].upper()
    if stem in {"CON", "PRN", "AUX", "NUL"} or re.fullmatch(r"(?:COM|LPT)[1-9]", stem):
        raise ProtocolError("The run/scope id is a reserved device name; choose another safe id.")
    return value


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"Cannot read {path.name}; inspect and recover the original checkpoint: {exc}") from exc
    if not isinstance(value, dict):
        raise ProtocolError(f"{path.name} must contain a JSON object.")
    return value


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = stream.name
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def fields(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    output: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*(?:-\s*)?(?:\*\*)?([A-Za-z_]+)(?:\*\*)?\s*:\s*(.*?)\s*$", line)
        if match:
            output.setdefault(match[1].lower(), match[2].strip().strip("`"))
    return output


class Runtime:
    def __init__(self, root: Path, run: str):
        self.root = root.resolve()
        self.run = safe_id(run)
        self.directory = self.inside(f".specify/delivery/{self.run}")
        self.local = self.inside(f".specify/delivery/{self.run}/runtime")
        self.path = self.local / "state.json"

    def inside(self, value: str | Path) -> Path:
        raw = Path(value)
        path = raw if raw.is_absolute() else self.root / raw
        resolved = path.resolve()
        if not resolved.is_relative_to(self.root):
            raise ProtocolError(f"Path escapes the project: {value}")
        # Owned writes must not follow a symlink, even one pointing back inside.
        current = path
        while current != self.root and current.is_relative_to(self.root):
            if current.is_symlink():
                raise ProtocolError(f"Refusing a symlink in a coordinator path: {value}")
            current = current.parent
        return resolved

    def relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def git(self, *arguments: str) -> bytes:
        return self.git_at(self.root, *arguments)

    def git_at(self, cwd: Path, *arguments: str) -> bytes:
        cwd = self.inside(cwd)
        result = subprocess.run(
            ["git", "-C", str(cwd), *arguments], capture_output=True,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
        if result.returncode:
            raise ProtocolError(f"Git {' '.join(arguments[:2])} failed; restore the project worktree before continuing.")
        return result.stdout

    def _operation_id(self, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not OPERATION_ID.fullmatch(value):
            raise ProtocolError(
                "operation-id must be a stable nonempty token (letters, digits, '.', '_', ':', '@', '/', '=', '+', ',' or '-'; maximum 160 characters)."
            )
        return value

    def _operation_request(self, operation: str, values: dict[str, Any]) -> dict[str, Any]:
        return {"operation": operation, **values}

    def _operation_replay(
        self,
        state: dict[str, Any],
        operation_id: str | None,
        operation: str,
        request: dict[str, Any],
    ) -> dict[str, Any] | None:
        operation_id = self._operation_id(operation_id)
        if operation_id is None:
            return None
        operations = state.setdefault("operations", {})
        existing = operations.get(operation_id)
        if existing is None:
            return None
        if (
            not isinstance(existing, dict)
            or existing.get("operation") != operation
            or existing.get("request_fingerprint") != digest(encoded(request))
            or not isinstance(existing.get("result"), dict)
        ):
            raise ProtocolError(
                f"operation-id {operation_id!r} was already used for a different {operation}; use a new occurrence key instead of replaying a real new round."
            )
        return json.loads(json.dumps(existing["result"], ensure_ascii=False))

    def _operation_store(
        self,
        state: dict[str, Any],
        operation_id: str | None,
        operation: str,
        request: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        operation_id = self._operation_id(operation_id)
        if operation_id is None:
            return
        state.setdefault("operations", {})[operation_id] = {
            "operation": operation,
            "request_fingerprint": digest(encoded(request)),
            "result": json.loads(json.dumps(result, ensure_ascii=False)),
        }

    def _workflow_component(self, value: str) -> str:
        raw = str(value)
        readable = re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("_") or "empty"
        suffix = digest(raw.encode("utf-8"))[:16]
        return f"{readable[:32]}-{suffix}"

    def workflow_operation_id(self, workflow_run: str, operation: str, arguments: dict[str, Any]) -> str:
        """Derive one replay key from the engine's persisted active occurrence.

        The helper never scans for a newest workflow or guesses a loop counter.
        The engine must have persisted current_step_id before invoking this
        process; an occurrence path, when available, is included as a bound
        component and its digest preserves the full path even when punctuation
        is not valid in an operation id.
        """
        workflow_run = safe_id(workflow_run)
        path = self.inside(f".specify/workflows/runs/{workflow_run}/state.json")
        if not path.is_file() or path.is_symlink():
            raise ProtocolError("--workflow-run needs the exact engine state.json for its active occurrence; use --operation-id only for direct CLI calls.")
        engine = read_json(path)
        identity_values = [engine.get("run_id"), engine.get("workflow_run"), engine.get("id")]
        if any(value is not None and value != workflow_run for value in identity_values):
            raise ProtocolError("Engine workflow state identity does not match --workflow-run; refusing to journal another run.")
        inputs = engine.get("inputs") if isinstance(engine.get("inputs"), dict) else None
        delivery_input = inputs.get("delivery_run") if inputs is not None else None
        if isinstance(delivery_input, dict):
            delivery_input = delivery_input.get("value")
        if delivery_input != self.run:
            raise ProtocolError("Engine workflow checkpoint inputs.delivery_run does not match the helper --run.")
        context = engine.get("context") if isinstance(engine.get("context"), dict) else {}
        for container in (engine, context):
            delivery = container.get("delivery_run")
            if delivery is not None and delivery != self.run:
                raise ProtocolError("Engine workflow checkpoint delivery_run does not match the helper --run.")
        execution = engine.get("execution") if isinstance(engine.get("execution"), dict) else {}
        step = engine.get("current_step_id") or execution.get("current_step_id")
        occurrence = (
            engine.get("current_occurrence_path") or engine.get("active_occurrence_path")
            or engine.get("execution_path") or execution.get("current_occurrence_path")
            or execution.get("active_occurrence_path") or execution.get("path")
        )
        if not isinstance(step, str) or not step.strip():
            raise ProtocolError("Engine state has no persisted current_step_id; refusing to guess a replay occurrence.")
        workflow_status = str(engine.get("status") or engine.get("workflow_status") or "").lower()
        if workflow_status in {"completed", "succeeded", "cancelled", "canceled", "aborted"}:
            raise ProtocolError("Engine workflow occurrence is no longer active; refusing to replay a finished step.")
        active_step = engine.get("active_step_id") or execution.get("active_step_id")
        if active_step is not None and active_step != step:
            raise ProtocolError("Engine current_step_id is not the active step; refusing to guess an occurrence.")
        completed_steps = engine.get("completed_step_ids") or engine.get("completed_steps")
        if isinstance(completed_steps, list) and step in completed_steps:
            raise ProtocolError("Engine current_step_id is already completed; use the next persisted occurrence.")
        step_states = engine.get("steps")
        if isinstance(step_states, dict) and isinstance(step_states.get(step), dict):
            step_status = str(step_states[step].get("status", "")).lower()
            if step_status in {"completed", "succeeded", "failed", "cancelled", "canceled"}:
                raise ProtocolError("Engine current step is no longer active; refusing to replay a finished occurrence.")
        if occurrence is None:
            occurrence = step
        if not isinstance(occurrence, str) or not occurrence.strip():
            raise ProtocolError("Engine active occurrence path is malformed; resume from the engine checkpoint.")
        raw_args = {key: value for key, value in arguments.items() if key not in {"root", "workflow_run", "operation_id"} and value not in (None, False, [], {})}
        raw = encoded({"workflow_run": workflow_run, "delivery_run": self.run, "step": step, "occurrence": occurrence, "operation": operation, "arguments": raw_args})
        identifier = f"workflow-{self._workflow_component(workflow_run)}-{self._workflow_component(step)}-{self._workflow_component(occurrence)}-{self._workflow_component(operation)}-{self._workflow_component(self.run)}"
        if len(identifier) > 160:
            identifier = "workflow-" + digest(raw)
        return identifier

    def load(self) -> dict[str, Any]:
        state = read_json(self.path)
        if (state.get("schema_version"), state.get("delivery_run")) != (SCHEMA, self.run):
            raise ProtocolError("Checkpoint schema/run mismatch; recover the original run, do not initialize a replacement.")
        if state.get("lane") not in LANES or state.get("root") != str(self.root):
            raise ProtocolError("Checkpoint lane/worktree mismatch; inspect the original run binding.")
        if state.get("phase") not in PHASES:
            raise ProtocolError("Checkpoint phase is invalid; recover the original owner transition instead of skipping it.")
        if type(state.get("revision")) is not int or state["revision"] < 0:
            raise ProtocolError("Checkpoint revision is malformed; recover the original state before resuming it.")
        for key in ("bindings", "stages", "pending", "attempts", "approvals"):
            if not isinstance(state.get(key), dict):
                raise ProtocolError(f"Checkpoint is missing {key}; recover it without resetting counters.")
        if "operations" in state and not isinstance(state["operations"], dict):
            raise ProtocolError("Checkpoint operation ledger is malformed; recover it without replaying mutations.")
        self._validate_bindings(state["bindings"])
        self._validate_approvals(state["approvals"])
        self._validate_operations(state.get("operations", {}))
        self._validate_observation(state.get("evidence_observation"), "evidence")
        self._validate_observation(state.get("handoff_observation"), "handoff")
        self._validate_checkpoint_history(state.get("checkpoint_history", []), state)
        for stage, pending in state["pending"].items():
            self._validate_pending(state, stage, pending)
        for stage, result in state["stages"].items():
            if stage not in VERDICTS or not isinstance(result, dict):
                raise ProtocolError("Checkpoint contains an unknown or malformed completed stage.")
            self._validate_result_shape(state, stage, result, stored=True, dynamic=False)
        outgoing = state.get("outgoing_review")
        if outgoing is not None:
            if not isinstance(outgoing, dict) or outgoing.get("scope") != "outgoing-diff":
                raise ProtocolError("Integrated Review history is malformed; recover its original finding states.")
            self._validate_result_shape(state, "review", outgoing, stored=True, dynamic=False)
        for key, budget in state["attempts"].items():
            if not isinstance(key, str) or not isinstance(budget, dict):
                raise ProtocolError("Checkpoint attempt accounting is malformed; do not allocate a replacement budget.")
            if type(budget.get("used")) is not int or budget["used"] < 0:
                raise ProtocolError(f"Attempt counter {key!r} is malformed; recover its original value.")
            pending = budget.get("pending")
            if pending is not None and (type(pending) is not int or pending < 1 or pending > budget["used"]):
                raise ProtocolError(f"Pending attempt {key!r} is malformed; resume or recover the original reservation.")
            if "operation_id" in budget:
                self._operation_id(budget["operation_id"])
        return state

    def _validate_bindings(self, bindings: dict[str, Any]) -> None:
        for key, value in bindings.items():
            if key == "inputs":
                if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                    raise ProtocolError("Checkpoint input bindings are malformed; recover the original explicit inputs.")
                for item in value:
                    self.inside(item)
            elif not isinstance(value, str):
                raise ProtocolError(f"Checkpoint binding {key!r} is malformed; recover the original path.")
            else:
                self.inside(value)

    def _validate_operations(self, operations: dict[str, Any]) -> None:
        for operation_id, entry in operations.items():
            self._operation_id(operation_id)
            if not isinstance(entry, dict) or not isinstance(entry.get("operation"), str):
                raise ProtocolError("Checkpoint operation ledger entry is malformed; do not replay it.")
            if not isinstance(entry.get("request_fingerprint"), str) or not HASH.fullmatch(entry["request_fingerprint"]):
                raise ProtocolError("Checkpoint operation request fingerprint is malformed; recover the original occurrence.")
            if not isinstance(entry.get("result"), dict):
                raise ProtocolError("Checkpoint operation result is malformed; recover the original occurrence.")

    def _validate_approvals(self, approvals: dict[str, Any]) -> None:
        for name, approval in approvals.items():
            if not isinstance(name, str) or not isinstance(approval, dict) or approval.get("choice") not in {"pending", "approve", "reject"}:
                raise ProtocolError("Checkpoint approval receipt is malformed; present the gate inputs again.")
            inputs = approval.get("inputs")
            if not isinstance(inputs, dict) or any(not isinstance(path, str) or not HASH.fullmatch(value) for path, value in inputs.items()):
                raise ProtocolError("Checkpoint approval inputs are malformed; do not reuse the choice.")
            for path in inputs:
                self.inside(path)
            if not isinstance(approval.get("presented_head"), str) or not GIT_OBJECT.fullmatch(approval["presented_head"]):
                raise ProtocolError("Checkpoint approval HEAD is malformed; present the gate inputs again.")
            if "candidate_ids" in approval:
                candidates = approval["candidate_ids"]
                if not isinstance(candidates, list) or not candidates or any(not isinstance(item, str) or not item.strip() for item in candidates) or len(set(candidates)) != len(candidates):
                    raise ProtocolError("Checkpoint candidate approval is malformed; present the native proposal again.")
            if "operation_id" in approval:
                self._operation_id(approval["operation_id"])

    def _validate_pending(self, state: dict[str, Any], stage: str, pending: Any) -> None:
        if stage not in VERDICTS or not isinstance(pending, dict):
            raise ProtocolError("Checkpoint contains an unknown or malformed pending stage.")
        required = ("schema_version", "delivery_run", "lane", "stage", "scope", "ticket", "input_fingerprint", "snapshot")
        if any(key not in pending for key in required):
            raise ProtocolError(f"Pending {stage} input is incomplete; resume the original stage manually.")
        if pending.get("schema_version") != SCHEMA or pending.get("delivery_run") != self.run or pending.get("lane") != state["lane"] or pending.get("stage") != stage:
            raise ProtocolError(f"Pending {stage} identity does not match this run.")
        if not isinstance(pending.get("ticket"), str) or not pending["ticket"] or not isinstance(pending.get("input_fingerprint"), str) or not HASH.fullmatch(pending["input_fingerprint"]):
            raise ProtocolError(f"Pending {stage} ticket is malformed; resume the original stage manually.")
        safe_id(pending["scope"])
        self._validate_snapshot_shape(pending["snapshot"])
        if pending["snapshot"].get("fingerprint") != pending["input_fingerprint"]:
            raise ProtocolError(f"Pending {stage} snapshot fingerprint is inconsistent; recover the original ticket.")
        if stage == "converge" and (not isinstance(pending.get("tasks_before_b64"), str) or not isinstance(pending.get("tasks_before_sha256"), str) or not HASH.fullmatch(pending["tasks_before_sha256"])):
            raise ProtocolError("Convergence input has no valid byte-exact queue snapshot; recover the original ticket.")
        if "operation_id" in pending:
            self._operation_id(pending["operation_id"])
        input_path = self.local / f"input-{stage}.json"
        if not input_path.is_file() or read_json(input_path) != pending:
            raise ProtocolError(f"Pending {stage} input file is missing or differs from checkpoint state; recover the original ticket.")

    def _validate_snapshot_shape(self, snapshot: Any) -> None:
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get("head"), str) or not GIT_OBJECT.fullmatch(snapshot["head"]):
            raise ProtocolError("A stored snapshot is malformed; recover the original input identity.")
        if not isinstance(snapshot.get("fingerprint"), str) or not HASH.fullmatch(snapshot["fingerprint"]):
            raise ProtocolError("A stored snapshot fingerprint is malformed; recover the original input identity.")
        for key in ("files", "worktree", "index", "submodules"):
            if not isinstance(snapshot.get(key), (dict, list)):
                raise ProtocolError("A stored snapshot is missing conservative worktree/index identity; recover the original input.")

    def _validate_observation(self, observation: Any, kind: str) -> None:
        if observation is None:
            return
        if not isinstance(observation, dict) or set(observation) != {"kind", "path", "sha256", "head", "input_fingerprint"}:
            raise ProtocolError(f"Stored {kind} observation is malformed; rerun the native owner before continuing.")
        if observation.get("kind") != kind or not isinstance(observation.get("path"), str) or not HASH.fullmatch(observation.get("sha256", "")) or not GIT_OBJECT.fullmatch(observation.get("head", "")) or not HASH.fullmatch(observation.get("input_fingerprint", "")):
            raise ProtocolError(f"Stored {kind} observation identity is malformed; rerun the native owner before continuing.")
        self.inside(observation["path"])

    def _validate_checkpoint_association(self, association: Any, state: dict[str, Any]) -> None:
        required = {"checkpoint_ticket", "analyze_ticket", "analyze_output_fingerprint", "prior_head", "new_head", "approved_paths", "report", "native_receipt"}
        if not isinstance(association, dict) or set(association) != required:
            raise ProtocolError("Planning checkpoint Analyze association is malformed; recover the native checkpoint.")
        if any(not isinstance(association.get(key), str) or not association[key] for key in ("checkpoint_ticket", "analyze_ticket")):
            raise ProtocolError("Planning checkpoint Analyze association tickets are malformed.")
        if not HASH.fullmatch(association["analyze_output_fingerprint"]) or not GIT_OBJECT.fullmatch(association["prior_head"]) or not GIT_OBJECT.fullmatch(association["new_head"]):
            raise ProtocolError("Planning checkpoint Analyze association fingerprints/HEADs are malformed.")
        approved = association["approved_paths"]
        if not isinstance(approved, list) or not approved or any(not isinstance(item, str) or self.relative(self.inside(item)) != item for item in approved) or len(set(approved)) != len(approved):
            raise ProtocolError("Planning checkpoint Analyze association needs exact normalized approved paths.")
        self.reference(association["report"])
        self.reference(association["native_receipt"])

    def _validate_checkpoint_history(self, history: Any, state: dict[str, Any]) -> None:
        if not isinstance(history, list):
            raise ProtocolError("Planning checkpoint history is malformed; recover the original planning chain.")
        for association in history:
            self._validate_checkpoint_association(association, state)

    def _component(self, name: str) -> Any:
        path = Path(__file__).with_name(f"delivery_{name}.py")
        spec = importlib.util.spec_from_file_location(f"delivery_{name}", path)
        if spec is None or spec.loader is None:
            raise ProtocolError(f"Installed Delivery {name} helper is missing; refresh the Delivery installation.")
        module = importlib.util.module_from_spec(spec)
        # Loading an installed companion must not create __pycache__ inside a
        # consumer project and dirty an otherwise read-only status/checkpoint.
        exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
        return module

    def task_start(self, task: str, branch: str, inputs: list[str]) -> dict[str, Any]:
        return self._component("tasks").TaskClosure(self, ProtocolError).start(task, branch, inputs)

    def task_gate(self, task: str, file: str | None = None) -> dict[str, Any]:
        return self._component("tasks").TaskClosure(self, ProtocolError).gate(task, file)

    def task_record(self, task: str, commit: str) -> dict[str, Any]:
        return self._component("tasks").TaskClosure(self, ProtocolError).record(task, commit)

    def audit_task_closure(self, state: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._component("tasks").TaskClosure(self, ProtocolError).audit(state)

    def close_record(self, outcome: str, verified: bool, pr: str | None, file: str | None) -> dict[str, Any]:
        # The Close companion validates everything and writes Evidence first;
        # only after that succeeds may the coordinator refresh its hash-bound
        # observation. A failed validation therefore cannot advance state.
        try:
            result = self._component("outcome").close_record(self, outcome, verified, pr, file)
        except ValueError as exc:
            raise ProtocolError(str(exc)) from exc
        state = self.load()
        state["evidence_observation"] = self._observe_evidence(state)
        self.save(state)
        return result


    def _operational_record(self, name: str) -> bool:
        """Declared coordinator records never block execution entry."""
        run_prefix = f".specify/delivery/{self.run}/"
        if name.startswith(run_prefix):
            relative = name[len(run_prefix):]
            if relative.split("/", 1)[0] in {"runtime", "reviews", "receipts", "checks"}:
                return True
            if relative in {
                "task-verdicts.yml", "slice-verdicts.yml", "evidence.md",
            } or re.fullmatch(r"pull-request(?:-[A-Za-z0-9._-]+)?\.md", relative):
                return True
        return name.startswith(".specify/workflows/runs/")

    def execution_dirty_paths(self) -> list[str]:
        entries = self.git("status", "--porcelain=v1", "-z", "--untracked-files=all").split(b"\0")
        dirty: list[str] = []
        index = 0
        while index < len(entries):
            entry = entries[index]
            index += 1
            if not entry:
                continue
            if len(entry) < 4 or entry[2:3] != b" ":
                raise ProtocolError("Malformed Git status entry; recover the index before execution.")
            names = [os.fsdecode(entry[3:]).replace("\\", "/")]
            if b"R" in entry[:2] or b"C" in entry[:2]:
                if index >= len(entries) or not entries[index]:
                    raise ProtocolError("Git rename/copy status has no original path.")
                names.append(os.fsdecode(entries[index]).replace("\\", "/"))
                index += 1
            for name in names:
                if name and not self._operational_record(name) and name not in dirty:
                    dirty.append(name)
        return dirty

    def save(self, state: dict[str, Any]) -> None:
        self.inside(self.path)
        state["revision"] = state.get("revision", 0) + 1
        atomic_json(self.path, state)

    def limits(self) -> dict[str, int]:
        path = self.inside(".specify/extensions/delivery/delivery-config.yml")
        if not path.is_file():
            return {"review": 3, "convergence": 3}
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ProtocolError(f"Cannot read delivery configuration; fix it before continuing: {exc}") from exc
        output: dict[str, int] = {}
        for kind, field in (("review", "max_review_fix_rounds"), ("convergence", "max_convergence_rounds")):
            values: list[str] = []
            for raw_line in text.splitlines():
                line = raw_line.split("#", 1)[0].rstrip()
                if not line.strip():
                    continue
                match = re.match(rf"^\s*{re.escape(field)}\s*:\s*(.*?)\s*$", line)
                if match:
                    values.append(match[1])
                    continue
                # A relevant key in a flow mapping, list item, quoted key, or
                # other unsupported YAML representation must not disappear into
                # the default budget.
                if re.search(rf"(?:^|[-{{,\[\"'])\s*{re.escape(field)}\s*:", line):
                    raise ProtocolError(
                        f"{field} must use an indented block scalar such as '{field}: 2'; flow/quoted YAML is unsupported."
                    )
            if len(values) > 1:
                raise ProtocolError(f"Duplicate {field}; use one integer from 1 through 3.")
            value = values[0] if values else "3"
            if not re.fullmatch(r"[1-3]", value):
                raise ProtocolError(f"{field} must be an unquoted integer scalar from 1 through 3; fix the project configuration.")
            output[kind] = int(value)
        return output

    def init(self, lane: str, bug_slug: str | None = None, operation_id: str | None = None) -> dict[str, Any]:
        if lane not in LANES:
            raise ProtocolError("Select feature, bugfix, or lightweight.")
        if lane == "bugfix":
            if not isinstance(bug_slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", bug_slug):
                raise ProtocolError("Bugfix runs require an explicit lowercase kebab-case bug-slug.")
        elif bug_slug is not None:
            raise ProtocolError("bug-slug is valid only for the Bugfix lane.")
        request = self._operation_request("init", {"lane": lane, "bug_slug": bug_slug})
        if self.path.exists():
            state = self.load()
            replay = self._operation_replay(state, operation_id, "init", request)
            if replay is not None:
                return replay
            if state["lane"] != lane or state.get("bug_slug") != bug_slug:
                raise ProtocolError("Run identity already exists with another lane/bug mapping; resume the original run.")
            self.limits()
            self._operation_store(state, operation_id, "init", request, state)
            if operation_id is not None:
                self.save(state)
            return state
        if self.directory.exists() and any(self.directory.iterdir()):
            raise ProtocolError("Legacy or interrupted artifacts already exist without this checkpoint. Use status and recover their identity/counters; do not reset them with init.")
        head = self.git("rev-parse", "HEAD").decode().strip()
        if bug_slug is not None:
            safe_id(bug_slug)
        state = {
            "schema_version": SCHEMA, "delivery_run": self.run, "lane": lane,
            "root": str(self.root), "bug_slug": bug_slug, "phase": "intake",
            "started_head": head, "revision": 0, "bindings": {}, "stages": {},
            "pending": {}, "attempts": {}, "approvals": {}, "operations": {},
            "evidence_observation": None, "handoff_observation": None,
            "checkpoint_history": [],
        }
        self.limits()
        # Only operational bookkeeping is local; planning/evidence policy is untouched.
        exclude_raw = self.git("rev-parse", "--git-path", "info/exclude").decode().strip()
        exclude = Path(exclude_raw)
        if not exclude.is_absolute():
            exclude = self.root / exclude
        exclude.parent.mkdir(parents=True, exist_ok=True)
        rules = (f"/.specify/delivery/{self.run}/runtime/", "/.specify/workflows/runs/")
        previous = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
        missing = [rule for rule in rules if rule not in previous.splitlines()]
        if missing:
            with exclude.open("a", encoding="utf-8") as stream:
                stream.write(("\n" if previous and not previous.endswith("\n") else "") + "\n".join(missing) + "\n")
        self._operation_store(state, operation_id, "init", request, state)
        self.save(state)
        return state

    def bind_from_packet(self, packet: str, operation_id: str | None = None, inputs: list[str] | None = None) -> dict[str, Any]:
        state = self.load()
        inputs = list(inputs or [])
        request = self._operation_request("bind-from-packet", {"packet": packet, "inputs": inputs})
        replay = self._operation_replay(state, operation_id, "bind-from-packet", request)
        if replay is not None:
            return replay
        path = self.inside(packet)
        if not path.is_file() or not path.is_relative_to(self.directory):
            raise ProtocolError("Bind the Feature from this run's persisted packet; the packet path must be canonical and existing.")
        matches: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^\s*(?:[-*]\s*)?(?:FEATURE_DIR|FEATURE_PATH|feature_dir|feature_path)\s*:\s*(.*?)\s*$", line)
            if match:
                value = match[1].strip().strip("`").strip()
                if value:
                    matches.append(value)
        if len(set(matches)) != 1:
            raise ProtocolError("The packet must contain exactly one explicit FEATURE_DIR:/FEATURE_PATH: emitted by Core Specify.")
        bindings = self._bind_impl(state, matches[0], None, inputs)
        self._operation_store(state, operation_id, "bind-from-packet", request, bindings)
        self.save(state)
        return bindings

    def _bind_impl(self, state: dict[str, Any], feature_dir: str | None, assessment: str | None, inputs: list[str]) -> dict[str, Any]:
        updates: dict[str, Any] = {}
        directory: Path | None = None
        if feature_dir:
            if state["lane"] != "feature":
                raise ProtocolError("Only Feature binds Spec/Plan/Tasks; do not create Feature artifacts for another lane.")
            directory = self.inside(feature_dir)
            updates.update({name: self.relative(directory / f"{name}.md") for name in ("spec", "plan", "tasks")})
            # Clarify may touch only this governed checklist, when Core has
            # actually emitted it. Persist the expected path even before the
            # optional file exists so packet/direct binding behaves identically.
            updates["clarification_checklist"] = self.relative(directory / "checklists" / "requirements.md")
        if assessment:
            if state["lane"] != "bugfix":
                raise ProtocolError("Assessment binding requires the Bugfix lane.")
            path = self.inside(assessment)
            if state.get("bug_slug") and path != self.root / f".specify/bugs/{state['bug_slug']}/assessment.md":
                raise ProtocolError("Assessment does not match the explicit Bug slug.")
            updates["assessment"] = self.relative(path)
        for name, value in updates.items():
            if name in state["bindings"] and state["bindings"][name] != value:
                raise ProtocolError(f"Cannot relocate this run's {name}; recover the original mapping.")
            state["bindings"][name] = value
        bound = state["bindings"].setdefault("inputs", [])
        for value in inputs:
            relative = self.relative(self.inside(value))
            if relative not in bound:
                bound.append(relative)
            if directory is not None and relative == self.relative(directory / "checklists" / "requirements.md"):
                state["bindings"]["clarification_checklist"] = relative
        return state["bindings"]

    def bind(self, feature_dir: str | None, assessment: str | None, inputs: list[str], operation_id: str | None = None) -> dict[str, Any]:
        state = self.load()
        request = self._operation_request("bind", {"feature_dir": feature_dir, "assessment": assessment, "inputs": list(inputs)})
        replay = self._operation_replay(state, operation_id, "bind", request)
        if replay is not None:
            return replay
        bindings = self._bind_impl(state, feature_dir, assessment, inputs)
        self._operation_store(state, operation_id, "bind", request, bindings)
        self.save(state)
        return bindings

    def _index_entries(self, repository: Path, prefix: str = "") -> list[dict[str, Any]]:
        raw = self.git_at(repository, "ls-files", "--stage", "-z")
        entries: list[dict[str, Any]] = []
        for record in raw.split(b"\0"):
            if not record:
                continue
            try:
                metadata, raw_path = record.split(b"\t", 1)
                mode, object_id, stage = metadata.decode("ascii").split()
                relative = os.fsdecode(raw_path).replace("\\", "/")
            except (UnicodeDecodeError, ValueError) as exc:
                raise ProtocolError("Git index contains an unreadable staged entry; resolve the index before continuing.") from exc
            if not re.fullmatch(r"[0-9]{6}", mode) or not re.fullmatch(r"[0-3]", stage) or not GIT_OBJECT.fullmatch(object_id):
                raise ProtocolError("Git index contains a malformed mode/object/stage entry; resolve it before continuing.")
            entries.append({"path": prefix + relative, "mode": mode, "object": object_id.lower(), "stage": int(stage)})
        return sorted(entries, key=lambda item: (item["path"], item["stage"], item["mode"], item["object"]))

    def _repository_names(self, repository: Path) -> set[str]:
        names: set[str] = set()
        for arguments in (("--cached",), ("--others", "--exclude-standard")):
            raw = self.git_at(repository, "ls-files", "-z", *arguments)
            names.update(os.fsdecode(value).replace("\\", "/") for value in raw.split(b"\0") if value)
        return names

    def _snapshot_bytes(self, name: str, path: Path) -> bytes:
        raw = path.read_bytes()
        if name != f".specify/delivery/{self.run}/slices.md":
            return raw
        try:
            lines = raw.decode("utf-8").splitlines(keepends=True)
        except UnicodeDecodeError:
            return raw
        approval_line = re.compile(
            r"^\s*(?:[-*]\s*)?(?:SLICE_APPROVAL|Choice / accepted risks|Choice|Approved by|Approved mode / snapshot|Approved mode|Approved at)\s*:",
            re.IGNORECASE,
        )
        return "".join(line for line in lines if not approval_line.match(line)).encode("utf-8")

    def _worktree_entry(self, path: Path) -> dict[str, Any]:
        try:
            info = path.lstat()
        except FileNotFoundError:
            return {"kind": "missing"}
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISLNK(info.st_mode):
            target = os.fsdecode(os.readlink(path))
            return {"kind": "symlink", "mode": mode, "target": target}
        if stat.S_ISREG(info.st_mode):
            content = path.read_bytes()
            return {"kind": "file", "mode": mode, "sha256": digest(content)}
        if stat.S_ISDIR(info.st_mode):
            return {"kind": "directory", "mode": mode}
        return {"kind": "special", "mode": mode, "sha256": digest(path.read_bytes())}

    def _directory_manifest(self, path: Path) -> list[dict[str, Any]]:
        """Return conservative bytes/modes for a directory without following .git."""
        if not path.exists() or not path.is_dir():
            return [{"path": ".", **self._worktree_entry(path)}]
        entries: list[dict[str, Any]] = []
        for root, directories, files in os.walk(path, topdown=True, followlinks=False):
            directories.sort()
            files.sort()
            kept: list[str] = []
            for name in directories:
                child = Path(root) / name
                relative = child.relative_to(path).as_posix()
                if name == ".git":
                    continue
                item = self._worktree_entry(child)
                entries.append({"path": relative, **item})
                if item.get("kind") == "directory":
                    kept.append(name)
            directories[:] = kept
            for name in files:
                child = Path(root) / name
                if name == ".git":
                    continue
                relative = child.relative_to(path).as_posix()
                entries.append({"path": relative, **self._worktree_entry(child)})
        return sorted(entries, key=lambda item: item["path"])

    def _submodule_snapshot(self, path: Path, depth: int = 0) -> dict[str, Any]:
        if depth > 8:
            raise ProtocolError("Nested submodule depth exceeds the conservative snapshot limit.")
        try:
            head = self.git_at(path, "rev-parse", "HEAD").decode("ascii", errors="strict").strip()
            if not GIT_OBJECT.fullmatch(head):
                raise ProtocolError("Submodule HEAD is malformed; restore the submodule before continuing.")
            index = self._index_entries(path)
            names = self._repository_names(path)
        except (ProtocolError, UnicodeError):
            return {"head": "missing", "index": [], "files": {}, "worktree": {}, "submodules": {}, "status": "missing", "fingerprint": digest(b"missing-submodule")}
        modes = {entry["path"]: entry["mode"] for entry in index if entry["stage"] == 0}
        files: dict[str, str] = {}
        worktree: dict[str, Any] = {}
        submodules: dict[str, Any] = {}
        for name in sorted(names):
            child = path / Path(name)
            if modes.get(name) == "160000":
                nested = self._submodule_snapshot(child, depth + 1)
                submodules[name] = nested
                worktree[name] = {"kind": "submodule", "mode": self._worktree_entry(child).get("mode", 0), "sha256": nested["fingerprint"]}
                files[name] = nested["fingerprint"]
            else:
                item = self._worktree_entry(child)
                worktree[name] = item
                files[name] = item.get("sha256", "missing") if item.get("kind") == "file" else digest(encoded(item)) if item.get("kind") != "missing" else "missing"
        try:
            status = self.git_at(path, "status", "--porcelain=v1", "--untracked-files=all").decode("utf-8", errors="replace")
        except ProtocolError:
            status = "unavailable"
        value = {"head": head, "index": index, "files": files, "worktree": worktree, "submodules": submodules, "status": status}
        value["fingerprint"] = digest(encoded(value))
        return value

    def _directory_fingerprint(self, name: str, path: Path) -> str:
        """Hash a bound directory including worktree modes and all nested bytes."""
        return digest(encoded(self._directory_manifest(path)))

    @staticmethod
    def _simplify_noop(state: dict[str, Any]) -> bool:
        """A no-candidate scan is bookkeeping, not a new content input."""
        result = state.get("stages", {}).get("simplify")
        return (
            isinstance(result, dict)
            and isinstance(result.get("data"), dict)
            and result["data"].get("candidates") == []
        )

    def _canonical_run_inputs(
        self, state: dict[str, Any], simplify_noop: bool | None = None
    ) -> set[str]:
        names = set(CANONICAL_RUN_INPUT_NAMES)
        if simplify_noop is None:
            simplify_noop = self._simplify_noop(state)
        if simplify_noop:
            names.discard("simplifications.md")
        return names

    def _snapshot_included(
        self,
        name: str,
        explicit_inputs: set[str],
        canonical_names: set[str] | None = None,
    ) -> bool:
        if name in explicit_inputs:
            return True
        run_prefix = f".specify/delivery/{self.run}/"
        if name.startswith(run_prefix):
            relative = name[len(run_prefix):]
            # These are project-owned requirements/planning inputs even when
            # artifact policy keeps them local. Runtime/, reviews/, receipts,
            # evidence, PR bodies, and task/slice ledgers remain bookkeeping.
            return relative in (canonical_names or CANONICAL_RUN_INPUT_NAMES)
        return not name.startswith((".specify/delivery/", ".specify/workflows/runs/"))

    def snapshot(
        self,
        state: dict[str, Any] | None = None,
        simplify_noop: bool | None = None,
    ) -> dict[str, Any]:
        state = state or self.load()
        canonical_names = self._canonical_run_inputs(state, simplify_noop)
        names = self._repository_names(self.root)
        index_entries = self._index_entries(self.root)
        names.update(entry["path"] for entry in index_entries)
        names.update(value for key, value in state["bindings"].items() if key != "inputs")
        names.update(state["bindings"].get("inputs", []))
        names.update((
            ".specify/memory/constitution.md", ".specify/extensions/delivery/delivery-config.yml",
            ".specify/extensions/quality/quality-config.yml",
        ))
        names.update(
            f".specify/delivery/{self.run}/{name}"
            for name in canonical_names
            if (self.directory / name).is_file()
        )
        explicit_inputs = {value for key, value in state["bindings"].items() if key != "inputs"} | set(state["bindings"].get("inputs", []))
        index_entries = [entry for entry in index_entries if self._snapshot_included(entry["path"], explicit_inputs, canonical_names)]
        files: dict[str, str] = {}
        worktree: dict[str, Any] = {}
        submodules: dict[str, Any] = {}
        modes = {entry["path"]: entry["mode"] for entry in index_entries if entry["stage"] == 0}
        for name in sorted(names):
            if not self._snapshot_included(name, explicit_inputs, canonical_names):
                # Delivery and Spec Kit workflow ledgers are coordinator
                # bookkeeping, except for an explicitly bound ignored input.
                continue
            path = self.inside(name)
            if modes.get(name) == "160000":
                nested = self._submodule_snapshot(path)
                submodules[name] = nested
                worktree[name] = {"kind": "submodule", "mode": self._worktree_entry(path).get("mode", 0), "sha256": nested["fingerprint"]}
                files[name] = nested["fingerprint"]
            elif path.is_dir() and not path.is_symlink():
                manifest = self._directory_manifest(path)
                worktree[name] = {"kind": "directory", "mode": self._worktree_entry(path).get("mode", 0), "sha256": digest(encoded(manifest))}
                files[name] = worktree[name]["sha256"]
            else:
                item = self._worktree_entry(path)
                if item.get("kind") == "file":
                    item = {**item, "sha256": digest(self._snapshot_bytes(name, path))}
                worktree[name] = item
                files[name] = item.get("sha256", "missing") if item.get("kind") == "file" else digest(encoded(item)) if item.get("kind") != "missing" else "missing"
        value: dict[str, Any] = {
            "head": self.git("rev-parse", "HEAD").decode().strip(),
            "files": files,
            "worktree": worktree,
            "index": index_entries,
            "submodules": submodules,
        }
        value["fingerprint"] = digest(encoded({**value, "run": self.run, "lane": state["lane"]}))
        return value

    def bound_file(self, state: dict[str, Any], name: str) -> Path:
        value = state["bindings"].get(name)
        if not isinstance(value, str) or not self.inside(value).is_file():
            raise ProtocolError(f"Bind this run's actual {name} file before continuing.")
        return self.inside(value)

    def _snapshot_path_value(self, snapshot: dict[str, Any], path: str) -> Any:
        index = [entry for entry in snapshot.get("index", []) if isinstance(entry, dict) and entry.get("path") == path]
        return {
            "file": snapshot.get("files", {}).get(path),
            "worktree": snapshot.get("worktree", {}).get(path),
            "index": index,
            "submodule": snapshot.get("submodules", {}).get(path),
        }

    def _changed_snapshot_paths(self, before: dict[str, Any], after: dict[str, Any]) -> set[str]:
        names = set(before.get("files", {})) | set(after.get("files", {}))
        names |= set(before.get("worktree", {})) | set(after.get("worktree", {}))
        names |= {entry.get("path") for entry in before.get("index", []) if isinstance(entry, dict)}
        names |= {entry.get("path") for entry in after.get("index", []) if isinstance(entry, dict)}
        names |= set(before.get("submodules", {})) | set(after.get("submodules", {}))
        return {name for name in names if isinstance(name, str) and self._snapshot_path_value(before, name) != self._snapshot_path_value(after, name)}

    def _checklist_only_checkbox_changes(self, before: bytes, after: bytes) -> bool:
        try:
            old_lines = before.decode("utf-8").splitlines(keepends=True)
            new_lines = after.decode("utf-8").splitlines(keepends=True)
        except UnicodeDecodeError:
            return False
        if len(old_lines) != len(new_lines):
            return False
        changed = False
        for old, new in zip(old_lines, new_lines):
            if old == new:
                continue
            old_match = CHECKBOX.fullmatch(old)
            new_match = CHECKBOX.fullmatch(new)
            if not old_match or not new_match:
                return False
            if old_match.group("prefix") != new_match.group("prefix") or old_match.group("suffix") != new_match.group("suffix") or old_match.group("newline") != new_match.group("newline"):
                return False
            changed = changed or old_match.group("mark") != new_match.group("mark")
        return changed

    def _resume_allowed(self, state: dict[str, Any], stage: str, pending: dict[str, Any], snapshot: dict[str, Any]) -> bool:
        before = pending["snapshot"]
        changed = self._changed_snapshot_paths(before, snapshot)
        if not changed:
            return True
        if stage == "converge":
            tasks = self.bound_file(state, "tasks")
            try:
                original = base64.b64decode(pending["tasks_before_b64"], validate=True)
            except (KeyError, TypeError, ValueError):
                return False
            return changed <= {self.relative(tasks)} and tasks.read_bytes().startswith(original)
        if stage == "clarify":
            spec = self.relative(self.bound_file(state, "spec"))
            checklist_value = state["bindings"].get("clarification_checklist")
            allowed = {spec}
            if isinstance(checklist_value, str):
                allowed.add(checklist_value)
            if not changed <= allowed:
                return False
            if checklist_value in changed:
                path = self.inside(checklist_value)
                old_entry = before.get("worktree", {}).get(checklist_value, {})
                # A checklist mutation is permitted only when both byte
                # versions are available; mode/index changes remain blocked.
                if old_entry.get("kind") != "file" or self._worktree_entry(path).get("kind") != "file":
                    return False
                old_path = self.inside(checklist_value)
                # The old bytes are not stored in the snapshot, so use the
                # pending input's exact supplemental bytes when available.
                old_bytes = pending.get("checklist_before_b64")
                if not isinstance(old_bytes, str):
                    return False
                try:
                    original = base64.b64decode(old_bytes, validate=True)
                except (ValueError, TypeError):
                    return False
                if not self._checklist_only_checkbox_changes(original, old_path.read_bytes()):
                    return False
            return True
        return False

    def begin(self, stage: str, resume: bool = False, scope: str = "outgoing-diff", operation_id: str | None = None) -> dict[str, Any]:
        state = self.load()
        if stage not in VERDICTS:
            raise ProtocolError("Unknown owner stage.")
        safe_id(scope)
        request = self._operation_request("begin", {"stage": stage, "resume": bool(resume), "scope": scope})
        replay = self._operation_replay(state, operation_id, "begin", request)
        if replay is not None:
            return replay
        snapshot = self.snapshot(state)
        if stage in state["pending"]:
            pending = state["pending"][stage]
            if pending.get("scope") != scope or (not resume and pending.get("operation_id") != operation_id):
                raise ProtocolError(f"Unfinished {stage} input exists. Inspect status and resume the original ticket with the same occurrence key.")
            if not self._resume_allowed(state, stage, pending, snapshot):
                raise ProtocolError(f"Unfinished {stage} input changed outside its permitted mutation boundary; recover the original ticket instead of replacing it.")
            if operation_id is not None:
                self._operation_store(state, operation_id, "begin", request, pending)
                self.save(state)
            return pending
        if state["lane"] == "feature":
            required = ("spec",) if stage == "clarify" else ("spec", "plan", "tasks")
            for name in required:
                self.bound_file(state, name)
        if state["lane"] == "bugfix":
            self.bound_file(state, "assessment")
        pending = {
            "schema_version": SCHEMA, "delivery_run": self.run, "lane": state["lane"],
            "stage": stage, "scope": scope, "ticket": uuid.uuid4().hex,
            "input_fingerprint": snapshot["fingerprint"], "snapshot": snapshot,
        }
        if operation_id is not None:
            pending["operation_id"] = self._operation_id(operation_id)
        if stage == "converge":
            tasks_before = self.bound_file(state, "tasks").read_bytes()
            pending["tasks_before_b64"] = base64.b64encode(tasks_before).decode("ascii")
            pending["tasks_before_sha256"] = digest(tasks_before)
        if stage == "clarify" and isinstance(state["bindings"].get("clarification_checklist"), str):
            checklist = self.inside(state["bindings"]["clarification_checklist"])
            if checklist.is_file():
                pending["checklist_before_b64"] = base64.b64encode(checklist.read_bytes()).decode("ascii")
        state["pending"][stage] = pending
        atomic_json(self.local / f"input-{stage}.json", pending)
        self._operation_store(state, operation_id, "begin", request, pending)
        self.save(state)
        return pending

    def reference(self, reference: Any) -> Path:
        if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
            raise ProtocolError("Evidence needs an exact {path,sha256} reference to original bytes.")
        if not isinstance(reference["path"], str) or not isinstance(reference["sha256"], str):
            raise ProtocolError("Malformed evidence reference.")
        path = self.inside(reference["path"])
        if not path.is_relative_to(self.directory) or not path.is_file() or path.is_symlink():
            raise ProtocolError("Report/evidence must be an existing regular non-symlink file inside this canonical run.")
        if not HASH.fullmatch(reference["sha256"]) or digest(path.read_bytes()) != reference["sha256"]:
            raise ProtocolError("Original report/evidence bytes changed; refresh the owner result instead of restamping it.")
        return path

    def references_current(self, value: Any) -> bool:
        if isinstance(value, dict):
            if set(value) == {"path", "sha256"}:
                self.reference(value)
            else:
                for child in value.values():
                    self.references_current(child)
        elif isinstance(value, list):
            for child in value:
                self.references_current(child)
        return True

    def _evidence_references(self, value: Any) -> list[dict[str, str]]:
        found: list[dict[str, str]] = []
        if isinstance(value, dict):
            if set(value) == {"path", "sha256"}:
                found.append({"path": value["path"], "sha256": value["sha256"]})
            else:
                for child in value.values():
                    found.extend(self._evidence_references(child))
        elif isinstance(value, list):
            for child in value:
                found.extend(self._evidence_references(child))
        return found

    def _explicit_report_verdict(self, path: Path, stage: str) -> str | None:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return None
        names = {
            "quality": "QUALITY_VERDICT", "standards": "STANDARDS_VERDICT", "review": "REVIEW_VERDICT",
            "analyze": "ANALYZE_VERDICT", "converge": "CONVERGE_VERDICT", "clarify": "CLARIFY_VERDICT",
            "simplify": "SIMPLIFY_SCAN", "simplify-verify": "SIMPLIFY_VERIFY",
            "checkpoint": "CHECKPOINT_VERDICT",
        }
        markers = {names[stage], "NATIVE_VERDICT"}
        if stage == "checkpoint":
            markers.add("SD_CORE_HANDOFF")
        values: list[str] = []
        for line in text.splitlines():
            match = re.match(r"^\s*([A-Z][A-Z0-9_-]*)\s*:\s*([A-Za-z][A-Za-z0-9_-]*)\s*$", line)
            if match and match[1] in markers:
                value = match[2].lower()
                if stage == "checkpoint" and match[1] == "SD_CORE_HANDOFF":
                    value = "pass" if value == "pass" else "blocked" if value == "blocked" else value
                values.append(value)
        if not values:
            # SD Core's native handoff is the one legacy machine header whose
            # name is not stage-specific; it remains an exact header, not prose parsing.
            for line in text.splitlines():
                match = re.match(r"^\s*SD_CORE_HANDOFF\s*:\s*(PASS|BLOCKED)\s*$", line, re.IGNORECASE)
                if match:
                    values.append(match[1].lower())
        if not values:
            return None
        if len(set(values)) != 1:
            raise ProtocolError("Native report contains conflicting explicit verdict headers.")
        return values[0]

    def _validate_native_receipt(
        self,
        state: dict[str, Any],
        stage: str,
        result: dict[str, Any],
        expected_head: str,
    ) -> None:
        receipt_ref = result.get("native_receipt")
        receipt_path = self.reference(receipt_ref)
        if receipt_path == self.inside(result["report"]["path"]):
            raise ProtocolError("A native owner receipt cannot be the report it claims to bind.")
        receipt = read_json(receipt_path)
        if set(receipt) != NATIVE_RECEIPT_KEYS or receipt.get("schema_version") != NATIVE_RECEIPT_SCHEMA or receipt.get("receipt_type") != "delivery-native-owner":
            raise ProtocolError("Native owner receipt must use the exact delivery-native-owner JSON schema.")
        for key in ("delivery_run", "lane", "stage", "scope", "ticket", "input_fingerprint", "verdict"):
            if receipt.get(key) != result.get(key):
                raise ProtocolError(f"Native owner receipt {key} does not match the normalized result envelope.")
        if not isinstance(receipt.get("head"), str) or not GIT_OBJECT.fullmatch(receipt["head"]) or receipt["head"] != expected_head:
            raise ProtocolError("Native owner receipt HEAD does not match the exact owner input/output identity.")
        if not HASH.fullmatch(receipt.get("input_fingerprint", "")):
            raise ProtocolError("Native owner receipt input fingerprint is malformed.")
        if receipt.get("report") != result.get("report") or receipt.get("data") != result.get("data"):
            raise ProtocolError("Native owner receipt does not bind the exact report and normalized owner outcome.")
        evidence = receipt.get("evidence")
        expected_evidence = self._evidence_references(result.get("data"))
        if evidence != expected_evidence:
            raise ProtocolError("Native owner receipt evidence list does not match the result's exact evidence references.")
        self.references_current(receipt)
        explicit = self._explicit_report_verdict(self.inside(result["report"]["path"]), stage)
        if explicit is not None and explicit != result["verdict"]:
            raise ProtocolError("Native report's explicit machine verdict conflicts with the receipt; a blocked report cannot be upgraded to pass.")

    def _validate_result_shape(
        self,
        state: dict[str, Any],
        stage: str,
        result: dict[str, Any],
        *,
        stored: bool,
        dynamic: bool,
    ) -> None:
        required = RESULT_INPUT_KEYS | ({"output_fingerprint", "input_snapshot", "output_snapshot"} if stored else set())
        if not isinstance(result, dict) or not required.issubset(result):
            raise ProtocolError(f"Completed {stage} result is incomplete; recover the original owner receipt.")
        if result.get("schema_version") != SCHEMA or result.get("delivery_run") != self.run or result.get("lane") != state["lane"] or result.get("stage") != stage:
            raise ProtocolError(f"Completed {stage} result belongs to another run or lane.")
        if not isinstance(result.get("scope"), str):
            raise ProtocolError(f"Completed {stage} result has no stable scope.")
        safe_id(result["scope"])
        if not isinstance(result.get("ticket"), str) or not result["ticket"] or not isinstance(result.get("input_fingerprint"), str) or not HASH.fullmatch(result["input_fingerprint"]):
            raise ProtocolError(f"Completed {stage} result has a malformed ticket or input fingerprint.")
        if result.get("verdict") not in VERDICTS[stage] or not isinstance(result.get("data"), dict):
            raise ProtocolError(f"Malformed {stage} verdict/data; a null or partial stored result cannot be reused.")
        self.reference(result.get("report"))
        if stored:
            self._validate_snapshot_shape(result["input_snapshot"])
            self._validate_snapshot_shape(result["output_snapshot"])
            if result["input_snapshot"]["fingerprint"] != result["input_fingerprint"] or result["output_snapshot"]["fingerprint"] != result["output_fingerprint"]:
                raise ProtocolError(f"Stored {stage} result snapshot fingerprints are inconsistent.")
            expected_head = result["output_snapshot"]["head"] if stage == "checkpoint" else result["input_snapshot"]["head"]
            pending = {
                "snapshot": result["input_snapshot"],
                "tasks_before_b64": result.get("tasks_before_b64"),
                "tasks_before_sha256": result.get("tasks_before_sha256"),
            }
        else:
            pending = state["pending"].get(stage)
            if not pending:
                raise ProtocolError(f"No pending {stage} input exists for this result.")
            expected_head = self.snapshot(state)["head"] if stage == "checkpoint" and dynamic else pending["snapshot"]["head"]
        self._validate_native_receipt(state, stage, result, expected_head)
        if stage == "checkpoint" and stored:
            manifest_ref = result.get("planning_manifest")
            if not isinstance(manifest_ref, dict):
                raise ProtocolError("Stored planning checkpoint has no immutable planning manifest reference.")
            manifest_path = self.reference(manifest_ref)
            if not manifest_path.is_relative_to(self.local):
                raise ProtocolError("Stored planning manifest must remain under this run's runtime directory.")
            pending["planning_manifest_path"] = self.relative(manifest_path)
            self._planning_manifest(state, manifest_ref)
            if result.get("verdict") == "pass":
                self._validate_checkpoint_association(result.get("checkpoint_association"), state)
        self.validate_data(state, stage, result, pending, dynamic=dynamic, structural_only=not dynamic)
        self.references_current(result)

    def _dependency_receipt(self, result: dict[str, Any]) -> dict[str, Any]:
        return {
            "stage": result["stage"], "ticket": result["ticket"],
            "input_fingerprint": result["input_fingerprint"], "verdict": result["verdict"],
            "report": result["report"], "native_receipt": result["native_receipt"],
        }

    def _review_dependencies_current(self, state: dict[str, Any], data: dict[str, Any]) -> bool:
        dependencies = data.get("dependencies")
        if not isinstance(dependencies, dict):
            return False
        for stage in ("quality", "standards"):
            owner = state["stages"].get(stage)
            if not isinstance(owner, dict) or owner.get("verdict") != "pass" or dependencies.get(stage) != self._dependency_receipt(owner):
                return False
            if not self.current(state, stage, "pass"):
                return False
        return True

    def _git_changed_paths(self, base: str, head: str) -> set[str] | None:
        if base == head:
            return set()
        try:
            self.git("merge-base", "--is-ancestor", base, head)
            return {
                os.fsdecode(item).replace("\\", "/")
                for item in self.git("diff", "--name-only", "-z", base, head).split(b"\0")
                if item
            }
        except ProtocolError:
            return None

    def _analyze_current_via_checkpoint(self, state: dict[str, Any], analyze: dict[str, Any], current_snapshot: dict[str, Any]) -> bool:
        if "analyze" in state.get("pending", {}):
            return False
        if analyze.get("output_snapshot", {}).get("files") != current_snapshot.get("files"):
            return False
        history = state.get("checkpoint_history", [])
        matches = [
            association for association in history
            if association.get("analyze_ticket") == analyze.get("ticket")
            and association.get("analyze_output_fingerprint") == analyze.get("output_fingerprint")
        ]
        checkpoint = state.get("stages", {}).get("checkpoint")
        if not isinstance(checkpoint, dict) or checkpoint.get("verdict") != "pass" or not matches:
            return False
        latest = checkpoint.get("checkpoint_association")
        if not isinstance(latest, dict) or latest not in matches:
            return False
        try:
            self._validate_result_shape(state, "checkpoint", checkpoint, stored=True, dynamic=False)
            if self.git("branch", "--show-current").decode().strip() != checkpoint.get("data", {}).get("branch"):
                return False
            self.references_current(analyze)
            self.references_current(checkpoint)
            if current_snapshot["head"] != matches[-1]["new_head"]:
                return False
            first = matches[0]
            approved: set[str] = set()
            for association in matches:
                self._validate_checkpoint_association(association, state)
                approved.update(association["approved_paths"])
                if self._git_changed_paths(association["prior_head"], association["new_head"]) is None:
                    return False
            changed = self._git_changed_paths(first["prior_head"], current_snapshot["head"])
            return changed is not None and changed <= approved
        except (ProtocolError, OSError):
            return False

    def current(self, state: dict[str, Any], stage: str, verdict: str | None = None) -> bool:
        # A fresh owner ticket is an unfinished occurrence. An older pass may
        # remain in state for recovery/audit, but it cannot satisfy a gate while
        # that ticket is still pending.
        if stage in state.get("pending", {}):
            return False
        result = state.get("stages", {}).get(stage)
        if not isinstance(result, dict) or (verdict and result.get("verdict") != verdict):
            return False
        try:
            self._validate_result_shape(state, stage, result, stored=True, dynamic=stage in {"review", "converge"})
            current_snapshot = self.snapshot(state)
            if result.get("output_fingerprint") != current_snapshot["fingerprint"]:
                if not (stage == "analyze" and result.get("verdict") == "pass" and self._analyze_current_via_checkpoint(state, result, current_snapshot)):
                    return False
            if stage == "review" and result.get("verdict") == "pass" and not self._review_dependencies_current(state, result["data"]):
                return False
            if stage == "checkpoint" and result.get("verdict") == "pass":
                if self.git("branch", "--show-current").decode().strip() != result.get("data", {}).get("branch"):
                    return False
                analyze = state.get("stages", {}).get("analyze")
                if not isinstance(analyze, dict) or not self._analyze_current_via_checkpoint(state, analyze, current_snapshot):
                    return False
            self.references_current(result)
        except (ProtocolError, OSError):
            # A stale/tampered native report is not a current pass. The caller's
            # require/needs operation still blocks or requests a fresh result.
            return False
        return True

    def _checkpoint_manifest_path(self, pending: dict[str, Any], explicit: str | None = None) -> Path:
        if explicit is not None:
            path = self.inside(explicit)
        else:
            path = self.local / f"planning-inputs-{pending['ticket']}.json"
            if not path.exists():
                # Compatibility for already-installed fixtures/runs. New
                # checkpoints prefer the immutable ticket-specific filename.
                path = self.local / "planning-inputs.json"
        if not path.is_relative_to(self.local) or not path.is_file() or path.is_symlink():
            raise ProtocolError("Planning checkpoint needs one exact regular non-symlink manifest under its runtime directory.")
        return path

    def _planning_manifest(
        self,
        state: dict[str, Any],
        expected: dict[str, str] | None = None,
        manifest_path: str | None = None,
    ) -> dict[str, Any]:
        if expected is not None:
            if not isinstance(expected, dict) or set(expected) != {"path", "sha256"}:
                raise ProtocolError("Planning checkpoint manifest reference is malformed.")
            path = self.inside(expected["path"])
        elif manifest_path is not None:
            path = self.inside(manifest_path)
        else:
            path = self.local / "planning-inputs.json"
        if not path.is_relative_to(self.local) or not path.is_file() or path.is_symlink():
            raise ProtocolError("Planning checkpoint needs one exact regular non-symlink manifest under its runtime directory.")
        if expected is not None:
            if expected.get("path") != self.relative(path) or not HASH.fullmatch(expected.get("sha256", "")) or digest(path.read_bytes()) != expected["sha256"]:
                raise ProtocolError("Planning input manifest changed after the checkpoint; renew the native planning authorization.")
        manifest = read_json(path)
        if manifest.get("schema_version") != 1 or manifest.get("delivery_run") != self.run or manifest.get("lane") != state["lane"]:
            raise ProtocolError("Planning input manifest identity is missing or belongs to another run/lane.")
        authorization = manifest.get("authorization")
        if isinstance(authorization, str):
            if not authorization.strip():
                raise ProtocolError("Planning input manifest authorization is empty.")
        elif isinstance(authorization, dict):
            if not isinstance(authorization.get("statement"), str) or not authorization["statement"].strip():
                raise ProtocolError("Planning input manifest authorization needs a statement.")
            if "evidence" in authorization:
                self.reference(authorization["evidence"])
        else:
            raise ProtocolError("Planning input manifest needs an explicit authorization statement or evidence object.")
        paths = manifest.get("paths")
        if not isinstance(paths, list) or not paths:
            raise ProtocolError("Planning input manifest needs a nonempty exact path list.")
        normalized: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in paths:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("source_owner"), str):
                raise ProtocolError("Planning input manifest entries need exact path and source_owner fields.")
            path_value = item["path"]
            path_obj = self.inside(path_value)
            if self.relative(path_obj) != path_value or "*" in path_value or not path_obj.is_file() or path_obj.is_symlink() or path_value in seen:
                raise ProtocolError("Planning input manifest paths must be existing normalized non-symlink files without globs.")
            owner = item["source_owner"].strip().lower()
            if owner not in {"core", "decision", "adr"}:
                raise ProtocolError("Planning input manifest source_owner must be core or decision/adr.")
            normalized.append({"path": path_value, "source_owner": owner})
            seen.add(path_value)
        manifest["paths"] = normalized
        return manifest

    def _config_list(self, text: str, key: str) -> list[str]:
        lines = text.splitlines()
        matches: list[tuple[int, int, str]] = []
        for index, raw_line in enumerate(lines):
            content = raw_line.split("#", 1)[0].rstrip()
            match = re.match(rf"^(?P<indent>\s*){re.escape(key)}\s*:\s*(?P<value>.*)$", content)
            if match:
                matches.append((index, len(match["indent"]), match["value"].strip()))
        if len(matches) > 1:
            raise ProtocolError(f"Duplicate Decision configuration key {key}; recover the project policy.")
        if not matches:
            return []
        index, indent, value = matches[0]
        if value:
            if not (value.startswith("[") and value.endswith("]")):
                raise ProtocolError(f"Decision configuration {key} must use an indented list or a simple inline list.")
            value = value[1:-1].strip()
            if not value:
                return []
            values = [part.strip() for part in value.split(",")]
        else:
            values = []
            for raw_line in lines[index + 1:]:
                content = raw_line.split("#", 1)[0].rstrip()
                if not content.strip():
                    continue
                current_indent = len(content) - len(content.lstrip())
                if current_indent <= indent:
                    break
                list_item = re.match(r"^\s*-\s*(.*?)\s*$", content)
                if not list_item:
                    raise ProtocolError(f"Decision configuration {key} contains an unsupported nested representation.")
                values.append(list_item[1].strip())
            if not values:
                raise ProtocolError(f"Decision configuration {key} needs at least one list item.")
        normalized: list[str] = []
        for value in values:
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            if not value or any(character in value for character in "[]{}"):
                raise ProtocolError(f"Decision configuration {key} contains an unsupported list value.")
            normalized.append(value)
        return normalized

    def _adr_policy(self) -> tuple[list[Path], set[str]]:
        config = self.inside(".specify/extensions/decision/decision-config.yml")
        if not config.is_file():
            return [self.inside(".specify/decisions")], {"proposed"}
        try:
            text = config.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ProtocolError(f"Cannot read Decision configuration; fix it before checkpointing: {exc}") from exc
        directories = self._config_list(text, "adr_directories")
        if not directories:
            raise ProtocolError("Decision configuration must declare adr_directories before an ADR can enter a planning manifest.")
        paths: list[Path] = []
        for value in directories:
            path = self.inside(value)
            if self.relative(path) != value or path in paths:
                raise ProtocolError("Decision adr_directories must be unique normalized project-relative directories.")
            paths.append(path)
        proposed = {value.strip().lower() for value in self._config_list(text, "proposed_statuses")}
        if not proposed:
            raise ProtocolError("Decision proposed_statuses must contain at least one status.")
        return paths, proposed

    def _planning_path_allowed(self, state: dict[str, Any], item: str, owner: str, require_proposed: bool = True) -> bool:
        path = self.inside(item)
        if owner == "core":
            bound = {state["bindings"].get(name) for name in ("spec", "plan", "tasks")}
            if item in bound:
                return True
            spec = state["bindings"].get("spec")
            if not isinstance(spec, str):
                return False
            feature_root = self.inside(spec).parent
            if path.is_relative_to(feature_root):
                relative = path.relative_to(feature_root).as_posix()
                if relative in PLANNING_OUTPUT_NAMES or relative == "checklists/requirements.md":
                    return True
                if relative.startswith("contracts/") and relative != "contracts/":
                    return True
            if path.is_relative_to(self.directory) and not path.is_relative_to(self.local):
                return len(path.relative_to(self.directory).parts) == 1 and path.name in PLANNING_RUN_NAMES
            return False
        if owner in {"decision", "adr"}:
            directories, proposed_statuses = self._adr_policy()
            if not any(path.parent == directory for directory in directories):
                return False
            if not require_proposed:
                return True
            header = fields(path)
            status = header.get("adr_status", header.get("status", "")).strip().lower()
            return status in proposed_statuses
        return False

    def validate_data(
        self,
        state: dict[str, Any],
        stage: str,
        result: dict[str, Any],
        pending: dict[str, Any],
        *,
        dynamic: bool = True,
        structural_only: bool = False,
    ) -> None:
        data = result.get("data")
        verdict = result.get("verdict")
        if not isinstance(data, dict) or verdict not in VERDICTS[stage]:
            raise ProtocolError(f"Malformed {stage} verdict/data.")
        if stage == "quality":
            checks = data.get("checks")
            if not isinstance(checks, list):
                raise ProtocolError("Quality needs original per-check execution evidence.")
            if not checks and (verdict != "pass" or data.get("applicability") != "not-applicable" or not isinstance(data.get("reason"), str) or not data["reason"].strip()):
                raise ProtocolError("Quality needs original per-check evidence or an explicit policy-backed not-applicable pass.")
            for check in checks:
                if not isinstance(check, dict) or not isinstance(check.get("command"), str) or not check["command"].strip():
                    raise ProtocolError("Quality check command is missing.")
                if type(check.get("exit_code")) is not int:
                    raise ProtocolError("Quality exit codes must be integers.")
                self.reference(check.get("evidence"))
                if verdict == "pass" and check["exit_code"] != 0:
                    raise ProtocolError("A failing mechanical check cannot produce Quality pass.")
        if stage in {"standards", "analyze", "review"}:
            if data.get("coverage") not in {"complete", "incomplete"}:
                raise ProtocolError("Record complete/incomplete coverage explicitly.")
            if verdict == "pass" and data["coverage"] != "complete":
                raise ProtocolError("Incomplete coverage cannot pass.")
        if stage == "review":
            dimensions = data.get("dimensions")
            if not isinstance(dimensions, dict) or set(dimensions) != DIMENSIONS:
                raise ProtocolError("Review must account for all six dimensions.")
            if any(value not in {"pass", "blocked", "incomplete"} for value in dimensions.values()):
                raise ProtocolError("Invalid per-dimension verdict.")
            findings = data.get("findings")
            if not isinstance(findings, list) or type(data.get("repairable")) is not bool:
                raise ProtocolError("Review needs finding states and an explicit repairable flag.")
            known: dict[str, dict[str, Any]] = {}
            for finding in findings:
                if not isinstance(finding, dict) or not isinstance(finding.get("id"), str) or not finding["id"]:
                    raise ProtocolError("Every finding needs a stable id.")
                if finding["id"] in known or finding.get("status") not in {"open", "fixed-pending-review", "resolved", "dismissed"}:
                    raise ProtocolError("Duplicate finding or invalid finding lifecycle.")
                if type(finding.get("blocking")) is not bool:
                    raise ProtocolError("Finding blocking must be a boolean.")
                if finding["status"] in {"resolved", "dismissed"}:
                    self.reference(finding.get("evidence"))
                elif "evidence" in finding:
                    self.reference(finding["evidence"])
                known[finding["id"]] = finding
            previous_result = state.get("outgoing_review") if result.get("scope") == "outgoing-diff" else None
            if previous_result is None:
                previous_result = state["stages"].get("review")
            if previous_result is result or (isinstance(previous_result, dict) and (previous_result.get("ticket") == result.get("ticket") or previous_result.get("scope") != result.get("scope"))):
                previous_result = None
            previous = previous_result.get("data", {}).get("findings", []) if isinstance(previous_result, dict) else []
            for item in previous:
                if item.get("status") not in {"open", "fixed-pending-review"}:
                    continue
                current = known.get(item.get("id"))
                if current is None:
                    raise ProtocolError("An earlier unresolved finding disappeared; account for its disposition explicitly.")
                if item.get("blocking") is True and current.get("status") in {"open", "fixed-pending-review"} and current.get("blocking") is not True:
                    raise ProtocolError("A prior blocking finding cannot become nonblocking while open; record evidenced resolution or dismissal.")
            independence = data.get("independence")
            if independence not in {"independent", "accepted-self-review", "self-review"}:
                raise ProtocolError("Record actual review independence.")
            if independence == "accepted-self-review":
                self.reference(data.get("acceptance"))
            if verdict == "pass":
                if independence == "self-review" or any(value != "pass" for value in dimensions.values()):
                    raise ProtocolError("Review cannot pass with an unaccepted self-review or failing dimension.")
                if any(item["blocking"] and item["status"] in {"open", "fixed-pending-review"} for item in findings):
                    raise ProtocolError("Unresolved blockers prevent Review pass.")
                dependencies = data.get("dependencies")
                dependency_keys = {"stage", "ticket", "input_fingerprint", "verdict", "report", "native_receipt"}
                if not isinstance(dependencies, dict) or set(dependencies) != {"quality", "standards"}:
                    raise ProtocolError("Review pass needs exact Quality and Standards dependency receipts.")
                for stage_name in ("quality", "standards"):
                    dependency = dependencies[stage_name]
                    if not isinstance(dependency, dict) or set(dependency) != dependency_keys or dependency.get("stage") != stage_name or dependency.get("verdict") != "pass":
                        raise ProtocolError("Review pass dependency receipt shape is malformed.")
                    if not isinstance(dependency.get("ticket"), str) or not HASH.fullmatch(dependency.get("input_fingerprint", "")):
                        raise ProtocolError("Review pass dependency receipt identity is malformed.")
                    self.reference(dependency["report"])
                    self.reference(dependency["native_receipt"])
                    # A persisted old Review may become stale when Quality or
                    # Standards is refreshed. Loading it must remain possible
                    # so the pending owner can be recovered; only a new record
                    # or a current/require check demands exact equality.
                    if not structural_only:
                        owner = state["stages"].get(stage_name)
                        if not isinstance(owner, dict) or owner.get("verdict") != "pass" or dependency != self._dependency_receipt(owner):
                            raise ProtocolError("Review pass dependency receipt is not the exact current owner result.")
                        if dynamic and not self.current(state, stage_name, "pass"):
                            raise ProtocolError("Review pass needs current Quality and Standards owner evidence.")
        if stage == "converge":
            try:
                before = base64.b64decode(pending["tasks_before_b64"], validate=True)
            except (KeyError, ValueError, TypeError) as exc:
                raise ProtocolError("Convergence input has no valid byte-exact queue snapshot; begin it again.") from exc
            if digest(before) != pending.get("tasks_before_sha256"):
                raise ProtocolError("Convergence input queue fingerprint is corrupt; recover the original ticket.")
            appended = data.get("appended_tasks")
            if not isinstance(appended, list) or any(not isinstance(item, str) or not item for item in appended) or len(appended) != len(set(appended)):
                raise ProtocolError("Convergence needs a unique exact appended Task ID list.")
            if dynamic:
                tasks_path = self.bound_file(state, "tasks")
                current_bytes = tasks_path.read_bytes()
                if not current_bytes.startswith(before):
                    raise ProtocolError("Converge may append tasks, never rewrite earlier queue contents.")
                try:
                    before_text = before.decode("utf-8")
                    appended_text = current_bytes[len(before):].decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise ProtocolError("tasks.md must remain valid UTF-8 for append-only TaskID validation.") from exc
                old_ids = {match[1] for match in TASK.findall(before_text)}
                appended_matches = TASK.findall(appended_text)
                actual = [match[1] for match in appended_matches]
                if len(actual) != len(set(actual)) or old_ids.intersection(actual) or data.get("appended_tasks") != actual:
                    raise ProtocolError("Convergence result does not match the actual appended Task IDs.")
                if verdict == "tasks-appended" and (not actual or any(mark != " " for mark, _ in appended_matches)):
                    raise ProtocolError("tasks-appended may append only new unchecked Task IDs; Ralph must own their completion.")
                if verdict == "converged":
                    if current_bytes != before:
                        raise ProtocolError("Converged must leave tasks.md byte-equivalent.")
                    if any(mark == " " for mark, _ in TASK.findall(before_text)):
                        raise ProtocolError("Converged requires zero unchecked bound Tasks; run Ralph before convergence can close.")
                    self.audit_task_closure(state)
        if stage == "clarify" and type(data.get("needs_approval")) is not bool:
            raise ProtocolError("Clarify must explicitly identify a real approval decision.")
        if stage == "simplify":
            candidates = data.get("candidates")
            if not isinstance(candidates, list) or any(not isinstance(item, str) or not item.strip() for item in candidates) or len(set(candidates)) != len(candidates):
                raise ProtocolError("Simplify needs a unique candidate ID array.")
            if (verdict == "none" and candidates) or (verdict == "candidates" and not candidates):
                raise ProtocolError("Simplification verdict and candidate list disagree.")
        if stage == "simplify-verify":
            accepted = self.accepted_candidates(state)
            if data.get("accepted_candidates") != accepted:
                raise ProtocolError("Simplify Verify must cover exactly the candidate IDs accepted by this run's gate.")
            if verdict == "not-applicable" and accepted:
                raise ProtocolError("Accepted simplifications need actual verification; not-applicable cannot close them.")
        if stage == "checkpoint":
            if state["lane"] != "feature":
                raise ProtocolError("Only the Feature lane uses a planning-to-execution checkpoint.")
            if data.get("planning_stage") not in {"initial", "converge", "simplify", "outgoing-repair"}:
                raise ProtocolError("Record the actual Core planning stage at the checkpoint.")
            approved = data.get("approved_paths")
            if not isinstance(approved, list) or not approved or any(not isinstance(item, str) for item in approved) or len(set(approved)) != len(approved):
                raise ProtocolError("Planning checkpoint needs an exact nonempty approved path list.")
            manifest = self._planning_manifest(
                state,
                manifest_path=pending.get("planning_manifest_path") if isinstance(pending, dict) else None,
            )
            manifest_entries = {entry["path"]: entry["source_owner"] for entry in manifest["paths"]}
            if any(item not in manifest_entries for item in approved):
                raise ProtocolError("Checkpoint approved_paths must be a subset of the exact native planning-input manifest.")
            for item in approved:
                path = self.inside(item)
                if self.relative(path) != item or "*" in item or not path.is_file() or path.is_symlink() or path.is_relative_to(self.local):
                    raise ProtocolError("Approved planning paths must be existing normalized non-symlink files outside runtime bookkeeping.")
                if not self._planning_path_allowed(state, item, manifest_entries[item], require_proposed=dynamic):
                    raise ProtocolError("Approved planning path is outside the actual Core output/explicit Proposed ADR allowlist.")
            branch = data.get("branch")
            base_head = data.get("base_head")
            if not isinstance(branch, str) or not branch.strip() or not isinstance(base_head, str) or not GIT_OBJECT.fullmatch(base_head):
                raise ProtocolError("Planning checkpoint branch/base identity is malformed.")
            if dynamic and (self.git("branch", "--show-current").decode().strip() != branch or base_head != pending["snapshot"]["head"]):
                raise ProtocolError("Planning checkpoint branch/base does not match the actual entry identity.")
            authorization = data.get("authorization")
            if isinstance(authorization, str):
                if not authorization.strip():
                    raise ProtocolError("Planning checkpoint authorization is empty.")
            elif isinstance(authorization, dict):
                if not isinstance(authorization.get("statement"), str) or not authorization["statement"].strip():
                    raise ProtocolError("Planning checkpoint authorization needs a statement.")
                if "evidence" in authorization:
                    self.reference(authorization["evidence"])
            else:
                raise ProtocolError("Planning checkpoint must cite the project's Git authorization or actual user decision.")
            if verdict == "pass" and not structural_only:
                dirty = self.execution_dirty_paths()
                if dirty:
                    raise ProtocolError("Planning checkpoint has a dirty execution entry; commit only authorized planning paths or recover:\n" + "\n".join(dirty))
                analyze = state["stages"].get("analyze", {})
                if analyze.get("verdict") != "pass" or analyze.get("output_fingerprint") != pending["snapshot"]["fingerprint"]:
                    raise ProtocolError("Planning checkpoint requires a current passing Analyze result for the exact entry snapshot.")
                if "analyze_fingerprint" in data and data["analyze_fingerprint"] != analyze.get("output_fingerprint"):
                    raise ProtocolError("Planning checkpoint Analyze association is not exact.")
                if "content_fingerprint" in data and data["content_fingerprint"] != pending["snapshot"]["fingerprint"]:
                    raise ProtocolError("Planning checkpoint content fingerprint is not the exact entry snapshot.")
                self.references_current(analyze)
                current_head = self.git("rev-parse", "HEAD").decode().strip()
                if current_head != pending["snapshot"]["head"]:
                    self.git("merge-base", "--is-ancestor", pending["snapshot"]["head"], current_head)
                    changed = {os.fsdecode(item).replace("\\", "/") for item in self.git("diff", "--name-only", "-z", pending["snapshot"]["head"], current_head).split(b"\0") if item}
                    if changed - set(approved):
                        raise ProtocolError("Planning commit included paths outside the explicit approved set: " + ", ".join(sorted(changed - set(approved))))

    def record(
        self,
        stage: str,
        file: str | None = None,
        operation_id: str | None = None,
        planning_manifest: str | None = None,
    ) -> dict[str, Any]:
        state = self.load()
        result_name = file or f".specify/delivery/{self.run}/runtime/result-{stage}.json"
        request = self._operation_request(
            "record",
            {"stage": stage, "file": result_name, "planning_manifest": planning_manifest},
        )
        replay = self._operation_replay(state, operation_id, "record", request)
        if replay is not None:
            return replay
        pending = state["pending"].get(stage)
        if not pending:
            raise ProtocolError(f"No pending {stage} input; begin the owner stage before recording it.")
        manifest_path: Path | None = None
        if stage == "checkpoint":
            manifest_path = self._checkpoint_manifest_path(pending, planning_manifest)
            pending["planning_manifest_path"] = self.relative(manifest_path)
        path = self.inside(file) if file else self.local / f"result-{stage}.json"
        if not path.is_relative_to(self.local) or path.is_symlink():
            raise ProtocolError("Normalized results must stay in this run's non-symlink runtime directory.")
        result = read_json(path)
        if set(result) != RESULT_INPUT_KEYS:
            raise ProtocolError("Normalized result must use the exact envelope keys including scope and native_receipt.")
        for key in ("schema_version", "delivery_run", "lane", "stage", "scope", "ticket", "input_fingerprint"):
            if result.get(key) != pending[key]:
                raise ProtocolError(f"Result {key} does not match the original pending input.")
        if self.inside(result["report"]["path"]) == path:
            raise ProtocolError("A normalized result cannot use itself as native evidence.")
        # A no-candidate Simplify report is operational bookkeeping. Exclude it
        # from this result's output snapshot so its own freshness check uses the
        # same canonical inputs as every later consumer.
        simplify_noop = (
            isinstance(result.get("data"), dict)
            and result["data"].get("candidates") == []
            if stage == "simplify"
            else None
        )
        now = self.snapshot(state, simplify_noop=simplify_noop)
        before = pending["snapshot"]
        if now["head"] != before["head"] and stage != "checkpoint":
            raise ProtocolError("Owner stage changed HEAD; recover and begin against the actual execution identity.")
        changed = self._changed_snapshot_paths(before, now)
        allowed: set[str] = set()
        if stage == "converge":
            allowed.add(state["bindings"].get("tasks"))
        if stage == "clarify":
            allowed.add(state["bindings"].get("spec"))
            checklist = state["bindings"].get("clarification_checklist")
            if isinstance(checklist, str):
                allowed.add(checklist)
                if checklist in changed:
                    old_bytes = pending.get("checklist_before_b64")
                    if not isinstance(old_bytes, str):
                        raise ProtocolError("Clarify changed its checklist without an exact bound preimage.")
                    try:
                        original = base64.b64decode(old_bytes, validate=True)
                    except (ValueError, TypeError) as exc:
                        raise ProtocolError("Clarify checklist preimage is malformed; recover the original ticket.") from exc
                    if not self._checklist_only_checkbox_changes(original, self.inside(checklist).read_bytes()):
                        raise ProtocolError("Clarify may change only checkbox marks in the exact bound checklists/requirements.md file.")
        if stage == "simplify":
            allowed.add(f".specify/delivery/{self.run}/simplifications.md")
        if stage == "checkpoint":
            approved = result.get("data", {}).get("approved_paths", []) if isinstance(result.get("data"), dict) else []
            allowed.update(approved if isinstance(approved, list) else [])
        if changed - allowed:
            raise ProtocolError("Owner result is stale or edited undeclared source/input paths: " + ", ".join(sorted(changed - allowed)))
        self._validate_result_shape(state, stage, result, stored=False, dynamic=True)
        self.references_current(result)
        stored = {
            **result,
            "input_snapshot": pending["snapshot"],
            "output_fingerprint": now["fingerprint"],
            "output_snapshot": now,
        }
        if stage == "checkpoint":
            if manifest_path is None:
                raise ProtocolError("Checkpoint record did not resolve its ticket-specific planning manifest.")
            manifest_ref = {"path": self.relative(manifest_path), "sha256": digest(manifest_path.read_bytes())}
            self.reference(manifest_ref)
            stored["planning_manifest"] = manifest_ref
            if result["verdict"] == "pass":
                analyze = state["stages"].get("analyze")
                approved = result["data"].get("approved_paths")
                if not isinstance(analyze, dict) or not isinstance(approved, list):
                    raise ProtocolError("Passing planning checkpoint needs the exact Analyze owner result and approved path set.")
                association = {
                    "checkpoint_ticket": result["ticket"],
                    "analyze_ticket": analyze["ticket"],
                    "analyze_output_fingerprint": analyze["output_fingerprint"],
                    "prior_head": pending["snapshot"]["head"],
                    "new_head": now["head"],
                    "approved_paths": list(approved),
                    "report": result["report"],
                    "native_receipt": result["native_receipt"],
                }
                self._validate_checkpoint_association(association, state)
                stored["checkpoint_association"] = association
                state.setdefault("checkpoint_history", []).append(association)
        if stage == "converge":
            stored["tasks_before_b64"] = pending.get("tasks_before_b64")
            stored["tasks_before_sha256"] = pending.get("tasks_before_sha256")
        if operation_id is not None:
            stored["operation_id"] = self._operation_id(operation_id)
        state["stages"][stage] = stored
        if stage == "review" and stored.get("scope") == "outgoing-diff":
            # Task reviews during a repair must not erase unresolved integrated
            # findings before the next outgoing-diff reviewer reconciles them.
            state["outgoing_review"] = stored
        del state["pending"][stage]
        state["phase"] = "verification" if stage in {"quality", "standards", "review"} else "planning"
        self._operation_store(state, operation_id, "record", request, stored)
        self.save(state)
        return stored

    def budget(self, state: dict[str, Any], kind: str, scope: str) -> dict[str, Any]:
        if kind not in {"review", "convergence"}:
            raise ProtocolError("Unknown bounded pass kind.")
        safe_id(scope)
        return state["attempts"].setdefault(f"{kind}:{scope}", {"used": 0, "pending": None})

    def reserve(self, kind: str, scope: str, resume: int | None = None, operation_id: str | None = None) -> dict[str, Any]:
        if isinstance(resume, bool):
            raise ProtocolError("Reserve recovery requires the explicit pending attempt number; bare --resume cannot select attempt 1.")
        state = self.load()
        request = self._operation_request("reserve", {"kind": kind, "scope": scope, "resume": resume})
        replay = self._operation_replay(state, operation_id, "reserve", request)
        if replay is not None:
            return replay
        budget = self.budget(state, kind, scope)
        cap = self.limits()[kind]
        if resume is not None:
            if budget["pending"] != resume:
                raise ProtocolError("Resume must name the original unfinished reservation.")
            result = {"attempt": resume, "cap": cap, "resumed": True}
            self._operation_store(state, operation_id, "reserve", request, result)
            if operation_id is not None:
                self.save(state)
            return result
        if budget["pending"] is not None:
            if operation_id is not None and budget.get("operation_id") == operation_id:
                result = {"attempt": budget["pending"], "cap": cap, "resumed": True}
                self._operation_store(state, operation_id, "reserve", request, result)
                self.save(state)
                return result
            raise ProtocolError(f"Attempt {budget['pending']} is unfinished; resume it instead of allocating another.")
        if budget["used"] >= cap:
            raise ProtocolError(f"{kind} budget exhausted ({budget['used']}/{cap}); retain blockers and request a bounded recovery decision.")
        budget["used"] += 1
        budget["pending"] = budget["used"]
        if operation_id is not None:
            budget["operation_id"] = self._operation_id(operation_id)
        result = {"attempt": budget["pending"], "cap": cap, "resumed": False}
        self._operation_store(state, operation_id, "reserve", request, result)
        self.save(state)
        return result

    def complete(self, kind: str, scope: str, attempt: int, operation_id: str | None = None) -> dict[str, Any]:
        state = self.load()
        request = self._operation_request("complete", {"kind": kind, "scope": scope, "attempt": attempt})
        replay = self._operation_replay(state, operation_id, "complete", request)
        if replay is not None:
            return replay
        budget = self.budget(state, kind, scope)
        if budget["pending"] != attempt:
            raise ProtocolError("Completion must match the reserved attempt; do not clear another pending pass.")
        budget["pending"] = None
        budget.pop("operation_id", None)
        result = dict(budget)
        self._operation_store(state, operation_id, "complete", request, result)
        self.save(state)
        return result

    def needs(self, kind: str) -> bool:
        state = self.load()
        if kind in {"review", "quality", "standards"}:
            return not self.current(state, kind, "pass")
        if kind == "accepted-simplification":
            return bool(self.accepted_candidates(state))
        if kind == "simplification-verification":
            return bool(self.accepted_candidates(state)) and not self.current(state, "simplify-verify", "pass")
        if kind == "repair":
            if self.current(state, "review", "pass"):
                return False
            if not self.current(state, "review", "blocked"):
                raise ProtocolError("A current complete blocked Review is required before repair; refresh coverage/evidence first.")
            data = state["stages"]["review"]["data"]
            if not data["repairable"] or not any(item["blocking"] and item["status"] == "open" for item in data["findings"]):
                raise ProtocolError("No confirmed repairable blocker; recover evidence or scope instead of editing speculatively.")
            budget = self.budget(state, "review", "outgoing-diff")
            return budget["pending"] is not None or budget["used"] < self.limits()["review"]
        if kind == "convergence":
            if self.current(state, "converge", "converged"):
                return False
            if not self.current(state, "converge", "tasks-appended"):
                raise ProtocolError("Run the Core convergence assessment and record its current result first.")
            budget = self.budget(state, "convergence", "outgoing-diff")
            return budget["pending"] is not None or budget["used"] < self.limits()["convergence"]
        if kind in {"clarification", "simplification"}:
            stage = "clarify" if kind == "clarification" else "simplify"
            if not self.current(state, stage):
                raise ProtocolError(f"Missing or stale {stage} result; collect the owner result before deciding to skip.")
            result = state["stages"][stage]
            if result["verdict"] == "blocked":
                raise ProtocolError(f"{stage} is blocked; resolve its findings before proceeding.")
            return result["data"]["needs_approval"] if stage == "clarify" else bool(result["data"]["candidates"])
        if kind == "tasks":
            return any(mark == " " for mark, _ in TASK.findall(self.bound_file(state, "tasks").read_text(encoding="utf-8")))
        raise ProtocolError("Unknown conditional dispatch kind.")

    def _observe_evidence(self, state: dict[str, Any]) -> dict[str, str]:
        path = self.directory / "evidence.md"
        if not path.is_file() or path.is_symlink():
            raise ProtocolError("Canonical same-run evidence is missing; run Evidence before handoff.")
        header = fields(path)
        if header.get("delivery_run") != self.run or header.get("lane") != state["lane"]:
            raise ProtocolError("Canonical same-run evidence is missing or has another identity; run Evidence before handoff.")
        snapshot = self.snapshot(state)
        return {
            "kind": "evidence", "path": self.relative(path), "sha256": digest(path.read_bytes()),
            "head": snapshot["head"], "input_fingerprint": snapshot["fingerprint"],
        }

    def _evidence_current(self, state: dict[str, Any]) -> tuple[bool, str | None]:
        observation = state.get("evidence_observation")
        if not isinstance(observation, dict):
            return False, "Evidence has not been observed and persisted by the runtime."
        path = self.inside(observation["path"])
        if path != self.directory / "evidence.md":
            return False, "The persisted Evidence observation points outside the canonical evidence.md."
        if not path.is_file() or path.is_symlink():
            return False, "Previously recorded canonical Evidence is missing; rerun Evidence before handoff."
        if digest(path.read_bytes()) != observation["sha256"]:
            return False, "Previously recorded canonical Evidence changed; rerun Evidence before handoff."
        snapshot = self.snapshot(state)
        if snapshot["head"] != observation["head"] or snapshot["fingerprint"] != observation["input_fingerprint"]:
            return False, "The project inputs changed after Evidence was observed; refresh Evidence before handoff."
        header = fields(path)
        if header.get("delivery_run") != self.run or header.get("lane") != state["lane"]:
            return False, "Canonical Evidence identity no longer matches this run/lane."
        return True, None

    def _find_handoff_body(self, state: dict[str, Any]) -> Path:
        evidence = self.directory / "evidence.md"
        header = fields(evidence)
        requested = header.get("pr_body_path", "").strip()
        candidates: list[Path] = []
        if requested and requested.lower() not in {"inline", "none"}:
            candidates.append(self.inside(requested))
        else:
            exact = self.directory / "pull-request.md"
            if exact.is_file():
                candidates.append(exact)
            candidates.extend(sorted(self.directory.glob("pull-request-*.md")))
        valid: list[Path] = []
        for path in candidates:
            if path.parent != self.directory or not re.fullmatch(r"pull-request(?:-[A-Za-z0-9._-]+)?\.md", path.name) or not path.is_file() or path.is_symlink() or not path.read_bytes().strip():
                continue
            valid.append(path)
        if not valid:
            raise ProtocolError("Native Handoff must produce a nonempty canonical pull-request.md or pull-request-<slice>.md before phase handoff.")
        if len(valid) > 1 and (self.directory / "pull-request.md") not in valid:
            raise ProtocolError("Multiple slice PR bodies exist without a canonical selected body; record PR_BODY_PATH in same-run Evidence.")
        return self.directory / "pull-request.md" if self.directory / "pull-request.md" in valid else valid[0]

    def _require_handoff_native(self, state: dict[str, Any], persist: bool = True) -> dict[str, str]:
        body = self._find_handoff_body(state)
        snapshot = self.snapshot(state)
        observation = {
            "kind": "handoff", "path": self.relative(body), "sha256": digest(body.read_bytes()),
            "head": snapshot["head"], "input_fingerprint": snapshot["fingerprint"],
        }
        if persist:
            state["handoff_observation"] = observation
            self.save(state)
        return observation

    def _handoff_blockers(self, state: dict[str, Any]) -> list[str]:
        blockers: list[str] = []
        evidence_ok, evidence_reason = self._evidence_current(state)
        if not evidence_ok and evidence_reason:
            blockers.append(evidence_reason)
        observation = state.get("handoff_observation")
        if not isinstance(observation, dict):
            blockers.append("Native Handoff PR_BODY observation is missing; run Handoff before claiming handoff-ready.")
        else:
            try:
                body = self.inside(observation["path"])
                if body.parent != self.directory or not body.is_file() or body.is_symlink():
                    blockers.append("Previously observed native Handoff PR_BODY is missing; rerun Handoff.")
                elif digest(body.read_bytes()) != observation["sha256"]:
                    blockers.append("Previously observed native Handoff PR_BODY changed; rerun Handoff.")
                else:
                    snapshot = self.snapshot(state)
                    if snapshot["head"] != observation["head"] or snapshot["fingerprint"] != observation["input_fingerprint"]:
                        blockers.append("Project inputs changed after native Handoff; rerun review, Evidence, and Handoff.")
            except (ProtocolError, OSError) as exc:
                blockers.append(str(exc))
        if not self.current(state, "review", "pass"):
            blockers.append("Current passing Review is required before handoff.")
        return blockers

    def _terminal_header(self, state: dict[str, Any], header: dict[str, str]) -> tuple[str | None, list[str]]:
        status = header.get("status")
        if status not in TERMINAL:
            return status, []
        blockers: list[str] = []
        evidence_path = self.directory / "evidence.md"
        if not evidence_path.is_file() or evidence_path.is_symlink():
            blockers.append("Terminal Evidence file is missing or is not a regular canonical file.")
        if header.get("delivery_run") != self.run:
            blockers.append("Terminal Evidence delivery_run does not match this run.")
        if header.get("lane") != state["lane"]:
            blockers.append("Terminal Evidence lane does not match this run.")
        pull_request = header.get("pull_request", "").strip().lower()
        concrete = bool(pull_request) and pull_request not in {"pending", "none", "not-created", "not-published", "not-yet-published"}
        if status in {"delivered", "abandoned"} and not concrete:
            blockers.append(f"Terminal {status} Evidence needs a concrete observed pull_request reference.")
        if status == "superseded" and not concrete and not header.get("superseded_by", "").strip():
            blockers.append("Superseded Evidence needs a concrete replacement reference.")
        if "verified" in header and header["verified"].lower() not in {"true", "yes", "1"}:
            blockers.append("Terminal Evidence verified marker is not true.")
        if "outcome" in header:
            expected = {"delivered": "merged", "abandoned": "closed", "superseded": "superseded"}[status]
            if header["outcome"].lower() != expected:
                blockers.append("Terminal Evidence outcome does not match its status.")
        return status, blockers

    def require(self, kind: str) -> dict[str, Any]:
        state = self.load()
        if kind in {"review", "quality", "standards", "analyze", "convergence", "simplify-verify"}:
            stage = "converge" if kind == "convergence" else kind
            verdict = "converged" if kind == "convergence" else "pass"
            if not self.current(state, stage, verdict):
                raise ProtocolError(f"Current {stage} {verdict} is required; inspect status and the original owner report.")
        elif kind == "planning":
            dirty = self.execution_dirty_paths()
            if dirty:
                raise ProtocolError("Planning checkpoint requires a clean execution entry. Declared run operational records do not block; commit only approved planning paths under project authorization. Dirty paths:\n" + "\n".join(dirty))
            for name in ("spec", "plan", "tasks"):
                self.bound_file(state, name)
            if not self.current(state, "checkpoint", "pass"):
                raise ProtocolError("Record a current passing SD Core planning checkpoint through Delivery Route before Ralph.")
            state["execution_head"] = self.git("rev-parse", "HEAD").decode().strip()
            self.save(state)
        elif kind == "task-closure":
            return {"required": kind, "ready": True, **self.audit_task_closure(state)}
        elif kind == "evidence":
            if state["lane"] == "feature":
                self.audit_task_closure(state)
            state["evidence_observation"] = self._observe_evidence(state)
            self.save(state)
        else:
            raise ProtocolError("Unknown required transition.")
        return {"required": kind, "ready": True}

    def accepted_candidates(self, state: dict[str, Any]) -> list[str]:
        receipt = state["approvals"].get("simplify")
        if not receipt or receipt.get("choice") != "approve":
            return []
        for value, expected in receipt["inputs"].items():
            path = self.inside(value)
            if not path.is_file() or digest(path.read_bytes()) != expected:
                raise ProtocolError("Accepted Simplify proposal changed; renew its presentation/choice before applying or verifying it.")
        candidates = receipt.get("candidate_ids")
        if not isinstance(candidates, list) or not candidates:
            raise ProtocolError("The Simplify approval has no candidate identity; present and record the actual choice.")
        return candidates

    def present(self, name: str, inputs: list[str], bindings: list[str] | None = None, operation_id: str | None = None) -> dict[str, Any]:
        state = self.load()
        request = self._operation_request("present", {"name": name, "inputs": list(inputs), "bindings": list(bindings or [])})
        replay = self._operation_replay(state, operation_id, "present", request)
        if replay is not None:
            return replay
        resolved_inputs = [*inputs, *(self.relative(self.bound_file(state, item)) for item in (bindings or []))]
        safe_id(name)
        if not resolved_inputs:
            raise ProtocolError("Presentation needs the actual files shown at the gate.")
        hashes: dict[str, str] = {}
        for value in resolved_inputs:
            path = self.inside(value)
            if not path.is_file() or path.is_symlink():
                raise ProtocolError(f"Presented input is missing or is not a regular file: {value}")
            hashes[self.relative(path)] = digest(path.read_bytes())
        receipt: dict[str, Any] = {"choice": "pending", "inputs": hashes, "presented_head": self.git("rev-parse", "HEAD").decode().strip()}
        if name == "simplify":
            if not self.current(state, "simplify", "candidates"):
                raise ProtocolError("Present a current native candidate scan before the Simplify gate.")
            proposal = state["stages"]["simplify"]
            if proposal["report"]["path"] not in hashes:
                raise ProtocolError("The Simplify gate must present the native candidate proposal file.")
            receipt["candidate_ids"] = proposal["data"]["candidates"]
        if operation_id is not None:
            receipt["operation_id"] = self._operation_id(operation_id)
        state["approvals"][name] = receipt
        self._operation_store(state, operation_id, "present", request, receipt)
        self.save(state)
        return receipt

    def decide(self, name: str, choice: str, operation_id: str | None = None) -> dict[str, Any]:
        state = self.load()
        request = self._operation_request("decide", {"name": name, "choice": choice})
        replay = self._operation_replay(state, operation_id, "decide", request)
        if replay is not None:
            return replay
        receipt = state["approvals"].get(name)
        if not receipt or receipt["choice"] != "pending" or choice not in {"approve", "reject"}:
            if operation_id is not None and receipt and receipt.get("operation_id") == operation_id and receipt.get("choice") == choice:
                return receipt
            raise ProtocolError("Record a real choice against an existing pending presentation.")
        for value, expected in receipt["inputs"].items():
            path = self.inside(value)
            if not path.is_file() or path.is_symlink() or digest(path.read_bytes()) != expected:
                raise ProtocolError("Presented inputs changed while the gate was paused; present again before accepting a choice.")
        receipt["choice"] = choice
        if operation_id is not None:
            receipt["operation_id"] = self._operation_id(operation_id)
        self._operation_store(state, operation_id, "decide", request, receipt)
        self.save(state)
        return receipt

    def phase(self, name: str, operation_id: str | None = None) -> dict[str, Any]:
        state = self.load()
        request = self._operation_request("phase", {"name": name})
        replay = self._operation_replay(state, operation_id, "phase", request)
        if replay is not None:
            return replay
        if name not in PHASES or fields(self.directory / "evidence.md").get("status") in TERMINAL:
            raise ProtocolError("Invalid phase or terminal run; do not reopen an outcome with a phase update.")
        if name == "handoff":
            self.require("review")
            if state["lane"] == "feature":
                self.audit_task_closure(state)
            state["evidence_observation"] = self._observe_evidence(state)
            state["handoff_observation"] = self._require_handoff_native(state, persist=False)
        state["phase"] = name
        result = self.status(state)
        self._operation_store(state, operation_id, "phase", request, result)
        self.save(state)
        return result

    def _remote_repository(self) -> str | None:
        try:
            raw = self.git("config", "--get", "remote.origin.url").decode().strip()
        except ProtocolError:
            return None
        raw = raw.removesuffix(".git")
        match = re.search(r"github\.com[/:]([^/ :]+/[^/ :]+)$", raw, re.IGNORECASE)
        return match.group(1).lower() if match else None

    def _pr_identity(self, value: str, repository: str | None = None) -> str | None:
        value = value.strip()
        url = re.fullmatch(r"https?://github\.com/([^/]+/[^/]+)/pull/(\d+)/?", value, re.IGNORECASE)
        if url:
            return f"{url[1].lower()}#{int(url[2])}"
        number = re.fullmatch(r"#?(\d+)", value)
        if number:
            return f"{repository.lower()}#{int(number[1])}" if repository else f"#{int(number[1])}"
        return value.lower() if value else None

    def outcome(self, outcome: str, verified: bool, pr: str | None) -> dict[str, Any]:
        if outcome == "unverified" or not verified:
            raise ProtocolError("Outcome is unverified. Keep the active record and all workspace artifacts; retry after tracker verification.")
        if outcome not in {"merged", "closed", "superseded"}:
            raise ProtocolError("Unknown observed outcome.")
        state = self.load()
        header = fields(self.directory / "evidence.md")
        terminal_status, terminal_blockers = self._terminal_header(state, header)
        expected_terminal = {"merged": "delivered", "closed": "abandoned", "superseded": "superseded"}[outcome]
        evidence_ok, evidence_reason = self._evidence_current(state)
        if not evidence_ok and not (terminal_status == expected_terminal and not terminal_blockers):
            raise ProtocolError(evidence_reason or "Verify the canonical same-run evidence before closing.")
        if header.get("delivery_run") != self.run or header.get("lane") != state["lane"]:
            raise ProtocolError("Verify the canonical same-run evidence identity before closing.")
        existing = header.get("pull_request", "").strip()
        pending = not existing or existing.lower() in {"pending", "none", "not-created", "not-published", "not-yet-published"}
        repository = self._remote_repository()
        existing_identity = self._pr_identity(existing, repository) if not pending else None
        supplied_identity = self._pr_identity(pr, repository) if pr else None
        if pr and not pending and existing_identity != supplied_identity:
            # Numeric and URL spellings are equivalent only with a concrete provider mapping.
            raise ProtocolError("Concrete PR identity conflict; retain the record and resolve the project/repository mapping explicitly.")
        if outcome == "closed" and not pr:
            raise ProtocolError("A verified closed PR reference is required.")
        evidence_path = self.directory / "evidence.md"
        snapshot = self.snapshot(state)
        state["evidence_observation"] = {
            "kind": "evidence", "path": self.relative(evidence_path), "sha256": digest(evidence_path.read_bytes()),
            "head": snapshot["head"], "input_fingerprint": snapshot["fingerprint"],
        }
        self.save(state)
        return {"eligible": True, "outcome": outcome, "pull_request": pr or (existing if existing else None), "writes_performed": False}

    def status(self, state: dict[str, Any] | None = None) -> dict[str, Any]:
        if state is None and not self.path.exists():
            header = fields(self.directory / "evidence.md")
            raw_status = header.get("status", "legacy" if self.directory.exists() else "absent")
            blockers: list[str] = []
            if raw_status in TERMINAL:
                if header.get("delivery_run") != self.run or header.get("lane") not in LANES:
                    blockers.append("Terminal legacy Evidence identity is missing or corrupt.")
                pull_request = header.get("pull_request", "").lower()
                if raw_status in {"delivered", "abandoned"} and pull_request in {"", "pending", "none", "not-created", "not-published", "not-yet-published"}:
                    blockers.append("Terminal legacy Evidence has no concrete observed pull_request reference.")
            return {
                "delivery_run": self.run,
                "status": "verification-required" if blockers else raw_status,
                "lane": header.get("lane"),
                "blockers": blockers,
                "next_action": blockers[0] if blockers else ("Inspect the existing artifacts and recover identity/counters; do not initialize over them." if self.directory.exists() else "Initialize a new run after routing."),
            }
        if state is None:
            state = self.load()
        header = fields(self.directory / "evidence.md")
        terminal_status, terminal_blockers = self._terminal_header(state, header)
        phase = state["phase"]
        blockers = list(terminal_blockers)
        evidence_observed = state.get("evidence_observation")
        if evidence_observed is not None:
            evidence_ok, evidence_reason = self._evidence_current(state)
            if not evidence_ok and evidence_reason:
                blockers.append(evidence_reason)
        if terminal_status in TERMINAL:
            status = terminal_status if not blockers else "verification-required"
        else:
            status = "active"
            if phase == "handoff":
                blockers.extend(self._handoff_blockers(state))
                status = "handoff-ready" if not blockers else "verification-required"
        pending = list(state["pending"])
        pending_tasks = self._component("tasks").TaskClosure(self, ProtocolError).pending() if state["lane"] == "feature" else []
        reservations = {key: value for key, value in state["attempts"].items() if value["pending"] is not None}
        if blockers:
            next_action = blockers[0]
        elif terminal_status in TERMINAL:
            next_action = "Outcome recorded; retain durable evidence."
        elif reservations:
            next_action = "Resume the named reserved pass; do not allocate or reset its attempt."
        elif pending:
            next_action = "Recover the pending owner result or explicitly resume its unchanged input ticket."
        elif pending_tasks:
            task = pending_tasks[0]
            next_action = f"Recover task {task['task']} ({task['status']}) on {task['branch']}; retain its original HEAD/owner receipts and use task-record for an already-created closure commit."
        elif status == "handoff-ready":
            next_action = "Await separately authorized publication and the observed PR outcome, then close this run."
        else:
            next_action = f"Continue the {phase} owner using this run's bindings and recorded decisions."
        return {
            "schema_version": SCHEMA, "delivery_run": self.run, "lane": state["lane"],
            "phase": phase, "status": status, "bindings": state["bindings"],
            "approvals": {key: value["choice"] for key, value in state["approvals"].items()},
            "attempts": state["attempts"], "pending_stages": pending,
            "pending_tasks": pending_tasks,
            "blockers": blockers, "next_action": next_action,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=(
        "init", "bind", "phase", "begin", "record", "needs", "require", "reserve",
        "complete", "present", "decide", "status", "resume", "outcome",
        "task-start", "task-gate", "task-record", "close-record",
    ))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--run")
    parser.add_argument("--workflow-run", help="engine run id used to derive the persisted active occurrence operation key")
    parser.add_argument("--lane", choices=sorted(LANES))
    parser.add_argument("--bug-slug")
    parser.add_argument("--feature-dir")
    parser.add_argument("--feature-from-packet")
    parser.add_argument("--assessment")
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("--binding", action="append", default=[], choices=("spec", "plan", "tasks", "assessment", "clarification_checklist"))
    parser.add_argument("--operation-id", help="stable occurrence key used to replay one completed helper mutation")
    parser.add_argument("--stage", choices=sorted(VERDICTS))
    parser.add_argument("--file")
    parser.add_argument("--planning-manifest", help="exact project-relative checkpoint manifest under this run's runtime directory")
    parser.add_argument("--kind")
    parser.add_argument("--scope", default="outgoing-diff")
    parser.add_argument("--name")
    parser.add_argument("--choice", choices=("approve", "reject"))
    parser.add_argument("--attempt", type=int)
    parser.add_argument("--resume", nargs="?", const=True, type=int)
    parser.add_argument("--outcome", choices=("merged", "closed", "superseded", "unverified"))
    parser.add_argument("--verified", action="store_true")
    parser.add_argument("--pr")
    parser.add_argument("--task", help="exact bound Task ID for a Ralph closure transition")
    parser.add_argument("--branch", help="approved execution branch required before task edits")
    parser.add_argument("--commit", help="exact task closure commit to associate with pre-commit evidence")
    parser.add_argument("--plain", action="store_true", help="print a reservation attempt as a shell-safe scalar")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if not args.run and args.operation == "status":
            directory = args.root.resolve() / ".specify/delivery"
            result = []
            if directory.is_dir():
                for path in sorted(directory.iterdir()):
                    if not path.is_dir():
                        continue
                    try:
                        result.append(Runtime(args.root, path.name).status())
                    except (ProtocolError, OSError) as exc:
                        result.append({
                            "delivery_run": path.name,
                            "status": "corrupt",
                            "next_action": f"Inspect and recover this run without initializing over it: {exc}",
                        })
        else:
            if not args.run:
                raise ProtocolError("An explicit --run is required; use status to list available runs.")
            runtime = Runtime(args.root, args.run)
            operation = args.operation
            mutation_operations = {"init", "bind", "phase", "begin", "record", "reserve", "complete", "present", "decide"}
            if args.workflow_run and args.operation_id:
                raise ProtocolError("Use either --workflow-run for engine occurrence journaling or an explicit --operation-id, not both.")
            operation_id = args.operation_id
            if args.workflow_run and operation in mutation_operations:
                operation_id = runtime.workflow_operation_id(args.workflow_run, operation, vars(args))
            if operation == "init":
                runtime.init(args.lane, args.bug_slug, operation_id)
                result = runtime.status()
            elif operation == "bind":
                if args.feature_from_packet and (args.feature_dir or args.assessment):
                    raise ProtocolError("Choose one explicit Feature packet binding or direct binding, not both.")
                result = runtime.bind_from_packet(args.feature_from_packet, operation_id, args.input) if args.feature_from_packet else runtime.bind(args.feature_dir, args.assessment, args.input, operation_id)
            elif operation == "phase":
                result = runtime.phase(args.name, operation_id)
            elif operation == "begin":
                result = runtime.begin(args.stage, bool(args.resume), args.scope, operation_id)
            elif operation == "record":
                result = runtime.record(args.stage, args.file, operation_id, args.planning_manifest)
            elif operation == "needs":
                sys.stdout.write("true" if runtime.needs(args.kind) else "false")
                return 0
            elif operation == "require":
                result = runtime.require(args.kind)
            elif operation == "reserve":
                result = runtime.reserve(args.kind, args.scope, args.resume, operation_id)
                if args.plain:
                    sys.stdout.write(str(result["attempt"]))
                    return 0
            elif operation == "complete":
                result = runtime.complete(args.kind, args.scope, args.attempt, operation_id)
            elif operation == "present":
                result = runtime.present(args.name, args.input, args.binding, operation_id)
            elif operation == "decide":
                result = runtime.decide(args.name, args.choice, operation_id)
            elif operation == "outcome":
                result = runtime.outcome(args.outcome, args.verified, args.pr)
            elif operation == "close-record":
                result = runtime.close_record(args.outcome, args.verified, args.pr, args.file)
            elif operation == "task-start":
                result = runtime.task_start(args.task, args.branch, args.input)
            elif operation == "task-gate":
                result = runtime.task_gate(args.task, args.file)
            elif operation == "task-record":
                result = runtime.task_record(args.task, args.commit)
            else:
                result = runtime.status()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ProtocolError, OSError) as exc:
        print(f"DELIVERY_RUNTIME: blocked\n{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
