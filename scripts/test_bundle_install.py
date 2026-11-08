#!/usr/bin/env python3
"""Install the built Bundle from local release-style catalogs in a clean project."""

from __future__ import annotations

import argparse
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import zipfile


ROOT = Path(__file__).resolve().parents[1]
TAG_URL = re.compile(
    r"https://raw\.githubusercontent\.com/YanZhiwei/speckit-delivery/v[^/]+"
)
ASSET_URL = re.compile(
    r"https://github\.com/YanZhiwei/speckit-delivery/releases/download/v[^/]+/"
)


def check_delivery_install(
    project: Path, dist: Path, version: str, integration: str
) -> None:
    """Verify resources and prompt contents survive packaging and rendering."""
    resources = {
        "delivery": (
            "commands/speckit.delivery.route.md",
            "commands/speckit.delivery.doctor.md",
            "commands/speckit.delivery.explore.md",
            "commands/speckit.delivery.method.md",
            "commands/speckit.delivery.slice.md",
            "commands/speckit.delivery.review-fix.md",
            "commands/speckit.delivery.handoff.md",
            "commands/speckit.delivery.close.md",
            "commands/speckit.delivery.context.md",
            "templates/exploration.md",
            "templates/slices.md",
            "templates/bugfix-review-repair.md",
            "templates/repair-docs.md",
            "templates/method-adapter.md",
            "templates/method-design.md",
            "templates/method-diagnose.md",
            "templates/method-review.md",
            "templates/pull-request.md",
            "templates/runtime.md",
            "templates/core-adapter.md",
            "scripts/delivery_runtime.py",
            "scripts/delivery_tasks.py",
            "scripts/delivery_outcome.py",
        ),
        "review": ("commands/speckit.review.run.md", "commands/speckit.review.standards.md", "templates/reviewer.md"),
        "quality": (
            "commands/speckit.quality.brief.md",
            "commands/speckit.quality.check.md",
            "config-template.yml",
        ),
        "evidence": ("commands/speckit.evidence.collect.md",),
        "ralph": (
            "commands/speckit.ralph.run.md",
            "templates/slice-execution.md",
        ),
        "docs-sync": (
            "commands/speckit.docs-sync.run.md",
            "commands/speckit.docs-sync.package-readme.md",
            "templates/package-readme.md",
            "templates/project-readme.md",
            "scripts/readme_structure.py",
            "config-template.yml",
        ),
    }
    for extension_id, relatives in resources.items():
        with zipfile.ZipFile(dist / f"{extension_id}-{version}.zip") as archive:
            for relative in relatives:
                expected = (ROOT / "extensions" / extension_id / relative).read_bytes()
                if archive.read(relative) != expected:
                    raise RuntimeError(f"packaged {extension_id} resource differs: {relative}")
                installed = project / ".specify" / "extensions" / extension_id / relative
                if not installed.is_file() or installed.read_bytes() != expected:
                    raise RuntimeError(f"installed {extension_id} resource missing/stale: {relative}")

    for name, marker in (
        ("speckit.delivery.explore", "EXPLORATION_VERDICT"),
        ("speckit.delivery.method", "METHOD_STATUS"),
        ("speckit.delivery.slice", "SLICE_PLAN_VERDICT"),
        ("speckit.delivery.handoff", "PR_BODY_PATH"),
        ("speckit.delivery.handoff", "before/after screenshots"),
        ("speckit.delivery.handoff", "### Bugfix repair history"),
        ("speckit.delivery.close", "DELIVERY_STATUS"),
        ("speckit.docs-sync.package-readme", "PACKAGE_README_VERDICT"),
        ("speckit.docs-sync.package-readme", "README_STRUCTURE"),
        ("speckit.review.run", "REVIEW_VERDICT"),
        ("speckit.delivery.review-fix", "REVIEW_FIX_STATUS"),
        ("speckit.ralph.run", "REVIEW_VERDICT=pass"),
        ("speckit.ralph.run", "ALL_TASKS_DONE"),
        ("speckit.quality.brief", "QUALITY_BRIEF"),
        ("speckit.quality.check", "CHECK_RECEIPTS:"),
        ("speckit.review.standards", "POLICY_FINGERPRINT:"),
        ("speckit.evidence.collect", "project's explicit output-language convention first"),
        ("speckit.evidence.collect", "paths, commands, hashes, and original logs/receipts unchanged"),
    ):
        if integration == "codex":
            rendered = list(project.glob(f".agents/skills/{name.replace('.', '-')}/SKILL.md"))
        else:
            rendered = list(project.glob(f".opencode/**/{name}.md"))
        if not rendered or not any(
            marker in path.read_text(encoding="utf-8") for path in rendered
        ):
            raise RuntimeError(f"{integration} command missing/stale: {name}")

    # Doctor checks a resource owned by Review. The renderer rewrites bare
    # extension-relative paths to the owning extension, so verify the rendered
    # result names Review and resolves to the installed template.
    if integration == "codex":
        doctor_commands = list(
            project.glob(".agents/skills/speckit-delivery-doctor/SKILL.md")
        )
    else:
        doctor_commands = list(
            project.glob(".opencode/**/speckit.delivery.doctor.md")
        )
    if not doctor_commands:
        raise RuntimeError(f"{integration} command missing: speckit.delivery.doctor")
    reviewer_template = project / ".specify/extensions/review/templates/reviewer.md"
    reviewer_path = ".specify/extensions/review/templates/reviewer.md"
    wrong_path = ".specify/extensions/delivery/templates/reviewer.md"
    if not reviewer_template.is_file():
        raise RuntimeError("installed review templates/reviewer.md is missing")
    for command in doctor_commands:
        text = command.read_text(encoding="utf-8")
        if reviewer_path not in text or wrong_path in text:
            raise RuntimeError(
                f"{integration} Doctor has a stale Reviewer path: {command}"
            )

    installed_workflows = project / ".specify" / "workflows"
    candidates = [
        *installed_workflows.rglob("*.yml"),
        *installed_workflows.rglob("*.yaml"),
    ]
    for workflow_id in ("feature-delivery", "bugfix-delivery", "lightweight-delivery"):
        expected = (ROOT / "workflows" / workflow_id / "workflow.yml").read_text(
            encoding="utf-8"
        )
        # The CLI chooses installed filenames; compare newline-normalized
        # source contents rather than coupling this check to a naming convention.
        if not any(path.read_text(encoding="utf-8") == expected for path in candidates):
            raise RuntimeError(f"installed workflow missing/stale: {workflow_id}")
    print("Explore/Review/Ralph resources, rendering, and all workflows verified.", flush=True)


