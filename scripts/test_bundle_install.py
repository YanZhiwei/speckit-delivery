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


ROOT = Path(__file__).resolve().parents[1]
TAG_URL = re.compile(
    r"https://raw\.githubusercontent\.com/YanZhiwei/speckit-delivery/v[^/]+"
)
ASSET_URL = re.compile(
    r"https://github\.com/YanZhiwei/speckit-delivery/releases/download/v[^/]+/"
)


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
        commands = [
            [
                args.specify,
                "init",
                ".",
                "--integration",
                "opencode",
                "--script",
                "ps" if os.name == "nt" else "sh",
                "--ignore-agent-tools",
                "--non-interactive",
            ],
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
        print("Bundle install from local catalogs passed.", flush=True)
        return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Bundle installation test failed: {exc}")
        return 1
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        shutil.rmtree(temporary, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
