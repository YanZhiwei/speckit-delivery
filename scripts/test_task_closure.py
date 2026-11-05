#!/usr/bin/env python3
"""Behavioral tests for the Ralph task-close protocol."""
from __future__ import annotations

import base64
import json
from pathlib import Path
import sys
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import test_delivery_runtime as runtime_tests  # noqa: E402


RUNTIME = runtime_tests.RUNTIME


class RuntimeFixture:
    """Reuse the real Git/runtime fixtures without inheriting their test cases."""

    setUp = runtime_tests.DeliveryRuntimeTest.setUp
    tearDown = runtime_tests.DeliveryRuntimeTest.tearDown
    git = runtime_tests.DeliveryRuntimeTest.git
    write = runtime_tests.DeliveryRuntimeTest.write
    relative = runtime_tests.DeliveryRuntimeTest.relative
    commit = runtime_tests.DeliveryRuntimeTest.commit
    cli = runtime_tests.DeliveryRuntimeTest.cli
    new_runtime = runtime_tests.DeliveryRuntimeTest.new_runtime
    feature_runtime = runtime_tests.DeliveryRuntimeTest.feature_runtime
    reference = runtime_tests.DeliveryRuntimeTest.reference
    native_file = runtime_tests.DeliveryRuntimeTest.native_file
    result_file = runtime_tests.DeliveryRuntimeTest.result_file
    quality_data = runtime_tests.DeliveryRuntimeTest.quality_data
    review_data = runtime_tests.DeliveryRuntimeTest.review_data
    assert_blocked = runtime_tests.DeliveryRuntimeTest.assert_blocked


