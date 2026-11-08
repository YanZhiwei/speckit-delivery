#!/usr/bin/env python3
"""Deterministic README structure guard for the Docs Sync README contract.

The command contract asks the model to edit a README in place. This script is
the part that cannot be talked around. It fails on:

- duplicate headings and a stale table of contents;
- release-anchored prose such as "since 0.4.2";
- an exceeded line budget, with the split target named in the message;
- broken local links;
- a new document under the docs root that the README index never links;
- a section appended at the end of the file instead of a real edit.

Exit code 0 means pass, 1 means blocked, 2 means a usage error.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote


HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
TOC_ENTRY = re.compile(r"^\s*[-*+]\s+\[[^\]]*\]\(#([^)]+)\)\s*$")
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
RELEASE_PROSE = re.compile(r"(?:从|since)\s+`?v?\d+\.\d+", re.IGNORECASE)
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
TOC_TITLES = {"目录", "contents", "table of contents"}
FENCE = re.compile(r"^\s*(```|~~~)")
SKIP_LINK_PREFIXES = ("http://", "https://", "mailto:", "#")


def _readable_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def _headings(lines: list[str]) -> list[tuple[int, str, int]]:
    """Return (level, title, index) for headings outside fenced code blocks."""
    found: list[tuple[int, str, int]] = []
    in_fence = False
    for index, line in enumerate(lines):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING.match(line)
        if match:
            found.append((len(match.group(1)), match.group(2).strip(), index))
    return found


def _slugify(title: str) -> str:
    """Approximate the GitHub anchor for a heading title."""
    kept: list[str] = []
    for char in title.strip().lower():
        if char.isalnum() or char in "-_":
            kept.append(char)
        elif char == " ":
            kept.append("-")
    return "".join(kept)


def _toc(
    lines: list[str], headings: list[tuple[int, str, int]]
) -> tuple[int, list[str]] | None:
    """Return (heading index, anchors) for the table-of-contents section."""
    for level, title, index in headings:
        if title.strip().lower() in TOC_TITLES:
            end = next(
                (
                    other
                    for other_level, _, other in headings
                    if other > index and other_level <= level
                ),
                len(lines),
            )
            anchors: list[str] = []
            for line in lines[index + 1 : end]:
                match = TOC_ENTRY.match(line)
                if match:
                    anchors.append(match.group(1))
            return index, anchors
    return None


def _section_sizes(
    lines: list[str], headings: list[tuple[int, str, int]]
) -> list[tuple[str, int]]:
    """Return (title, line count) for every level-2 section."""
    sizes: list[tuple[str, int]] = []
    for position, (level, title, index) in enumerate(headings):
        if level != 2:
            continue
        end = next(
            (
                other
                for other_level, _, other in headings[position + 1 :]
                if other_level <= level
            ),
            len(lines),
        )
        sizes.append((title, end - index))
    return sizes


def _local_links(text: str) -> list[str]:
    targets: list[str] = []
    for raw in LINK.findall(text):
        target = raw.strip().strip("<>").split(maxsplit=1)[0]
        if not target or target.startswith(SKIP_LINK_PREFIXES):
            continue
        path_text = unquote(target.split("#", 1)[0])
        if path_text:
            targets.append(path_text)
    return targets


def check_structure(
    path: Path,
    text: str,
    max_lines: int | None,
    sections: list[str] | None,
    docs_root: str | None,
) -> list[str]:
    """Return structure blockers for one README's current contents."""
    lines = text.splitlines()
    problems: list[str] = []
    split_target = f"{docs_root or 'docs'}/<topic>.md"
    if max_lines and len(lines) > max_lines:
        problems.append(
            f"{len(lines)} lines exceeds the {max_lines}-line budget; move detail to "
            f"{split_target} and keep one index row"
        )

    headings = _headings(lines)
    seen: dict[tuple[int, str], int] = {}
    for level, title, index in headings:
        key = (level, _slugify(title))
        if key in seen:
            problems.append(
                f"duplicate heading {title!r} at line {index + 1} "
                f"(first at line {seen[key] + 1})"
            )
        else:
            seen[key] = index

    toc = _toc(lines, headings)
    if toc is not None:
        toc_index, anchors = toc
        listed = set(anchors)
        if anchors:
            for level, title, index in headings:
                if level != 2 or index == toc_index:
                    continue
                if _slugify(title) not in listed:
                    problems.append(
                        f"section {title!r} is missing from the table of contents"
                    )
        known = {_slugify(title) for _, title, _ in headings}
        for anchor in anchors:
            if anchor not in known:
                problems.append(
                    f"table-of-contents entry #{anchor} does not resolve to a heading"
                )

    if sections:
        titles = [title for level, title, _ in headings if level == 2]
        toc_title = next(
            (
                title
                for level, title, _ in headings
                if level == 2 and title.strip().lower() in TOC_TITLES
            ),
            None,
        )
        actual = [title for title in titles if title != toc_title]
        if actual != sections:
            problems.append(
                f"sections {actual} != {sections}; replace content in an existing "
                f"section or move it to {split_target} instead of adding one"
            )

    for target in _local_links(text):
        resolved = (path.parent / target).resolve()
        if not resolved.exists():
            problems.append(f"local link {target!r} does not resolve")

    for index, line in enumerate(lines):
        match = RELEASE_PROSE.search(line)
        if match:
            problems.append(
                f"release-anchored prose {match.group(0)!r} at line {index + 1} "
                "belongs in the changelog; describe current behavior only"
            )
            break

    return problems


