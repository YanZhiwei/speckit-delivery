#!/usr/bin/env python3
"""Install the built Bundle from local release-style catalogs in a clean project."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
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
import tomllib
import zipfile


ROOT = Path(__file__).resolve().parents[1]
TAG_URL = re.compile(
    r"https://raw\.githubusercontent\.com/YanZhiwei/speckit-delivery/v[^/]+"
)
ASSET_URL = re.compile(
    r"https://github\.com/YanZhiwei/speckit-delivery/releases/download/v[^/]+/"
)


@dataclass(frozen=True)
class HostLayout:
    root: str
    skills: bool = False
    suffix: str = ".md"
    arguments: str = "$ARGUMENTS"
    alias: bool = True


# Layouts provided by the pinned Spec Kit 1.2.3 validation environment.
HOSTS = {
    "codex": HostLayout(".agents/skills", skills=True),
    "claude": HostLayout(".claude/skills", skills=True),
    "opencode": HostLayout(".opencode/commands"),
    # The dual-layout Skills registration path in 1.2.3 renders primary
    # commands, but not manifest aliases. Verify its canonical route instead.
    "copilot": HostLayout(".github/skills", skills=True, alias=False),
    "gemini": HostLayout(".gemini/commands", suffix=".toml", arguments="{{args}}"),
    "cursor-agent": HostLayout(".cursor/skills", skills=True),
}


def rendered_command(project: Path, integration: str, name: str) -> Path:
    host = HOSTS[integration]
    if host.skills:
        skill = name.replace(".", "-")
        if not skill.startswith("speckit-"):
            skill = f"speckit-{skill}"
        return project / host.root / skill / "SKILL.md"
    return project / host.root / f"{name}{host.suffix}"


def read_prompt(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".toml":
        prompt = tomllib.loads(text)["prompt"]
        if not isinstance(prompt, str):
            raise ValueError(f"{path}: TOML prompt must be a string")
        return prompt
    return text


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
            "templates/focused-audits.md",
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
        "simplify": (
            "commands/speckit.simplify.scan.md",
            "commands/speckit.simplify.verify.md",
        ),
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
        rendered = rendered_command(project, integration, name)
        if not rendered.is_file() or marker not in read_prompt(rendered):
            raise RuntimeError(f"{integration} command missing/stale: {name}")

    # Doctor checks a resource owned by Review. The renderer rewrites bare
    # extension-relative paths to the owning extension, so verify the rendered
    # result names Review and resolves to the installed template.
    doctor = rendered_command(project, integration, "speckit.delivery.doctor")
    if not doctor.is_file():
        raise RuntimeError(f"{integration} command missing: speckit.delivery.doctor")
    reviewer_template = project / ".specify/extensions/review/templates/reviewer.md"
    reviewer_path = ".specify/extensions/review/templates/reviewer.md"
    wrong_path = ".specify/extensions/delivery/templates/reviewer.md"
    if not reviewer_template.is_file():
        raise RuntimeError("installed review templates/reviewer.md is missing")
    text = read_prompt(doctor)
    if reviewer_path not in text or wrong_path in text:
        raise RuntimeError(f"{integration} Doctor has a stale Reviewer path: {doctor}")

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


def check_router_entry(project: Path, integration: str) -> tuple[Path, Path | None]:
    """Verify the canonical entry and any supported alias share an owner/body."""
    host = HOSTS[integration]
    router = rendered_command(project, integration, "speckit.delivery.route")
    alias = rendered_command(project, integration, "sd") if host.alias else None
    if not router.is_file() or (alias is not None and not alias.is_file()):
        raise RuntimeError(f"{integration} delivery entry missing: route={router}, alias={alias}")
    router_text = read_prompt(router)
    alias_text = read_prompt(alias) if alias is not None else router_text
    heading = "# Spec Kit Delivery Route\n"
    if heading not in router_text or heading not in alias_text:
        raise RuntimeError(f"{integration} entry does not contain the installed router")
    if router_text.split(heading, 1)[1].strip() != alias_text.split(heading, 1)[1].strip():
        raise RuntimeError(f"{integration} sd alias differs from the installed router")
    if host.arguments not in alias_text:
        raise RuntimeError(f"{integration} entry lost its native request argument")
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
    if host.skills:
        for entry in (router, alias):
            if entry is not None and not re.search(
                rf"^name: {re.escape(entry.parent.name)}$", read_prompt(entry), re.MULTILINE
            ):
                raise RuntimeError(f"{integration} skill has the wrong name: {entry}")
    elif router_text != alias_text:
        raise RuntimeError(f"{integration} sd alias must match the router prompt exactly")
    registry = json.loads((project / ".specify/extensions/.registry").read_text(encoding="utf-8"))
    metadata = registry["extensions"]["delivery"]
    if alias is not None:
        registered = metadata["registered_commands"].get(integration, [])
        if not {"speckit.delivery.route", "sd"}.issubset(registered):
            raise RuntimeError(f"{integration} registry does not assign both router names to Delivery")
    elif router.parent.name not in metadata.get("registered_skills", []):
        raise RuntimeError(f"{integration} registry does not assign the route skill to Delivery")
    entry_label = "route and sd alias" if alias is not None else "canonical route"
    print(f"{integration} {entry_label}, request input, and Delivery ownership verified.", flush=True)
    return router, alias


def check_controlled_alias_upgrade(
    project: Path,
    specify: str,
    integration: str,
    original_config: bytes,
    config_path: Path,
) -> None:
    """Verify Bundle update and, where supported, adoption of an old sd shim."""
    _router, alias = check_router_entry(project, integration)
    if alias is None:
        run([specify, "bundle", "update", "speckit-delivery", "--integration", integration], project)
        check_router_entry(project, integration)
        if config_path.read_bytes() != original_config:
            raise RuntimeError("Controlled Bundle update overwrote the project configuration")
        print(f"{integration} canonical-route Bundle update verified (no alias in this CLI layout).", flush=True)
        return
    legacy_marker = "# legacy custom sd forwarding shim"
    host = HOSTS[integration]
    if host.skills:
        legacy = (
            "---\n"
            "name: speckit-sd\n"
            "description: Legacy local Delivery shortcut\n"
            "---\n\n"
            f"{legacy_marker}\n"
            "Delegate to the old Delivery route with the request below.\n"
            "$ARGUMENTS\n"
        )
    elif host.suffix == ".toml":
        body = f"{legacy_marker}\nDelegate to the old Delivery route.\n{host.arguments}\n"
        legacy = 'description = "Legacy local Delivery shortcut"\n' + f"prompt = {json.dumps(body)}\n"
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
    check_router_entry(project, integration)
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
    parser.add_argument("--integration", choices=[*HOSTS, "all"], default="opencode")
    parser.add_argument(
        "--list-integrations", action="store_true",
        help="Print the CI integration matrix as JSON",
    )
    args = parser.parse_args()
    if args.list_integrations:
        print(json.dumps(list(HOSTS)))
        return 0
    if not args.specify:
        print("specify CLI is not on PATH")
        return 1
    version = args.version or version_from_bundle()
    if args.integration == "all":
        failed = []
        for integration in HOSTS:
            try:
                run(
                    [
                        sys.executable, str(Path(__file__).resolve()),
                        "--specify", args.specify, "--version", version,
                        "--integration", integration,
                    ],
                    ROOT,
                )
            except RuntimeError:
                failed.append(integration)
        print(f"Host installation matrix: {len(HOSTS) - len(failed)}/{len(HOSTS)} passed.", flush=True)
        if failed:
            print(f"Failed integrations: {', '.join(failed)}", flush=True)
        return int(bool(failed))
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
        router, alias = check_router_entry(project, args.integration)
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
        missing_entry = alias if alias is not None else router
        missing_entry.unlink()
        if missing_entry.name == "SKILL.md":
            # Model a missing installed entry, not an existing user directory:
            # the dual-layout installer deliberately preserves the latter.
            missing_entry.parent.rmdir()
        run([args.specify, "extension", "add", "delivery", "--force"], project)
        check_router_entry(project, args.integration)
        if config_path.read_bytes() != original_config:
            raise RuntimeError("Reinstalling Delivery overwrote the project configuration")
        run([args.specify, "extension", "remove", "delivery", "--keep-config", "--force"], project)
        if router.exists() or (alias is not None and alias.exists()):
            raise RuntimeError(f"{args.integration} removal left a router or sd alias behind")
        if config_path.read_bytes() != original_config:
            raise RuntimeError("Removing Delivery with --keep-config lost the project configuration")
        print(f"{args.integration}: Bundle install, entry refresh/removal, and config preservation passed.", flush=True)
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