class TaskClosureTest(RuntimeFixture, unittest.TestCase):
    maxDiff = None

    def task_fixture(
        self,
        run: str,
        tasks: str = "# Tasks\n\n- [ ] T001 Implement the change\n",
    ) -> tuple[object, Path]:
        return self.feature_runtime(run, tasks=tasks)

    def actual_branch(self) -> str:
        return self.git("branch", "--show-current").stdout.strip()

    def start_task(
        self,
        runtime: object,
        task: str = "T001",
        inputs: tuple[str, ...] = ("src/app.py",),
        *,
        via_cli: bool = False,
        branch: str | None = None,
    ) -> dict[str, object]:
        branch = self.actual_branch() if branch is None else branch
        if via_cli:
            result = self.cli(
                "task-start",
                runtime.run,
                task=task,
                branch=branch,
                input=list(inputs),
            )
            return json.loads(result.stdout)
        return runtime.task_start(task, branch, list(inputs))

    def record_quality(
        self,
        runtime: object,
        scope: str,
        *,
        native_header: bool = True,
    ) -> dict[str, object]:
        pending = runtime.begin("quality", scope=scope)
        self.result_file(
            runtime,
            pending,
            "pass",
            self.quality_data(runtime),
            report_text=(
                "QUALITY_VERDICT: pass\n"
                if native_header
                else "native quality report without a machine verdict\n"
            ),
        )
        return runtime.record("quality")

    def record_standards(self, runtime: object, scope: str) -> dict[str, object]:
        pending = runtime.begin("standards", scope=scope)
        self.result_file(
            runtime,
            pending,
            "pass",
            {"coverage": "complete"},
            report_text="STANDARDS_VERDICT: pass\n",
        )
        return runtime.record("standards")

    def record_review(self, runtime: object, scope: str) -> dict[str, object]:
        pending = runtime.begin("review", scope=scope)
        self.result_file(
            runtime,
            pending,
            "pass",
            self.review_data(runtime),
            report_text="REVIEW_VERDICT: pass\n",
        )
        return runtime.record("review")

    def record_task_owners(
        self,
        runtime: object,
        task: str = "T001",
        *,
        scope: str | None = None,
        include_standards: bool = True,
        include_review: bool = True,
    ) -> None:
        scope = f"task-{task}" if scope is None else scope
        self.record_quality(runtime, scope)
        if include_standards:
            self.record_standards(runtime, scope)
        if include_review:
            self.record_review(runtime, scope)

    def docs_record(
        self,
        runtime: object,
        *,
        required: bool = False,
        reason: str | None = "No public documentation changed by this task.",
    ) -> Path:
        path = runtime.local / "docs-refresh.json"
        value: dict[str, object] = {"required": required}
        if reason is not None:
            value["reason"] = reason
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        return path

    def gate_task(
        self,
        runtime: object,
        task: str,
        docs: Path,
        *,
        via_cli: bool = False,
    ) -> dict[str, object]:
        if via_cli:
            result = self.cli(
                "task-gate",
                runtime.run,
                task=task,
                file=runtime.relative(docs),
            )
            return json.loads(result.stdout)
        return runtime.task_gate(task, runtime.relative(docs))

    def mark_task(self, tasks: Path, task: str = "T001") -> None:
        raw = tasks.read_bytes()
        unchecked = f"- [ ] {task}".encode("utf-8")
        checked = f"- [x] {task}".encode("utf-8")
        self.assertEqual(raw.count(unchecked), 1)
        tasks.write_bytes(raw.replace(unchecked, checked, 1))

    def commit_exact(self, paths: list[str], message: str) -> str:
        self.git("add", "--", *paths)
        staged = self.git("diff", "--cached", "--name-only").stdout.splitlines()
        self.assertEqual(sorted(staged), sorted(paths))
        self.git("commit", "--quiet", "-m", message)
        return self.git("rev-parse", "HEAD").stdout.strip()

    def record_task(
        self,
        runtime: object,
        task: str,
        commit: str,
        *,
        via_cli: bool = False,
    ) -> dict[str, object]:
        if via_cli:
            result = self.cli(
                "task-record",
                runtime.run,
                task=task,
                commit=commit,
            )
            return json.loads(result.stdout)
        return runtime.task_record(task, commit)

    def close_task(
        self,
        runtime: object,
        feature: Path,
        *,
        task: str = "T001",
        source: str = "src/app.py",
        value: int = 2,
        via_cli: bool = False,
    ) -> tuple[str, dict[str, object]]:
        self.start_task(runtime, task, (source,), via_cli=via_cli)
        self.write(source, f"VALUE = {value}\n")
        self.record_task_owners(runtime, task)
        docs = self.docs_record(runtime)
        self.gate_task(runtime, task, docs, via_cli=via_cli)
        tasks = feature / "tasks.md"
        self.mark_task(tasks, task)
        commit = self.commit_exact(
            [source, self.relative(tasks)],
            f"{task} implement the reviewed change",
        )
        record = self.record_task(runtime, task, commit, via_cli=via_cli)
        return commit, record

    def test_successful_cli_closure_audits_multiple_tasks_and_preserves_historical_scopes(
        self,
    ) -> None:
        tasks = (
            "# Tasks\n\n"
            "- [ ] T001 Implement the first change\n"
            "- [ ] T002 Implement the second change\n"
        )
        runtime, feature = self.task_fixture("task-success", tasks)

        first_commit, first = self.close_task(
            runtime, feature, task="T001", value=2, via_cli=True
        )
        second_commit, second = self.close_task(
            runtime, feature, task="T002", value=3, via_cli=True
        )

        audited = json.loads(
            self.cli("require", runtime.run, kind="task-closure").stdout
        )
        self.assertEqual(audited["required"], "task-closure")
        self.assertTrue(audited["ready"])
        self.assertTrue(audited["audited"])
        self.assertEqual(audited["task_count"], 2)
        self.assertEqual(audited["task_ids"], ["T001", "T002"])
        self.assertEqual(first["status"], "committed")
        self.assertEqual(second["status"], "committed")
        self.assertEqual(first["commit"], first_commit)
        self.assertEqual(second["commit"], second_commit)
        self.assertNotEqual(first_commit, second_commit)

        first_record = runtime.local / "task-closures" / "T001.json"
        second_record = runtime.local / "task-closures" / "T002.json"
        first_history = json.loads(first_record.read_text(encoding="utf-8"))
        second_history = json.loads(second_record.read_text(encoding="utf-8"))
        for stage in ("quality", "standards", "review"):
            self.assertEqual(first_history["owners"][stage]["scope"], "task-T001")
            self.assertEqual(second_history["owners"][stage]["scope"], "task-T002")
        self.assertIsInstance(first_history["tasks_after_b64"], str)
        self.assertIn(b"- [x] T001", base64.b64decode(first_history["tasks_after_b64"]))
        self.assertEqual(set(first_history["closed_queue"]), {"mode", "oid"})
        self.assertEqual(runtime.load()["stages"]["review"]["scope"], "task-T002")
        self.assertEqual(
            (feature / "tasks.md").read_text(encoding="utf-8"),
            "# Tasks\n\n- [x] T001 Implement the first change\n- [x] T002 Implement the second change\n",
        )

    def test_audit_rejects_closed_task_acceptance_text_rewrite(self) -> None:
        runtime, feature = self.task_fixture("task-acceptance-rewrite")
        self.close_task(runtime, feature, task="T001", value=2)
        tasks = feature / "tasks.md"
        tasks.write_bytes(
            tasks.read_bytes().replace(
                b"Implement the change", b"Rewritten acceptance text", 1
            )
        )
        self.commit("rewrite closed task acceptance")
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "definitions/order"):
            runtime.audit_task_closure()

    def test_audit_rejects_removed_started_task_and_removed_historical_task(self) -> None:
        tasks_text = (
            "# Tasks\n\n"
            "- [ ] T001 First change\n"
            "- [ ] T002 Follow-up change\n"
        )
        for index, (run, removed) in enumerate(
            (
                ("task-remove-pending", "T002"),
                ("task-remove-old", "T001"),
            ),
            start=2,
        ):
            with self.subTest(removed=removed):
                runtime, feature = self.task_fixture(run, tasks_text)
                self.close_task(runtime, feature, task="T001", value=index)
                self.start_task(runtime, task="T002")
                tasks = feature / "tasks.md"
                if removed == "T002":
                    tasks.write_bytes(
                        tasks.read_bytes().replace(
                            b"- [ ] T002 Follow-up change", b"", 1
                        )
                    )
                else:
                    tasks.write_bytes(
                        tasks.read_bytes()
                        .replace(b"- [x] T001 First change", b"", 1)
                        .replace(
                            b"- [ ] T002 Follow-up change",
                            b"- [x] T002 Follow-up change",
                            1,
                        )
                    )
                pending = runtime.status()["pending_tasks"]
                self.assertEqual(pending[0]["task"], "T002")
                with self.assertRaisesRegex(
                    RUNTIME.ProtocolError, "removed historical or unfinished Task IDs"
                ) as blocked:
                    runtime.audit_task_closure()
                self.assertIn(removed, str(blocked.exception))

    def test_rename_out_of_allowed_scope_is_rejected(self) -> None:
        runtime, _ = self.task_fixture("task-rename-outside")
        self.start_task(runtime, inputs=("src/app.py",))
        self.git("mv", "src/app.py", "outside.py")
        docs = self.docs_record(runtime)
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "undeclared path"):
            runtime.task_gate("T001", runtime.relative(docs))

    def test_reverse_rename_with_space_unicode_and_quote_path_is_scoped(self) -> None:
        runtime, _ = self.task_fixture("task-rename-quoted")
        self.git("config", "core.quotePath", "true")
        self.start_task(runtime, inputs=("src",))
        self.git("mv", "src/app.py", "outside.py")
        unicode_path = "src/功能 file.py"
        self.git("mv", "outside.py", unicode_path)
        self.record_task_owners(runtime)
        docs = self.docs_record(runtime)
        gated = runtime.task_gate("T001", runtime.relative(docs))
        self.assertEqual(gated["gate"], "pass")
        self.assertEqual(runtime.load()["stages"]["review"]["scope"], "task-T001")

    def test_tracked_progress_written_before_owners_and_gate_is_allowed(self) -> None:
        runtime, feature = self.task_fixture("task-progress-before-gate")
        progress = self.write("progress.md", "# Progress\n\nInitial.\n")
        self.commit("bind tracked progress ledger")
        self.start_task(runtime, inputs=("src/app.py", "progress.md"))
        self.write("src/app.py", "VALUE = 2\n")
        progress.write_text("# Progress\n\nT001 reviewed progress.\n", encoding="utf-8")
        self.record_task_owners(runtime)
        docs = self.docs_record(runtime)
        gated = runtime.task_gate("T001", runtime.relative(docs))
        self.assertEqual(gated["gate"], "pass")
        self.mark_task(feature / "tasks.md")
        commit = self.commit_exact(
            ["src/app.py", "progress.md", self.relative(feature / "tasks.md")],
            "T001 record reviewed progress",
        )
        record = runtime.task_record("T001", commit)
        self.assertEqual(record["status"], "committed")
        self.assertTrue(runtime.audit_task_closure()["audited"])

    def test_audit_allows_a_completed_tail_task_append(self) -> None:
        runtime, feature = self.task_fixture("task-tail-append")
        self.close_task(runtime, feature, task="T001", value=2)
        tasks = feature / "tasks.md"
        tasks.write_bytes(
            tasks.read_bytes() + b"- [ ] T002 Appended follow-up\n"
        )
        self.commit("append a new tail task")
        self.close_task(runtime, feature, task="T002", value=3)
        audited = runtime.audit_task_closure()
        self.assertTrue(audited["audited"])
        self.assertEqual(audited["task_ids"], ["T001", "T002"])

    def test_tracked_tasks_queue_untracked_after_gate_is_rejected(self) -> None:
        runtime, feature = self.task_fixture("task-untrack-queue")
        tasks = feature / "tasks.md"
        tasks_relative = self.relative(tasks)
        self.write(".gitignore", f"/{tasks_relative}\n")
        self.commit("ignore the local task queue after explicit untracking")
        self.assertEqual(
            self.git("ls-files", "--error-unmatch", tasks_relative).returncode, 0
        )

        self.start_task(runtime)
        self.write("src/app.py", "VALUE = 2\n")
        self.record_task_owners(runtime)
        docs = self.docs_record(runtime)
        runtime.task_gate("T001", runtime.relative(docs))
        self.mark_task(tasks)
        self.git("rm", "--cached", "--", tasks_relative)
        self.assertTrue(tasks.is_file())
        self.assertEqual(
            self.git(
                "check-ignore", "--quiet", "--no-index", "--", tasks_relative, check=False
            ).returncode,
            0,
        )
        self.git("add", "--", "src/app.py")
        staged = self.git("diff", "--cached", "--name-only").stdout.splitlines()
        self.assertEqual(sorted(staged), sorted(["src/app.py", tasks_relative]))
        self.git("commit", "--quiet", "-m", "T001 untrack the task queue")
        head = self.git("rev-parse", "HEAD").stdout.strip()
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "tracked task queue"):
            runtime.task_record("T001", head)

    def test_tasks_queue_line_endings_survive_git_attributes_and_autocrlf(self) -> None:
        variants = (
            ("crlf-attr", b"\r\n", "true"),
            ("crlf-autocrlf", b"\r\n", "true"),
            ("lf-autocrlf", b"\n", "true"),
        )
        for index, (label, newline, autocrlf) in enumerate(variants, start=2):
            with self.subTest(label=label):
                runtime, feature = self.task_fixture(f"task-line-endings-{label}")
                tasks = feature / "tasks.md"
                tasks_relative = self.relative(tasks)
                self.git("config", "core.autocrlf", autocrlf)
                attributes = self.root / ".gitattributes"
                existing_attributes = (
                    attributes.read_text(encoding="utf-8")
                    if attributes.exists()
                    else ""
                )
                self.write(
                    ".gitattributes",
                    existing_attributes + f"/{tasks_relative} -text\n",
                )
                tasks.write_bytes(
                    tasks.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", newline)
                )
                self.git("add", "--", ".gitattributes", tasks_relative)
                self.git("commit", "--quiet", "-m", f"bind {label} task queue policy")
                self.assertIn(
                    "unset",
                    self.git("check-attr", "text", "--", tasks_relative).stdout,
                )
                self.start_task(runtime)
                self.write("src/app.py", f"VALUE = {index}\n")
                self.record_task_owners(runtime)
                docs = self.docs_record(runtime)
                runtime.task_gate("T001", runtime.relative(docs))
                self.mark_task(tasks)
                commit = self.commit_exact(
                    ["src/app.py", tasks_relative],
                    f"T001 close {label} task",
                )
                record = runtime.task_record("T001", commit)
                self.assertEqual(record["status"], "committed")
                self.assertTrue(runtime.audit_task_closure()["audited"])

    def test_dependency_order_allows_t002_commit_before_dependent_t001(self) -> None:
        tasks = (
            "# Tasks\n\n"
            "- [ ] T001 Integration change (Depends on: T002)\n"
            "- [ ] T002 Prerequisite change\n"
        )
        runtime, feature = self.task_fixture("task-dependency-order", tasks)
        second_commit, _ = self.close_task(
            runtime, feature, task="T002", value=2
        )
        first_commit, _ = self.close_task(
            runtime, feature, task="T001", value=3
        )
        self.assertNotEqual(first_commit, second_commit)
        audited = runtime.audit_task_closure()
        self.assertEqual(audited["task_ids"], ["T001", "T002"])
        self.assertTrue(audited["audited"])

    def test_forged_checked_only_queue_and_duplicate_task_ids_are_rejected(self) -> None:
        checked_runtime, _ = self.task_fixture(
            "task-forged-checked",
            "# Tasks\n\n- [X] T001 Pretend this task was closed\n",
        )
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "closure record|committed closure"):
            checked_runtime.audit_task_closure()
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "unchecked"):
            self.start_task(checked_runtime)

        duplicate_runtime, _ = self.task_fixture(
            "task-duplicate-id",
            "# Tasks\n\n"
            "- [ ] T001 First occurrence\n"
            "- [ ] T001 Duplicate occurrence\n",
        )
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "unique"):
            self.start_task(duplicate_runtime)

    def test_task_start_requires_the_actual_branch_and_gate_rechecks_branch(self) -> None:
        runtime, _ = self.task_fixture("task-branch")
        actual = self.actual_branch()
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "branch"):
            self.start_task(runtime, branch=actual + "-wrong")

        self.start_task(runtime)
        self.git("checkout", "--quiet", "-b", "task-branch-mismatch")
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "branch"):
            runtime.task_gate("T001", "missing-docs.json")

    def test_task_gate_requires_a_clean_single_task_sequence(self) -> None:
        runtime, feature = self.task_fixture("task-no-gate")
        self.start_task(runtime)
        self.write("src/app.py", "VALUE = 2\n")
        self.record_task_owners(runtime)
        head = self.git("rev-parse", "HEAD").stdout.strip()
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "task-gate"):
            runtime.task_record("T001", head)
        self.assertEqual(
            json.loads(
                (runtime.local / "task-closures" / "T001.json").read_text(
                    encoding="utf-8"
                )
            )["status"],
            "started",
        )
        self.assertTrue(feature.joinpath("tasks.md").is_file())

    def test_task_gate_rejects_missing_standards_and_final_outgoing_review_substitution(
        self,
    ) -> None:
        missing_runtime, _ = self.task_fixture("task-missing-standards")
        self.start_task(missing_runtime)
        self.write("src/app.py", "VALUE = 2\n")
        self.record_task_owners(
            missing_runtime, include_standards=False, include_review=False
        )
        missing_docs = self.docs_record(missing_runtime)
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "standards"):
            missing_runtime.task_gate("T001", missing_runtime.relative(missing_docs))

        outgoing_runtime, _ = self.task_fixture("task-outgoing-review")
        self.start_task(outgoing_runtime)
        self.write("src/app.py", "VALUE = 2\n")
        self.record_task_owners(outgoing_runtime, scope="outgoing-diff")
        outgoing_docs = self.docs_record(outgoing_runtime)
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "task-T001"):
            outgoing_runtime.task_gate(
                "T001", outgoing_runtime.relative(outgoing_docs)
            )

    def test_task_gate_requires_explicit_native_owner_verdict_headers(self) -> None:
        runtime, _ = self.task_fixture("task-missing-header")
        self.start_task(runtime)
        self.write("src/app.py", "VALUE = 2\n")
        self.record_quality(runtime, "task-T001", native_header=False)
        self.record_standards(runtime, "task-T001")
        self.record_review(runtime, "task-T001")
        docs = self.docs_record(runtime)
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "explicit native quality pass header"):
            runtime.task_gate("T001", runtime.relative(docs))

    def test_docs_applicability_requires_an_in_runtime_reason_for_not_required(self) -> None:
        runtime, _ = self.task_fixture("task-docs")
        self.start_task(runtime)
        self.write("src/app.py", "VALUE = 2\n")
        self.record_task_owners(runtime)
        docs = self.docs_record(runtime, reason=None)
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "applicability reason"):
            runtime.task_gate("T001", runtime.relative(docs))

        docs.write_text(
            json.dumps(
                {"required": False, "reason": "No public documentation changed."}
            )
            + "\n",
            encoding="utf-8",
        )
        gated = runtime.task_gate("T001", runtime.relative(docs))
        self.assertEqual(gated["gate"], "pass")
        self.assertEqual(
            json.loads(
                (runtime.local / "docs-refresh.json").read_text(encoding="utf-8")
            ),
            {"required": False, "reason": "No public documentation changed."},
        )

    def test_missing_or_tampered_native_owner_report_blocks_task_gate(self) -> None:
        for run, tamper in (
            ("task-missing-report", "missing"),
            ("task-tampered-report", "tampered"),
        ):
            with self.subTest(tamper=tamper):
                runtime, _ = self.task_fixture(run)
                self.start_task(runtime)
                self.write("src/app.py", "VALUE = 2\n")
                self.record_task_owners(runtime)
                report_ref = runtime.load()["stages"]["quality"]["report"]
                report = self.root / report_ref["path"]
                if tamper == "missing":
                    report.unlink()
                else:
                    report.write_text("QUALITY_VERDICT: pass\nchanged\n", encoding="utf-8")
                docs = self.docs_record(runtime)
                with self.assertRaises(RUNTIME.ProtocolError):
                    runtime.task_gate("T001", runtime.relative(docs))

    def test_unrelated_staged_path_is_not_in_the_task_allowed_paths(self) -> None:
        runtime, _ = self.task_fixture("task-unrelated-staged")
        self.start_task(runtime, inputs=("src/app.py",))
        self.write("src/app.py", "VALUE = 2\n")
        self.write("README.md", "unrelated task edit\n")
        self.git("add", "--", "README.md")
        docs = self.docs_record(runtime)
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "undeclared path"):
            runtime.task_gate("T001", runtime.relative(docs))

    def test_reviewed_code_changed_after_gate_is_rejected_even_in_task_commit(self) -> None:
        runtime, feature = self.task_fixture("task-code-after-gate")
        self.start_task(runtime)
        self.write("src/app.py", "VALUE = 2\n")
        self.record_task_owners(runtime)
        docs = self.docs_record(runtime)
        runtime.task_gate("T001", runtime.relative(docs))
        self.mark_task(feature / "tasks.md")
        self.write("src/app.py", "VALUE = 99\n")
        self.commit_exact(
            ["src/app.py", self.relative(feature / "tasks.md")],
            "T001 includes an unreviewed edit",
        )
        head = self.git("rev-parse", "HEAD").stdout.strip()
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "changed after the task gate"):
            runtime.task_record("T001", head)

    def test_changed_other_task_checkbox_is_rejected(self) -> None:
        tasks = (
            "# Tasks\n\n"
            "- [ ] T001 First change\n"
            "- [ ] T002 Other change\n"
        )
        runtime, feature = self.task_fixture("task-other-checkbox", tasks)
        self.start_task(runtime)
        self.write("src/app.py", "VALUE = 2\n")
        self.record_task_owners(runtime)
        docs = self.docs_record(runtime)
        runtime.task_gate("T001", runtime.relative(docs))
        self.mark_task(feature / "tasks.md", "T001")
        self.mark_task(feature / "tasks.md", "T002")
        head = self.commit_exact(
            ["src/app.py", self.relative(feature / "tasks.md")],
            "T001 changes two task checkboxes",
        )
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "another checkbox"):
            runtime.task_record("T001", head)

    def test_wrong_and_nonancestor_commit_objects_are_rejected(self) -> None:
        runtime, _ = self.task_fixture("task-wrong-commit")
        branch = self.actual_branch()
        self.git("checkout", "--quiet", "-b", "task-side-commit")
        self.git("commit", "--quiet", "--allow-empty", "-m", "side commit")
        side_commit = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("checkout", "--quiet", branch)

        self.start_task(runtime)
        self.write("src/app.py", "VALUE = 2\n")
        self.record_task_owners(runtime)
        docs = self.docs_record(runtime)
        runtime.task_gate("T001", runtime.relative(docs))
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "exact task commit"):
            runtime.task_record("T001", side_commit)

    def test_task_commit_message_must_identify_the_exact_task_id(self) -> None:
        runtime, feature = self.task_fixture("task-wrong-message")
        self.start_task(runtime)
        self.write("src/app.py", "VALUE = 2\n")
        self.record_task_owners(runtime)
        docs = self.docs_record(runtime)
        runtime.task_gate("T001", runtime.relative(docs))
        self.mark_task(feature / "tasks.md")
        commit = self.commit_exact(
            ["src/app.py", self.relative(feature / "tasks.md")],
            "Implement the reviewed change without its identifier",
        )
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "exact Task ID"):
            runtime.task_record("T001", commit)

    def test_merge_commit_is_not_a_linear_task_commit(self) -> None:
        runtime, feature = self.task_fixture("task-merge-commit")
        branch = self.actual_branch()
        prehead = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("checkout", "--quiet", "-b", "task-merge-side")
        self.git("commit", "--quiet", "--allow-empty", "-m", "parallel side")
        side_commit = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("checkout", "--quiet", branch)

        self.start_task(runtime)
        self.write("src/app.py", "VALUE = 2\n")
        self.record_task_owners(runtime)
        docs = self.docs_record(runtime)
        runtime.task_gate("T001", runtime.relative(docs))
        self.mark_task(feature / "tasks.md")
        self.git("add", "--", "src/app.py", self.relative(feature / "tasks.md"))
        tree = self.git("write-tree").stdout.strip()
        merge_commit = self.git(
            "commit-tree",
            tree,
            "-p",
            prehead,
            "-p",
            side_commit,
            "-m",
            "T001 merge commit",
        ).stdout.strip()
        self.git("update-ref", f"refs/heads/{branch}", merge_commit)
        self.git("reset", "--quiet", "--mixed", merge_commit)
        with self.assertRaisesRegex(RUNTIME.ProtocolError, "sole parent"):
            runtime.task_record("T001", merge_commit)


if __name__ == "__main__":
    unittest.main()
