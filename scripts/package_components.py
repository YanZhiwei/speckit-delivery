#!/usr/bin/env python3
"""Build deterministic root-layout zip archives for every extension."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import zipfile


FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
EXCLUDED = {".git", "__pycache__", ".DS_Store"}


def declared_version(manifest: Path) -> str:
    match = re.search(r'^\s*version:\s*["\']?([^"\'\s]+)', manifest.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise ValueError(f"No version found in {manifest}")
    return match.group(1)


def archive_directory(source: Path, target: Path) -> int:
    files = sorted(
        path
        for path in source.rglob("*")
        if path.is_file() and not any(part in EXCLUDED for part in path.parts)
    )
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(source).as_posix(), FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return len(files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path("dist"))
    parser.add_argument("--version")
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    for extension in sorted((root / "extensions").iterdir()):
        manifest = extension / "extension.yml"
        if not manifest.exists():
            continue
        version = declared_version(manifest)
        if args.version and version != args.version:
            raise ValueError(f"{extension.name} declares {version}, expected {args.version}")
        target = output / f"{extension.name}-{version}.zip"
        count = archive_directory(extension, target)
        print(f"built {target.name} ({count} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
