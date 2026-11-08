# Documentation Projection Sync

An optional extension for repositories where authored Markdown or another source tree generates a documentation site. The source is authoritative; generated projections are updated through the configured generator rather than edited directly.

## Commands

- `speckit.docs-sync.run`: update authored sources, the publication manifest,
  inbound links, and generated projections.
- `speckit.docs-sync.package-readme`: create or refresh a package README from the
  package's real manifest, exports, CLI, configuration, dependencies, and test
  commands.

## Package README contract

The package README node runs after projection sync and before review. It serves
two audiences:

- users: purpose and non-goals, install, quick start, public API/CLI/config,
  errors and limits, compatibility, license;
- maintainers: ownership, dependency direction, development and test commands,
  release/versioning, contributing.

For a new package, the command compares two or three comparable public projects
and records what it adopted or rejected. For a changed package, it judges each
changed surface and reports `updated`, `unchanged-with-reason`, or `gap`; it never
invents commands, defaults, or APIs. The packaged
[template](templates/package-readme.md) is the structure, and `package_readme`
in `docs-sync-config.yml` controls whether gaps block (`required`) or are only
reported (`auto`).

## README structure contract

A README is an index, not a log. `project_readme` in `docs-sync-config.yml`
(default `auto`) extends the same contract to project entry READMEs listed by
`readme_paths`, with `readme_max_lines`, `readme_sections`, and
`readme_docs_root` bounding how much lives in the entry point.

The contract allows exactly three moves, in order: rewrite the section that owns
the fact; move detail to `<readme_docs_root>/<topic>.md` and keep one index row
plus a link; or add a section that is registered in the table of contents in the
same edit. Appending a trailing paragraph, adding an unregistered section, or
duplicating an existing table is drift even when the content is correct.

[`scripts/readme_structure.py`](scripts/readme_structure.py) is the
deterministic guard. It fails on duplicate headings, a stale or broken table of
contents, release-anchored prose, a broken local link, an exceeded line budget,
a new document the index never links, and a section appended at the end of the
file. Its `SECTIONS:` output is the split worklist. The packaged
[project template](templates/project-readme.md) shows the index shape and the
`docs/` layout it expects.
