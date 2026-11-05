#!/usr/bin/env python3
"""Probe the installed Delivery runtime helper without importing repository code."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


RUNTIME_RELATIVE = Path(".specify/extensions/delivery/scripts/delivery_runtime.py")
CONFIG_RELATIVE = Path(".specify/extensions/delivery/delivery-config.yml")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def relative(project: Path, path: Path) -> str:
    return path.relative_to(project).as_posix()


def reference(project: Path, path: Path) -> dict[str, str]:
    return {"path": relative(project, path), "sha256": digest(path.read_bytes())}


def invoke(
    command: list[str],
    cwd: Path,
    *,
    expected: int | None = 0,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    if expected is not None and result.returncode != expected:
        raise RuntimeError(
            "command failed with "
            f"{result.returncode} (expected {expected}): {' '.join(command)}\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def git(
    project: Path,
    *arguments: str,
    expected: int | None = 0,
) -> subprocess.CompletedProcess[str]:
    return invoke(["git", "-C", str(project), *arguments], project, expected=expected)


def runtime_cli(
    helper: Path,
    project: Path,
    operation: str,
    *arguments: str,
    expected: int | None = 0,
) -> subprocess.CompletedProcess[str]:
    return invoke(
        [
            sys.executable,
            str(helper),
            operation,
            "--root",
            str(project),
            *arguments,
        ],
        project,
        expected=expected,
    )


def json_output(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"runtime helper did not return JSON: {result.stdout!r}") from exc
    if not isinstance(value, dict):
        raise RuntimeError("runtime helper returned a non-object JSON value")
    return value


def assert_config_unchanged(config: Path, original: bytes) -> None:
    if config.read_bytes() != original:
        raise RuntimeError("installed runtime changed the project-owned Delivery configuration")


def commit_if_needed(project: Path, message: str) -> None:
    head = git(project, "rev-parse", "--verify", "HEAD", expected=None)
    status = git(project, "status", "--porcelain", "--untracked-files=all").stdout
    if head.returncode != 0 or status:
        git(project, "add", "--all")
        git(project, "commit", "--quiet", "-m", message)


def ensure_git_fixture(project: Path) -> tuple[Path, bytes]:
    probe = git(project, "rev-parse", "--show-toplevel", expected=None)
    if probe.returncode != 0:
        git(project, "init", "--quiet")
    git(project, "config", "user.email", "delivery-runtime-install@example.invalid")
    git(project, "config", "user.name", "Delivery Runtime Install")

    source = project / "src" / "delivery_runtime_install_smoke.py"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    commit_if_needed(project, "runtime install smoke baseline")
    return source, source.read_bytes()


def write_owner_result(
    helper: Path,
    project: Path,
    pending: dict[str, Any],
    data: dict[str, Any],
    report_text: str,
) -> Path:
    local = project / ".specify" / "delivery" / pending["delivery_run"] / "runtime"
    stage = pending["stage"]
    report = local / f"native-{stage}-report.txt"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(report_text, encoding="utf-8")
    data_path = local / f"data-{stage}.json"
    data_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    result_path = local / f"result-{stage}.json"
    generated = json_output(
        runtime_cli(
            helper,
            project,
            "owner-result",
            "--run",
            pending["delivery_run"],
            "--stage",
            stage,
            "--report",
            relative(project, report),
            "--data",
            relative(project, data_path),
            "--verdict",
            "pass",
            "--output",
            relative(project, result_path),
            "--json",
        )
    )
    if generated.get("generated", {}).get("ticket") != pending["ticket"]:
        raise RuntimeError("installed owner-result helper changed the pending ticket")
    return result_path


def run_planning_checkpoint_smoke(
    helper: Path,
    project: Path,
    config: Path,
    config_before: bytes,
) -> None:
    run = "installed-feature-checkpoint"
    feature = project / ".specify" / "features" / run
    feature.mkdir(parents=True, exist_ok=True)
    (feature / "spec.md").write_text("# Spec\n\nInstalled helper checkpoint smoke.\n", encoding="utf-8")
    (feature / "plan.md").write_text("# Plan\n\nUse the installed helper.\n", encoding="utf-8")
    (feature / "tasks.md").write_text("# Tasks\n\n- [X] T1 Verify the installed checkpoint\n", encoding="utf-8")
    commit_if_needed(project, "checkpoint smoke planning fixture")

    initialized = json_output(
        runtime_cli(helper, project, "init", "--run", run, "--lane", "feature", "--json")
    )
    if initialized.get("delivery_run") != run or initialized.get("lane") != "feature":
        raise RuntimeError("installed helper Feature init returned the wrong run identity")

    bindings = json_output(
        runtime_cli(
            helper,
            project,
            "bind",
            "--run",
            run,
            "--feature-dir",
            relative(project, feature),
            "--json",
        )
    )
    approved = [bindings[name] for name in ("spec", "plan", "tasks")]

    analyze = json_output(
        runtime_cli(helper, project, "begin", "--run", run, "--stage", "analyze", "--json")
    )
    write_owner_result(
        helper,
        project,
        analyze,
        {"coverage": "complete"},
        "ANALYZE_VERDICT: pass\ninstalled helper analyze report\n",
    )
    recorded_analyze = json_output(
        runtime_cli(helper, project, "record", "--run", run, "--stage", "analyze", "--json")
    )

    checkpoint = json_output(
        runtime_cli(
            helper,
            project,
            "begin",
            "--run",
            run,
            "--stage",
            "checkpoint",
            "--scope",
            "initial",
            "--json",
        )
    )
    local = project / ".specify" / "delivery" / run / "runtime"
    manifest = local / f"planning-inputs-{checkpoint['ticket']}.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "delivery_run": run,
                "lane": "feature",
                "authorization": "installed helper planning checkpoint smoke",
                "paths": [
                    {"path": path, "source_owner": "core"} for path in approved
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    branch = git(project, "branch", "--show-current").stdout.strip()
    write_owner_result(
        helper,
        project,
        checkpoint,
        {
            "planning_stage": "initial",
            "approved_paths": approved,
            "branch": branch,
            "base_head": checkpoint["snapshot"]["head"],
            "planning_commit": "none",
            "authorization": "installed helper planning checkpoint smoke",
            "analyze_fingerprint": recorded_analyze["output_fingerprint"],
            "content_fingerprint": checkpoint["snapshot"]["fingerprint"],
        },
        "CHECKPOINT_VERDICT: pass\nSD_CORE_HANDOFF: PASS\ninstalled helper checkpoint report\n",
    )
    json_output(
        runtime_cli(helper, project, "record", "--run", run, "--stage", "checkpoint", "--json")
    )
    planning = json_output(
        runtime_cli(helper, project, "require", "--run", run, "--kind", "planning", "--json")
    )
    if planning != {"required": "planning", "ready": True}:
        raise RuntimeError("installed helper did not accept the native planning checkpoint")
    closure = runtime_cli(
        helper,
        project,
        "require",
        "--run",
        run,
        "--kind",
        "task-closure",
        "--json",
        expected=1,
    )
    if not closure.stderr.strip():
        raise RuntimeError(
            "installed helper accepted a checked-only Feature without task closure credentials"
        )
    assert_config_unchanged(config, config_before)


def run_lightweight_quality_smoke(
    helper: Path,
    project: Path,
    source: Path,
    source_before: bytes,
    config: Path,
    config_before: bytes,
) -> None:
    run = "installed-lightweight-runtime"
    initialized = json_output(
        runtime_cli(helper, project, "init", "--run", run, "--lane", "lightweight", "--json")
    )
    if initialized.get("delivery_run") != run or initialized.get("lane") != "lightweight":
        raise RuntimeError("installed helper lightweight init returned the wrong run identity")
    assert_config_unchanged(config, config_before)

    pending = json_output(
        runtime_cli(helper, project, "begin", "--run", run, "--stage", "quality", "--json")
    )
    pending_input = project / ".specify" / "delivery" / run / "runtime" / "input-quality.json"
    pending_before = json.loads(pending_input.read_text(encoding="utf-8"))
    if pending_before.get("ticket") != pending.get("ticket"):
        raise RuntimeError("installed helper quality input did not preserve its original ticket")

    status = json_output(runtime_cli(helper, project, "status", "--run", run, "--json"))
    resumed = json_output(runtime_cli(helper, project, "resume", "--run", run, "--json"))
    if status != resumed or status.get("delivery_run") != run:
        raise RuntimeError("installed helper status/resume changed the run identity")
    if status.get("pending_stages") != ["quality"]:
        raise RuntimeError("installed helper status did not expose the pending quality ticket")

    repeated = json_output(
        runtime_cli(
            helper,
            project,
            "begin",
            "--run",
            run,
            "--stage",
            "quality",
            "--json",
        )
    )
    pending_after = json.loads(pending_input.read_text(encoding="utf-8"))
    if (
        repeated.get("ticket") != pending_before.get("ticket")
        or pending_after.get("ticket") != pending_before.get("ticket")
    ):
        raise RuntimeError("a repeated quality begin reset the pending owner ticket")
    resumed_after = json_output(runtime_cli(helper, project, "resume", "--run", run, "--json"))
    if resumed_after != status:
        raise RuntimeError("resuming the installed helper changed a pending owner identity")

    local = project / ".specify" / "delivery" / run / "runtime"
    check = local / "checks" / "fake-native-check.txt"
    check.parent.mkdir(parents=True, exist_ok=True)
    check.write_text("fake-native-check: exit 0\n", encoding="utf-8")
    data = {
        "checks": [
            {
                "command": "fake-native-check",
                "exit_code": 0,
                "evidence": reference(project, check),
            }
        ]
    }
    write_owner_result(
        helper,
        project,
        pending,
        data,
        "QUALITY_VERDICT: pass\ninstalled helper quality report\n",
    )
    recorded = json_output(
        runtime_cli(helper, project, "record", "--run", run, "--stage", "quality", "--json")
    )
    if recorded.get("verdict") != "pass" or recorded.get("input_fingerprint") != pending.get("input_fingerprint"):
        raise RuntimeError("installed helper recorded a malformed quality identity")

    needs = runtime_cli(helper, project, "needs", "--run", run, "--kind", "quality")
    if needs.stdout.strip() != "false":
        raise RuntimeError("installed helper did not reuse the SHA-bound passing quality result")

    original_check = check.read_bytes()
    check.write_text("tampered native check\n", encoding="utf-8")
    tampered = runtime_cli(
        helper,
        project,
        "needs",
        "--run",
        run,
        "--kind",
        "quality",
        expected=1,
    )
    if not tampered.stderr.strip():
        raise RuntimeError("installed helper did not reject tampered SHA-bound check evidence")
    check.write_bytes(original_check)
    restored = runtime_cli(helper, project, "needs", "--run", run, "--kind", "quality")
    if restored.stdout.strip() != "false":
        raise RuntimeError("restoring the original SHA-bound check did not restore the quality pass")

    source.write_text("VALUE = 2\n", encoding="utf-8")
    changed = runtime_cli(helper, project, "needs", "--run", run, "--kind", "quality")
    if changed.stdout.strip() != "true":
        raise RuntimeError("installed helper did not invalidate Quality after an actual source mutation")
    source.write_bytes(source_before)
    final = runtime_cli(helper, project, "needs", "--run", run, "--kind", "quality")
    if final.stdout.strip() != "false":
        raise RuntimeError("restoring the actual source did not restore the current quality identity")
    assert_config_unchanged(config, config_before)


def run_runtime_install_smoke(project: Path, helper: Path) -> None:
    project = project.resolve()
    helper = helper.resolve()
    if not project.is_dir() or not helper.is_file():
        raise RuntimeError(f"installed runtime fixture is missing: project={project}, helper={helper}")
    if helper != (project / RUNTIME_RELATIVE).resolve():
        raise RuntimeError("runtime smoke must target the installed Delivery helper inside the project")

    config = project / CONFIG_RELATIVE
    config_before = config.read_bytes() if config.is_file() else b""
    source, source_before = ensure_git_fixture(project)
    run_planning_checkpoint_smoke(helper, project, config, config_before)
    run_lightweight_quality_smoke(
        helper,
        project,
        source,
        source_before,
        config,
        config_before,
    )
    if config.is_file():
        assert_config_unchanged(config, config_before)
    print("Installed runtime init/resume, planning checkpoint, SHA-bound Quality, and freshness smoke passed.", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--helper", type=Path)
    args = parser.parse_args()
    helper = args.helper or (args.project / RUNTIME_RELATIVE)
    try:
        run_runtime_install_smoke(args.project, helper)
    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Installed runtime smoke failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