def check_router_alias(project: Path, integration: str) -> tuple[Path, Path]:
    """Require the installed alias to share the router body and installer owner."""
    if integration == "codex":
        root = project / ".agents/skills"
        router = root / "speckit-delivery-route/SKILL.md"
        alias = root / "speckit-sd/SKILL.md"
    else:
        root = project / ".opencode/commands"
        router = root / "speckit.delivery.route.md"
        alias = root / "sd.md"
    if not router.is_file() or not alias.is_file():
        raise RuntimeError(f"{integration} delivery router or sd alias was not installed")
    router_text = router.read_text(encoding="utf-8")
    alias_text = alias.read_text(encoding="utf-8")
    heading = "# Spec Kit Delivery Route\n"
    if heading not in router_text or heading not in alias_text:
        raise RuntimeError(f"{integration} sd alias does not contain the installed router")
    if router_text.split(heading, 1)[1].strip() != alias_text.split(heading, 1)[1].strip():
        raise RuntimeError(f"{integration} sd alias differs from the installed router")
    if "$ARGUMENTS" not in alias_text:
        raise RuntimeError(f"{integration} sd alias lost its request argument")
    runtime_reference = ".specify/extensions/delivery/scripts/delivery_runtime.py"
    if runtime_reference not in router_text or runtime_reference not in alias_text:
        raise RuntimeError(f"{integration} route/alias lost its installed runtime helper reference")
    source_route = (ROOT / "extensions/delivery/commands/speckit.delivery.route.md").read_text(
        encoding="utf-8"
    )
    closure_markers = (
        "task-closure",
        "task_closure",
        "audit_task_closure",
        "all_tasks_done",
        "all-tasks-done",
        "task closure",
    )
    source_closure_markers = {
        marker.lower()
        for marker in closure_markers
        if marker.lower() in source_route.lower()
    }
    if source_closure_markers and not any(
        marker in alias_text.lower() for marker in source_closure_markers
    ):
        raise RuntimeError(
            f"{integration} route/alias lost the installed task-closure guard reference"
        )
    if integration == "codex":
        if not re.search(r"^name: speckit-sd$", alias_text, re.MULTILINE):
            raise RuntimeError("Codex alias skill has the wrong name")
    elif router_text != alias_text:
        raise RuntimeError("OpenCode sd alias must match the router command exactly")
    registry = json.loads((project / ".specify/extensions/.registry").read_text(encoding="utf-8"))
    registered = registry["extensions"]["delivery"]["registered_commands"].get(integration, [])
    if not {"speckit.delivery.route", "sd"}.issubset(registered):
        raise RuntimeError(f"{integration} registry does not assign both router names to Delivery")
    print(f"{integration} sd alias, request input, and Delivery ownership verified.", flush=True)
    return router, alias