def _git(repo: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _added_docs(
    repo: Path, base: str, docs_root: str | None
) -> tuple[list[str], str | None]:
    """Return new files under the docs root, tracked or not, or a limitation note."""
    if not docs_root:
        return [], None
    diff = _git(repo, "diff", "--name-only", "--diff-filter=A", base, "--", docs_root)
    if diff.returncode != 0:
        return [], f"git diff against {base!r} failed: {diff.stderr.strip()}"
    untracked = _git(
        repo, "ls-files", "--others", "--exclude-standard", "--", docs_root
    )
    if untracked.returncode != 0:
        return [], f"git ls-files failed: {untracked.stderr.strip()}"
    found = {
        line.strip()
        for line in (diff.stdout + "\n" + untracked.stdout).splitlines()
        if line.strip().endswith(".md")
    }
    return sorted(found), None


def check_diff(
    path: Path, base: str, total_lines: int, docs_root: str | None
) -> list[str]:
    """Return blockers for append-only edits relative to ``base``."""
    resolved = path.resolve()
    root = _git(resolved.parent, "rev-parse", "--show-toplevel")
    if root.returncode != 0:
        return ["not a Git work tree; append-only check was skipped"]
    repo = Path(root.stdout.strip())
    try:
        relative = resolved.relative_to(repo).as_posix()
    except ValueError:
        return ["file is outside the repository; append-only check was skipped"]

    problems: list[str] = []
    readme = path.read_text(encoding="utf-8")
    new_docs, limitation = _added_docs(repo, base, docs_root)
    if limitation:
        problems.append(limitation)
    for doc in new_docs:
        if doc not in readme:
            problems.append(
                f"new document {doc!r} is not registered in the README index"
            )

    if _git(repo, "cat-file", "-e", f"{base}:{relative}").returncode != 0:
        return problems
    numstat = _git(repo, "diff", "--numstat", base, "--", relative)
    if numstat.returncode != 0:
        return [*problems, f"git diff against {base!r} failed: {numstat.stderr.strip()}"]
    changed = [line for line in numstat.stdout.splitlines() if line.strip()]
    if not changed:
        return problems
    fields = changed[0].split("\t")
    if len(fields) < 2 or not fields[0].isdigit() or not fields[1].isdigit():
        return problems
    added, removed = int(fields[0]), int(fields[1])

    patch = _git(repo, "diff", "-U0", base, "--", relative)
    if patch.returncode != 0:
        return [*problems, f"git diff against {base!r} failed: {patch.stderr.strip()}"]
    patch_lines = patch.stdout.splitlines()
    added_lines = [
        line[1:]
        for line in patch_lines
        if line.startswith("+") and not line.startswith("+++")
    ]
    removed_lines = [
        line[1:]
        for line in patch_lines
        if line.startswith("-") and not line.startswith("---")
    ]
    new_headings = [line for line in added_lines if HEADING.match(line)]
    removed_headings = [line for line in removed_lines if HEADING.match(line)]
    toc_updates = [line for line in added_lines if TOC_ENTRY.match(line)]

    if new_headings and not removed_headings and not toc_updates:
        sample = HEADING.match(new_headings[0]).group(2).strip()
        problems.append(
            f"new section {sample!r} was added without replacing an existing "
            "section or registering it in the table of contents"
        )
    if _appends_at_end(patch_lines, total_lines):
        problems.append(
            "content was appended at the end of the file; add it to the section "
            "that owns the fact, or move detail to a docs page and link it"
        )
    if added and not removed and added >= 40:
        problems.append(
            f"{added} lines were added and none replaced; a change this size must "
            "also remove or rewrite the text it supersedes"
        )
    return problems


def _appends_at_end(patch_lines: list[str], total_lines: int) -> bool:
    """True when the last hunk inserts a heading at the end of the file."""
    old_count = new_start = new_count = 0
    inserted: list[str] = []
    at_end = False
    for line in patch_lines:
        match = HUNK.match(line)
        if match:
            old_count = int(match.group(2) or 1)
            new_start = int(match.group(3))
            new_count = int(match.group(4) or 1)
            inserted = []
            at_end = (
                old_count == 0
                and new_count > 0
                and new_start + new_count - 1 >= total_lines
            )
            continue
        if at_end and line.startswith("+") and not line.startswith("+++"):
            inserted.append(line[1:])
    return at_end and any(HEADING.match(line) for line in inserted)


def main() -> int:
    _readable_stdout()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="README files to check")
    parser.add_argument(
        "--base", help="Git base ref; enables append-only detection"
    )
    parser.add_argument("--max-lines", type=int, help="configured line budget")
    parser.add_argument(
        "--sections", help="comma-separated required level-2 sections, in order"
    )
    parser.add_argument(
        "--docs-root",
        help="directory that owns extracted detail, e.g. docs",
    )
    args = parser.parse_args()

    sections = (
        [item.strip() for item in args.sections.split(",") if item.strip()]
        if args.sections
        else None
    )

    blockers: list[str] = []
    checked: list[str] = []
    sizes: list[tuple[str, int]] = []
    for raw in args.paths:
        path = Path(raw)
        if not path.is_file():
            blockers.append(f"{raw}: missing README")
            continue
        text = path.read_text(encoding="utf-8")
        checked.append(raw)
        total_lines = len(text.splitlines())
        for problem in check_structure(
            path, text, args.max_lines, sections, args.docs_root
        ):
            blockers.append(f"{raw}: {problem}")
        if len(args.paths) == 1:
            sizes = _section_sizes(text.splitlines(), _headings(text.splitlines()))
        if args.base:
            for problem in check_diff(path, args.base, total_lines, args.docs_root):
                blockers.append(f"{raw}: {problem}")

    print(f"README_STRUCTURE: {'blocked' if blockers else 'pass'}")
    print(f"PATHS: {', '.join(checked) if checked else 'none'}")
    print(f"BUDGET: {'unset' if not args.max_lines else args.max_lines}")
    if sizes:
        print("SECTIONS:")
        for title, count in sizes:
            print(f"- {title}: {count} lines")
    if blockers:
        print("BLOCKERS:")
        for blocker in blockers:
            print(f"- {blocker}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
