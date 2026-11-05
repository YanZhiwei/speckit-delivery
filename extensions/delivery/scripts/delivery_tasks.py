#!/usr/bin/env python3
"""Ralph task-close transport checks; native owners retain semantic authority."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any

TASK = re.compile(r"^\s*-\s*\[([ xX])\]\s+(T\d+)\b", re.MULTILINE)
OBJECT = re.compile(r"[0-9a-f]{40,64}")


def read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Task closure record must be an object.")
    return value


class TaskClosure:
    def __init__(self, runtime: Any, error: type[Exception]):
        self.runtime = runtime
        self.error = error

    def _queue(self, state: dict[str, Any]) -> tuple[Path, str, list[tuple[str, str]]]:
        if state["lane"] != "feature":
            raise self.error("Task closure auditing requires a bound Feature run.")
        path = self.runtime.bound_file(state, "tasks")
        text = path.read_bytes().decode("utf-8")
        entries = [(task, mark.lower()) for mark, task in TASK.findall(text)]
        ids = [task for task, _ in entries]
        if not ids or len(ids) != len(set(ids)):
            raise self.error("Task closure needs a nonempty queue with unique Task IDs.")
        return path, text, entries

    def _path(self, task: str) -> Path:
        if not isinstance(task, str) or not re.fullmatch(r"T\d+", task):
            raise self.error("Use the exact T<number> identifier from the bound tasks.md.")
        return self.runtime.inside(self.runtime.local / "task-closures" / f"{task}.json")

    def _save(self, path: Path, value: dict[str, Any]) -> None:
        # Same atomic writer as the central helper, without another schema owner.
        import tempfile
        path.parent.mkdir(parents=True, exist_ok=True)
        name = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
                name = stream.name
                json.dump(value, stream, indent=2, ensure_ascii=False)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, path)
            name = None
        finally:
            if name:
                Path(name).unlink(missing_ok=True)

    def _load(self, task: str) -> dict[str, Any]:
        path = self._path(task)
        if not path.is_file() or path.is_symlink():
            raise self.error(f"Task {task} has no runtime closure record; run task-start before editing.")
        try:
            record = read(path)
        except (ValueError, UnicodeError) as exc:
            raise self.error(f"Task {task} closure record is malformed: {exc}") from exc
        if record.get("schema_version") != 1 or record.get("delivery_run") != self.runtime.run or record.get("task") != task or record.get("lane") != "feature":
            raise self.error(f"Task {task} closure identity does not match this run.")
        return record

    def _branch(self) -> str:
        return self.runtime.git("branch", "--show-current").decode().strip()

    def _head(self) -> str:
        return self.runtime.git("rev-parse", "HEAD").decode().strip()

    def _tree(self, revision: str) -> dict[str, dict[str, str]]:
        result = {}
        for entry in self.runtime.git("ls-tree", "-r", "-z", "--full-tree", revision).split(b"\0"):
            if not entry:
                continue
            metadata, raw_name = entry.split(b"\t", 1)
            mode, _, oid = metadata.decode("ascii").split()
            name = os.fsdecode(raw_name)
            if not self.runtime._operational_record(name):
                result[name] = {"mode": mode, "oid": oid}
        return result

    def _reviewed_tree(self) -> dict[str, dict[str, str]]:
        result = {}
        index = {item["path"]: item for item in self.runtime._index_entries(self.runtime.root)}
        for name in sorted(self.runtime._repository_names(self.runtime.root) | set(index)):
            if self.runtime._operational_record(name):
                continue
            path = self.runtime.inside(name)
            if not path.exists():
                continue
            item = index.get(name, {})
            if item.get("stage", 0) != 0:
                raise self.error("Resolve index conflicts before a task can close.")
            if item.get("mode") == "160000":
                if self.runtime.git_at(path, "status", "--porcelain").strip():
                    raise self.error("A dirty submodule cannot be associated with a task commit.")
                oid = self.runtime.git_at(path, "rev-parse", "HEAD").decode().strip()
                result[name] = {"mode": "160000", "oid": oid}
            elif path.is_file():
                # Reuse the index blob for a path Git considers clean. This is
                # important when a prior task queue is CRLF and the current
                # checkout has core.autocrlf enabled: hash-object --path uses
                # the current attribute/filter context and can otherwise project
                # an unchanged file differently from the committed blob. For a
                # genuinely changed path, use Git's own clean filters so the
                # projection still matches the blob task commit will contain.
                unchanged = False
                if item.get("stage") == 0:
                    try:
                        self.runtime.git("diff", "--quiet", "--", name)
                        self.runtime.git("diff", "--cached", "--quiet", "--", name)
                        unchanged = True
                    except self.error:
                        unchanged = False
                oid = item["object"] if unchanged else self.runtime.git("hash-object", f"--path={name}", str(path)).decode().strip()
                mode = item.get("mode", "100755" if os.name != "nt" and path.stat().st_mode & 0o111 else "100644")
                result[name] = {"mode": mode, "oid": oid}
            else:
                raise self.error(f"Unsupported task commit entry: {name}")
        return result

    def start(self, task: str, branch: str, inputs: list[str]) -> dict[str, Any]:
        state = self.runtime.load()
        path, text, entries = self._queue(state)
        if dict(entries).get(task) != " ":
            raise self.error(f"Task {task} must be an unchecked item from the bound queue.")
        if not branch or self._branch() != branch:
            raise self.error("Task branch differs from the explicit approved execution branch; switch before editing.")
        allowed = []
        for name in inputs:
            normalized = self.runtime.relative(self.runtime.inside(name)).rstrip("/")
            if not normalized or normalized == "." or "*" in normalized or normalized.startswith(".git/") or self.runtime._operational_record(normalized):
                raise self.error("Task allowed paths must be exact project paths or directory prefixes, not broad globs/bookkeeping.")
            allowed.append(normalized)
        if not allowed or len(allowed) != len(set(allowed)):
            raise self.error("Task start requires a unique explicit --input allowed-path list.")
        record_path = self._path(task)
        if record_path.exists():
            original = self._load(task)
            if original.get("status") == "started" and original.get("branch") == branch and original.get("pre_commit_head") == self._head() and original.get("allowed_paths") == allowed:
                return original
            raise self.error(f"Task {task} already has a closure occurrence; recover it without resetting evidence.")
        directory = record_path.parent
        if directory.exists():
            for existing in directory.glob("T*.json"):
                previous = self._load(existing.stem)
                if previous.get("status") != "committed":
                    raise self.error(f"Task {previous.get('task')} is unfinished; recover it before selecting {task}.")
        dirty = self.runtime.execution_dirty_paths()
        if dirty:
            raise self.error("Task start requires a clean execution entry: " + ", ".join(dirty))
        record = {
            "schema_version": 1, "delivery_run": self.runtime.run, "lane": "feature", "task": task,
            "status": "started", "branch": branch, "pre_commit_head": self._head(),
            "tasks_path": self.runtime.relative(path), "tasks_before_b64": base64.b64encode(text.encode("utf-8")).decode("ascii"),
            "allowed_paths": allowed,
        }
        self._save(record_path, record)
        return record

    def _owners(self, state: dict[str, Any], task: str, snapshot: dict[str, Any]) -> dict[str, Any]:
        owners = {}
        for stage in ("quality", "standards", "review"):
            owner = state["stages"].get(stage)
            if not isinstance(owner, dict) or owner.get("scope") != f"task-{task}" or not self.runtime.current(state, stage, "pass"):
                raise self.error(f"Task {task} requires current task-{task} {stage} evidence; final outgoing-diff evidence cannot replace it.")
            if owner["input_fingerprint"] != snapshot["fingerprint"]:
                raise self.error(f"Task {task} {stage} did not inspect the exact pre-commit snapshot.")
            report = self.runtime.reference(owner["report"])
            if self.runtime._explicit_report_verdict(report, stage) != "pass":
                raise self.error(f"Task {task} needs an explicit native {stage} pass header.")
            owners[stage] = copy.deepcopy(owner)
        return owners

    def gate(self, task: str, file: str | None = None) -> dict[str, Any]:
        state = self.runtime.load()
        record = self._load(task)
        if record.get("status") not in {"started", "gated"} or record["pre_commit_head"] != self._head() or record["branch"] != self._branch():
            raise self.error("Task HEAD/branch changed before closure; recover the original task instead of restamping it.")
        tasks_path, text, _ = self._queue(state)
        before = base64.b64decode(record["tasks_before_b64"], validate=True).decode("utf-8")
        if text != before:
            raise self.error("Task queue changed before task-gate; leave the selected checkbox unchecked.")
        for name in self.runtime.execution_dirty_paths():
            if not any(name == prefix or name.startswith(prefix + "/") for prefix in record["allowed_paths"]):
                raise self.error(f"Task {task} changed an undeclared path: {name}")
        snapshot = self.runtime.snapshot(state)
        owners = self._owners(state, task, snapshot)
        if not file:
            raise self.error("Task gate requires --file pointing to the native docs-refresh applicability record.")
        docs_path = self.runtime.inside(file)
        if not docs_path.is_relative_to(self.runtime.local) or docs_path.is_symlink():
            raise self.error("Docs-refresh applicability must be a regular JSON file inside this run's runtime.")
        docs = read(docs_path)
        if type(docs.get("required")) is not bool:
            raise self.error("Task docs-refresh applicability must say required: true or false.")
        if docs["required"]:
            if docs.get("verdict") not in {"pass", "updated", "unchanged"} or docs.get("input_fingerprint") != snapshot["fingerprint"]:
                raise self.error("Required task docs-refresh is missing, blocked or stale.")
            self.runtime.reference(docs.get("report"))
        elif not isinstance(docs.get("reason"), str) or not docs["reason"].strip():
            raise self.error("A task without docs refresh needs an explicit applicability reason.")
        record.update({"status": "gated", "reviewed_snapshot": snapshot, "reviewed_tree": self._reviewed_tree(), "owners": owners, "docs_refresh": docs})
        self._save(self._path(task), record)
        return {"task": task, "gate": "pass", "head": record["pre_commit_head"], "input_fingerprint": snapshot["fingerprint"]}

    def _validate_owners(self, state: dict[str, Any], record: dict[str, Any]) -> None:
        owners = record.get("owners")
        snapshot = record.get("reviewed_snapshot")
        if not isinstance(owners, dict) or set(owners) != {"quality", "standards", "review"} or not isinstance(snapshot, dict):
            raise self.error(f"Task {record['task']} has incomplete Quality/Standards/Review receipts.")
        self.runtime._validate_snapshot_shape(snapshot)
        historical = {**state, "stages": owners, "pending": {}}
        for stage, owner in owners.items():
            self.runtime._validate_result_shape(historical, stage, owner, stored=True, dynamic=False)
            if owner.get("scope") != f"task-{record['task']}" or owner.get("verdict") != "pass" or owner.get("input_fingerprint") != snapshot["fingerprint"] or owner.get("input_snapshot", {}).get("head") != record["pre_commit_head"]:
                raise self.error(f"Task {record['task']} {stage} scope/snapshot/HEAD does not match its closure.")
            if owner.get("input_snapshot") != snapshot or owner.get("output_snapshot") != snapshot:
                raise self.error("A task owner did not validate the exact unchanged task snapshot.")
        dependencies = owners["review"]["data"].get("dependencies", {})
        if any(dependencies.get(stage) != self.runtime._dependency_receipt(owners[stage]) for stage in ("quality", "standards")):
            raise self.error("Historical task Review does not bind the exact task Quality/Standards receipts.")
        docs = record.get("docs_refresh", {})
        if type(docs.get("required")) is not bool or (not docs["required"] and not docs.get("reason")):
            raise self.error("Historical task docs-refresh applicability is incomplete.")
        if docs["required"]:
            if docs.get("input_fingerprint") != snapshot["fingerprint"] or docs.get("verdict") not in {"pass", "updated", "unchanged"}:
                raise self.error("Historical task docs-refresh identity is stale.")
            self.runtime.reference(docs.get("report"))

    def _verify_commit(self, state: dict[str, Any], record: dict[str, Any], commit: str) -> None:
        if not isinstance(commit, str) or not OBJECT.fullmatch(commit):
            raise self.error("Task commit must be a full Git commit object id.")
        parents = self.runtime.git("rev-list", "--parents", "-n", "1", commit).decode().split()
        if parents != [commit, record["pre_commit_head"]]:
            raise self.error("Task commit must have exactly the task-start HEAD as its sole parent.")
        message = self.runtime.git("show", "-s", "--format=%B", commit).decode("utf-8", errors="replace")
        if not re.search(rf"(?<![A-Za-z0-9_]){re.escape(record['task'])}(?![A-Za-z0-9_])", message):
            raise self.error("Task commit message must identify the exact Task ID.")
        actual = self._tree(commit)
        expected = copy.deepcopy(record.get("reviewed_tree"))
        if not isinstance(expected, dict):
            raise self.error("Task closure has no reviewed Git tree projection.")
        tasks_name = record["tasks_path"]
        # A tracked tasks.md may change only the selected checkbox between the
        # original owner snapshot and the closure commit. Ignored queues stay local.
        actual_queue = actual.pop(tasks_name, None)
        original_queue = expected.pop(tasks_name, None)
        if original_queue is not None:
            closed_queue = record.get("closed_queue")
            if not isinstance(closed_queue, dict) or closed_queue.get("mode") != original_queue.get("mode") or actual_queue != closed_queue:
                raise self.error("The tracked task queue must retain its mode and exact checkbox-adjusted committed blob.")
        elif actual_queue is not None:
            raise self.error("Task closure cannot change the queue's tracked/ignored policy.")
        if actual != expected:
            raise self.error("Task commit contents/modes differ from the reviewed tree; rerun native owners before closing.")
        self._validate_owners(state, record)
        self.runtime.git("merge-base", "--is-ancestor", commit, self._head())

    def _closed_queue(self, record: dict[str, Any], text: str) -> None:
        before = base64.b64decode(record["tasks_before_b64"], validate=True).decode("utf-8")
        matches = [match for match in TASK.finditer(before) if match[2] == record["task"]]
        if len(matches) != 1 or matches[0][1] != " ":
            raise self.error("Task-start queue does not contain exactly one unchecked selected Task.")
        match = matches[0]
        variants = {before[:match.start(1)] + mark + before[match.end(1):] for mark in ("x", "X")}
        if text not in variants:
            raise self.error("Closure may change only the selected task checkbox; task text or another checkbox changed.")

    def record(self, task: str, commit: str) -> dict[str, Any]:
        state = self.runtime.load()
        record = self._load(task)
        if record.get("status") == "committed" and record.get("commit") == commit:
            self._verify_commit(state, record, commit)
            return record
        if record.get("status") != "gated" or self._branch() != record.get("branch") or self._head() != commit:
            raise self.error("Run task-gate before the exact task commit on its original execution branch.")
        path, text, _ = self._queue(state)
        self._closed_queue(record, text)
        current = self.runtime.snapshot(state)
        before = record["reviewed_snapshot"]
        names = set(before["files"]) | set(current["files"])
        if any(name != record["tasks_path"] and before["files"].get(name) != current["files"].get(name) for name in names):
            raise self.error("Requirements or worktree inputs changed after the task gate.")
        original_queue = record["reviewed_tree"].get(record["tasks_path"])
        record["closed_queue"] = None if original_queue is None else {
            "mode": original_queue["mode"],
            "oid": self.runtime.git("hash-object", f"--path={record['tasks_path']}", str(path)).decode().strip(),
        }
        self._verify_commit(state, record, commit)
        if self.runtime.execution_dirty_paths():
            raise self.error("Task commit left execution-relevant dirt; recover before recording closure.")
        record.update({"status": "committed", "commit": commit, "tasks_after_b64": base64.b64encode(path.read_bytes()).decode("ascii"), "queue_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        self._save(self._path(task), record)
        return record

    def pending(self) -> list[dict[str, Any]]:
        directory = self.runtime.inside(self.runtime.local / "task-closures")
        if not directory.exists():
            return []
        result = []
        for path in sorted(directory.glob("T*.json")):
            record = self._load(path.stem)
            if record.get("status") not in {"started", "gated", "committed"}:
                raise self.error("Task closure has an unknown transition; recover the original record.")
            if record["status"] != "committed":
                result.append({"task": record["task"], "status": record["status"], "branch": record["branch"], "pre_commit_head": record["pre_commit_head"]})
        return result

    @staticmethod
    def _definitions(text: str) -> str:
        # Preserve task definitions, order, whitespace and newlines. Only a
        # task checkbox is mutable; later Converge work may append to the tail.
        for match in reversed(list(TASK.finditer(text))):
            text = text[:match.start(1)] + " " + text[match.end(1):]
        return text

    def audit(self, state: dict[str, Any] | None = None) -> dict[str, Any]:
        state = state or self.runtime.load()
        _, current_text, entries = self._queue(state)
        unchecked = [task for task, mark in entries if mark == " "]
        if unchecked:
            raise self.error("Task closure requires zero unchecked Tasks: " + ", ".join(unchecked))
        ids = {task for task, _ in entries}
        directory = self.runtime.inside(self.runtime.local / "task-closures")
        recorded_ids = {path.stem for path in directory.glob("*.json")} if directory.exists() else set()
        if recorded_ids - ids:
            raise self.error("The queue removed historical or unfinished Task IDs: " + ", ".join(sorted(recorded_ids - ids)))
        current_head_tree = self._tree(self._head())
        commits = set()
        for task, _ in entries:
            record = self._load(task)
            original_queue = record.get("reviewed_tree", {}).get(record.get("tasks_path")) if isinstance(record.get("reviewed_tree"), dict) else None
            current_queue = current_head_tree.get(record.get("tasks_path"))
            if (original_queue is None) != (current_queue is None) or (original_queue is not None and current_queue.get("mode") != original_queue.get("mode")):
                raise self.error(f"Task {task} changed the bound task queue's tracked/mode policy after its closure.")
            commit = record.get("commit")
            if record.get("status") != "committed" or commit in commits:
                raise self.error(f"Task {task} has no unique verified committed closure.")
            try:
                after_bytes = base64.b64decode(record["tasks_after_b64"], validate=True)
                after_text = after_bytes.decode("utf-8")
                self._closed_queue(record, after_text)
            except (KeyError, ValueError, UnicodeError) as exc:
                raise self.error(f"Task {task} has no valid original queue closure: {exc}") from exc
            if hashlib.sha256(after_bytes).hexdigest() != record.get("queue_sha256"):
                raise self.error(f"Task {task} queue receipt hash changed.")
            if not self._definitions(current_text).startswith(self._definitions(after_text)):
                raise self.error(f"Task {task} definitions/order were rewritten or removed after closure; only checkbox changes and append-only planning are allowed.")
            self._verify_commit(state, record, commit)
            commits.add(commit)
        return {"audited": True, "delivery_run": self.runtime.run, "head": self._head(), "task_count": len(entries), "task_ids": [task for task, _ in entries]}
