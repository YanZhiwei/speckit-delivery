#!/usr/bin/env python3
"""Stamp all release versions and catalog URLs for a release-preparation PR."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
VERSION_LINE = re.compile(
    r'^(?P<prefix>\s+version:\s*["\']?)(?P<value>[^"\'\s]+)(?P<suffix>["\']?\s*)$',
    re.MULTILINE,
)
TAG_PATH = re.compile(r"/v\d+\.\d+\.\d+(?=/)")
ASSET_SUFFIX = re.compile(r"-\d+\.\d+\.\d+\.zip$")


def _changelog_section(path: Path, version: str) -> str:
    text = path.read_text(encoding="utf-8")
    header = re.compile(rf"^## \[{re.escape(version)}\][^\n]*\n", re.MULTILINE)
    match = header.search(text)
    if not match:
        raise ValueError(
            f"{path.name} has no '## [{version}]' section; add release notes first"
        )
    remainder = text[match.end() :]
    next_header = re.search(r"^## \[[^\n]+\].*\n", remainder, re.MULTILINE)
    section = remainder[: next_header.start() if next_header else None].strip()
    if not section:
        raise ValueError(f"{path.name} section for {version} is empty")
    return section


def _stamp_yaml(path: Path, version: str) -> str:
    text = path.read_text(encoding="utf-8")
    matches = list(VERSION_LINE.finditer(text))
    if not matches:
        raise ValueError(f"{path}: no version field found")
    return VERSION_LINE.sub(
        lambda match: f"{match.group('prefix')}{version}{match.group('suffix')}",
        text,
    )


README_TAG = re.compile(r"(speckit-delivery/)v\d+\.\d+\.\d+/")


def _stamp_readme(path: Path, tag: str) -> str:
    text = path.read_text(encoding="utf-8")
    updated, count = README_TAG.subn(rf"\g<1>{tag}/", text)
    if count == 0:
        raise ValueError(f"{path}: no versioned release URL found")
    return updated


def _stamp_bundle(path: Path, version: str) -> str:
    """Stamp Bundle and owned components, but preserve the bundled Bug pin.

    `bug` ships with Spec Kit rather than this catalog; changing it to the
    repository release version makes Bundle installation fail its pinned-
    version check.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    current_id: str | None = None
    replaced = 0
    for index, line in enumerate(lines):
        id_match = re.match(r'^\s*-\s*id:\s*["\']?([^"\'\s]+)', line)
        if id_match:
            current_id = id_match.group(1)
            continue
        if current_id == "bug":
            continue
        match = VERSION_LINE.match(line)
        if match:
            lines[index] = f"{match.group('prefix')}{version}{match.group('suffix')}"
            replaced += 1
    if replaced == 0:
        raise ValueError(f"{path}: no version field found")
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _tagged_url(value: object, tag: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"catalog URL is not a string: {value!r}")
    return TAG_PATH.sub(f"/{tag}", value)


def _asset_url(value: object, version: str, tag: str) -> str:
    url = _tagged_url(value, tag)
    return ASSET_SUFFIX.sub(f"-{version}.zip", url)


def _stamp_catalog(path: Path, version: str, tag: str) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["catalog_url"] = _tagged_url(data.get("catalog_url"), tag)
    if "extensions" in data:
        entries = data["extensions"]
        if not isinstance(entries, dict):
            raise ValueError(f"{path}: extensions must be an object")
        for extension_id, entry in entries.items():
            if not isinstance(entry, dict):
                raise ValueError(f"{path}: extension {extension_id} is not an object")
            entry["version"] = version
            entry["download_url"] = _asset_url(
                entry.get("download_url"), version, tag
            )
            if entry.get("documentation") is not None:
                entry["documentation"] = _tagged_url(
                    entry.get("documentation"), tag
                )
    elif "workflows" in data:
        entries = data["workflows"]
        if not isinstance(entries, dict):
            raise ValueError(f"{path}: workflows must be an object")
        for workflow_id, entry in entries.items():
            if not isinstance(entry, dict):
                raise ValueError(f"{path}: workflow {workflow_id} is not an object")
            entry["version"] = version
            entry["url"] = _tagged_url(entry.get("url"), tag)
    elif "bundles" in data:
        entries = data["bundles"]
        if not isinstance(entries, dict):
            raise ValueError(f"{path}: bundles must be an object")
        for bundle_id, entry in entries.items():
            if not isinstance(entry, dict):
                raise ValueError(f"{path}: bundle {bundle_id} is not an object")
            entry["version"] = version
            entry["download_url"] = _asset_url(
                entry.get("download_url"), version, tag
            )
    else:
        raise ValueError(f"{path}: unknown catalog shape")
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def plan(root: Path, version: str, tag: str) -> dict[Path, str]:
    """Return intended file contents without writing anything."""
    if tag != f"v{version}":
        raise ValueError(f"tag {tag!r} must be {f'v{version}'!r}")
    for changelog in (root / "CHANGELOG.md", root / "CHANGELOG.zh-CN.md"):
        _changelog_section(changelog, version)

    updates: dict[Path, str] = {}
    for path in sorted((root / "extensions").glob("*/extension.yml")):
        updates[path] = _stamp_yaml(path, version)
    for path in sorted((root / "workflows").glob("*/workflow.yml")):
        updates[path] = _stamp_yaml(path, version)
    updates[root / "bundle" / "bundle.yml"] = _stamp_bundle(
        root / "bundle" / "bundle.yml", version
    )
    for name in ("extensions.json", "workflows.json", "bundles.json"):
        path = root / "catalogs" / name
        updates[path] = _stamp_catalog(path, version, tag)
    for name in ("README.md", "README.en.md"):
        path = root / name
        if path.is_file():
            updates[path] = _stamp_readme(path, tag)
    return updates


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True, help="release version, e.g. 0.1.1")
    parser.add_argument("--tag", help="release tag; defaults to v<version>")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--check", action="store_true", help="report differences without writing"
    )
    args = parser.parse_args()

    version = args.version.removeprefix("v")
    if not SEMVER.fullmatch(version):
        print(f"version must be semantic X.Y.Z, got {args.version!r}")
        return 1
    tag = args.tag or f"v{version}"
    if tag != f"v{version}":
        print(f"tag must be v{version}, got {tag!r}")
        return 1

    try:
        updates = plan(args.root.resolve(), version, tag)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Release stamp failed: {exc}")
        return 1

    changed = [
        path for path, content in updates.items()
        if path.read_text(encoding="utf-8") != content
    ]
    if args.check:
        if changed:
            print("Release metadata is not stamped for", version)
            for path in changed:
                print(f"- {path}")
            return 1
        print(f"Release metadata is already stamped for {version}.")
        return 0

    for path in changed:
        path.write_text(updates[path], encoding="utf-8")
        print(f"updated {path}")
    if not changed:
        print(f"Release metadata is already stamped for {version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
