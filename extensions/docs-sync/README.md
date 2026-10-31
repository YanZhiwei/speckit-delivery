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
