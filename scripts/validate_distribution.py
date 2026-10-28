#!/usr/bin/env python3
"""Validate release catalogs, manifests, workflows, and the bundle as one contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
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
