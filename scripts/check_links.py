#!/usr/bin/env python3
"""Fail when a repository-local Markdown link points at a missing path."""

from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import unquote


LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#")
# Unmodified third-party skill copies keep their upstream relative links,
# including placeholders and references to demo assets this repository does not
# vendor. Their provenance and exclusions are recorded in each SOURCE.md.
THIRD_PARTY_SKILL_DIRS = {"skills/archify", "skills/fireworks-tech-graph"}


def is_third_party_skill(markdown: Path, root: Path) -> bool:
    relative = markdown.relative_to(root).as_posix()
    return any(relative.startswith(f"{prefix}/") for prefix in THIRD_PARTY_SKILL_DIRS)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failures: list[str] = []
    for markdown in sorted(root.rglob("*.md")):
        if any(part in {".git", "dist", "build"} for part in markdown.parts):
            continue
        if is_third_party_skill(markdown, root):
            continue
        text = markdown.read_text(encoding="utf-8")
        for raw_target in LINK.findall(text):
            target = raw_target.strip().strip("<>").split(maxsplit=1)[0]
            if not target or target.startswith(SKIP_PREFIXES):
                continue
            path_text = unquote(target.split("#", 1)[0])
            if not path_text:
                continue
            resolved = (markdown.parent / path_text).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                failures.append(f"{markdown.relative_to(root)} -> {target} escapes repository")
                continue
            if not resolved.exists():
                failures.append(f"{markdown.relative_to(root)} -> {target} is missing")

    if failures:
        print("Broken local Markdown links:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Local Markdown links are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