def check_controlled_alias_upgrade(
    project: Path,
    specify: str,
    integration: str,
    original_config: bytes,
    config_path: Path,
) -> None:
    """Exercise adoption of an old custom sd shim through the normal update path."""
    _router, alias = check_router_alias(project, integration)
    legacy_marker = "# legacy custom sd forwarding shim"
    if integration == "codex":
        legacy = (
            "---\n"
            "name: speckit-sd\n"
            "description: Legacy local Delivery shortcut\n"
            "---\n\n"
            f"{legacy_marker}\n"
            "Delegate to the old Delivery route with the request below.\n"
            "$ARGUMENTS\n"
        )
    else:
        legacy = (
            "---\n"
            "description: Legacy local Delivery shortcut\n"
            "---\n\n"
            f"{legacy_marker}\n"
            "Delegate to the old Delivery route with the request below.\n"
            "$ARGUMENTS\n"
        )
    alias.write_text(legacy, encoding="utf-8")

    registry_path = project / ".specify/extensions/.registry"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registered = registry["extensions"]["delivery"]["registered_commands"].get(integration, [])
    if not isinstance(registered, list):
        raise RuntimeError(f"{integration} registry has no command ownership list to upgrade")
    registry["extensions"]["delivery"]["registered_commands"][integration] = [
        name for name in registered if name != "sd"
    ]
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    if legacy_marker not in alias.read_text(encoding="utf-8"):
        raise RuntimeError(f"{integration} legacy alias fixture was not written")

    run(
        [specify, "bundle", "update", "speckit-delivery", "--integration", integration],
        project,
    )
    check_router_alias(project, integration)
    if legacy_marker in alias.read_text(encoding="utf-8"):
        raise RuntimeError(f"{integration} controlled Bundle update kept the old sd forwarding shim")
    if config_path.read_bytes() != original_config:
        raise RuntimeError("Controlled Bundle update overwrote the project configuration")
    print(f"{integration} controlled update adopted the Delivery-owned sd alias.", flush=True)


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    print(">", " ".join(command), flush=True)
    result = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, encoding="utf-8"
    )
    if result.stdout:
        print(result.stdout[-4000:], flush=True)
    if result.stderr:
        print(result.stderr[-2000:], flush=True)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}")
    return result


def version_from_bundle() -> str:
    text = (ROOT / "bundle" / "bundle.yml").read_text(encoding="utf-8")
    match = re.search(r"^\s{2}version:\s*[\"']?([^\"'\s]+)", text, re.MULTILINE)
    if not match:
        raise ValueError("bundle/bundle.yml has no bundle.version")
    return match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--specify", default=shutil.which("specify"))
    parser.add_argument("--version", default=None)
    parser.add_argument("--integration", choices=["opencode", "codex"], default="opencode")
    args = parser.parse_args()
    if not args.specify:
        print("specify CLI is not on PATH")
        return 1
    version = args.version or version_from_bundle()
    temporary = Path(tempfile.mkdtemp(prefix="speckit-bundle-install-"))
    server = None
    try:
        dist = temporary / "dist"
        run(
            [
                sys.executable,
                "scripts/package_components.py",
                "--version",
                version,
                "--output",
                str(dist),
            ],
            ROOT,
        )
        run(
            [
                args.specify,
                "bundle",
                "build",
                "--path",
                str(ROOT / "bundle"),
                "--output",
                str(dist),
            ],
            ROOT,
        )

        serve = temporary / "serve"
        (serve / "catalogs").mkdir(parents=True)
        shutil.copytree(dist, serve / "release-assets")
        shutil.copytree(ROOT / "workflows", serve / "workflows")
        # Serve the LF form used by GitHub's release sources. A Windows checkout
        # can have CRLF; the CLI writes fetched text using platform newlines.
        for workflow in (serve / "workflows").rglob("*.yml"):
            workflow.write_bytes(workflow.read_text(encoding="utf-8").encode("utf-8"))
        for name in ("extensions.json", "workflows.json", "bundles.json"):
            text = (ROOT / "catalogs" / name).read_text(encoding="utf-8")
            text = TAG_URL.sub("http://127.0.0.1:__PORT__", text)
            text = ASSET_URL.sub("http://127.0.0.1:__PORT__/release-assets/", text)
            (serve / "catalogs" / name).write_text(text, encoding="utf-8")

        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *_args: object) -> None:
                pass

        server = socketserver.ThreadingTCPServer(
            ("127.0.0.1", 0),
            lambda *a, **kw: Handler(*a, directory=str(serve), **kw),
        )
        port = server.server_address[1]
        for name in ("extensions.json", "workflows.json", "bundles.json"):
            path = serve / "catalogs" / name
            path.write_text(
                path.read_text(encoding="utf-8").replace("__PORT__", str(port)),
                encoding="utf-8",
            )
        threading.Thread(target=server.serve_forever, daemon=True).start()

        project = temporary / "project"
        project.mkdir()
        base = f"http://127.0.0.1:{port}"
        initialize = [
            args.specify,
            "init",
            ".",
            "--integration",
            args.integration,
            "--script",
            "ps" if os.name == "nt" else "sh",
            "--ignore-agent-tools",
            "--non-interactive",
        ]
        if args.integration == "codex":
            initialize.append("--integration-options=--skills")
        commands = [
            initialize,
            [
                args.specify,
                "extension",
                "catalog",
                "add",
                f"{base}/catalogs/extensions.json",
                "--name",
                "local-delivery",
                "--install-allowed",
            ],
            [
                args.specify,
                "workflow",
                "catalog",
                "add",
                f"{base}/catalogs/workflows.json",
                "--name",
                "local-delivery",
            ],
            [
                args.specify,
                "bundle",
                "catalog",
                "add",
                f"{base}/catalogs/bundles.json",
                "--id",
                "local-delivery",
                "--policy",
                "install-allowed",
            ],
            [args.specify, "bundle", "install", "speckit-delivery"],
        ]
        for command in commands:
            run(command, project)
        installed = run([args.specify, "bundle", "list", "--json"], project)
        data = json.loads(installed.stdout)
        text = json.dumps(data, ensure_ascii=False)
        if "speckit-delivery" not in text or version not in text:
            raise RuntimeError("Bundle installation record is missing the expected id/version")
        check_delivery_install(project, dist, version, args.integration)
        router, alias = check_router_alias(project, args.integration)
        config_path = project / ".specify/extensions/delivery/delivery-config.yml"
        custom_config = config_path.read_text(encoding="utf-8").replace(
            "max_review_fix_rounds: 3", "max_review_fix_rounds: 2"
        )
        config_path.write_text(
            custom_config + "\n# Project-owned setting: preserve this customization.\n",
            encoding="utf-8",
        )
        original_config = config_path.read_bytes()
        installed_helper = project / ".specify/extensions/delivery/scripts/delivery_runtime.py"
        run(
            [
                sys.executable,
                str(ROOT / "scripts/test_runtime_install.py"),
                "--project",
                str(project),
                "--helper",
                str(installed_helper),
            ],
            project,
        )
        check_controlled_alias_upgrade(
            project,
            args.specify,
            args.integration,
            original_config,
            config_path,
        )
        alias.unlink()
        run([args.specify, "extension", "add", "delivery", "--force"], project)
        check_router_alias(project, args.integration)
        if config_path.read_bytes() != original_config:
            raise RuntimeError("Reinstalling Delivery overwrote the project configuration")
        run([args.specify, "extension", "remove", "delivery", "--keep-config", "--force"], project)
        if router.exists() or alias.exists():
            raise RuntimeError(f"{args.integration} removal left a router or sd alias behind")
        if config_path.read_bytes() != original_config:
            raise RuntimeError("Removing Delivery with --keep-config lost the project configuration")
        print("Bundle install, sd alias refresh/removal, and config preservation passed.", flush=True)
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f"Bundle installation test failed: {exc}")
        return 1
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        shutil.rmtree(temporary, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
