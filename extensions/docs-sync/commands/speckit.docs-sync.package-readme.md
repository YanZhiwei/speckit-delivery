---
description: "Keep package READMEs true to their package contents for both users and maintainers"
---

# Package README

Run after `speckit.docs-sync.run` and before review, or directly when a package
is created or its public surface changes. Inside an already reserved Review Fix
attempt, `repair=1 attempt=<n>` refreshes only affected surfaces before that
attempt's re-review; it is not a new review round. This command owns the
package-level README contract; `speckit.docs-sync.run` still owns manifests,
generated projections, and inbound links. It edits documentation only.

## Input

`scope=outgoing-diff` (default) inspects the change against the repository base.
`package=<path>` limits the run to one package. `delivery_run=<id>` may be
supplied for traceability but does not create a new durable record. `lane` may be
`feature`, `bugfix`, or `lightweight`; `repair=1` marks a call made inside an
already reserved Review Fix attempt, with `attempt=<n>` identifying that reserved
round. It refreshes only affected package surfaces at that attempt and does not
add a repair round. `with_docs_sync=false` governs projection sync only; it does
not by itself suppress the package README policy (`package_readme` controls that).

Read `.specify/extensions/docs-sync/docs-sync-config.yml` when present. Honor
`package_readme: auto | required | off` (default `auto`), `package_roots`,
`project_readme: auto | required | off` (default `auto`), `readme_paths`,
`readme_max_lines`, `readme_sections`, and `readme_docs_root`. `off` reports
`not-applicable` and stops. `required` turns a missing section or an unresolved
fact gap into a blocker; `auto` reports it without blocking.

## Detect package surfaces

Resolve the actual outgoing diff. A package is in scope when the change adds or
modifies a package root (`packages/<...>` or another configured root) or any
manifest such as `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`,
`*.csproj`, `pom.xml`, or `build.gradle*`. For each package, read the manifest,
public exports, CLI entry points, configuration keys and defaults, environment
variables, supported runtime versions, dependencies, and the real test/quality
commands.

A change is README-affecting when it changes purpose, install or setup, public
API/CLI/config, defaults, compatibility, dependencies, error behavior,
development/test commands, release/versioning, or ownership. An internal-only
change is not README-affecting; record why.

## Contract

Every package README must serve both audiences and contain:

- purpose, scope, and explicit non-goals;
- status and compatibility: version, supported runtimes, and stability;
- install and the shortest working quick start;
- public API, CLI, or configuration reference with real names and defaults;
- errors, limits, and failure behavior users must handle;
- architecture and boundaries: ownership, dependency direction, and what the
  package must not do;
- development: layout, setup, test and quality commands, required tool versions;
- release and versioning, including the changelog or tag convention;
- ownership/contributing and links to related durable docs;
- license.

Use the packaged `templates/package-readme.md` as the structure. Omit sections
that do not apply with a reason instead of leaving boilerplate. Never invent
commands, defaults, or APIs that the package does not expose. Never append text
to the end of a README; the placement rules below apply to package READMEs too.

## Project README structure

A README is an index, not a log. `project_readme` governs project entry READMEs
listed by `readme_paths` (default `README.md`); `readme_docs_root` (default
`docs`) names the directory that owns extracted detail.

When the change touches a user-facing surface, edit the README under these rules:

- **One owner per fact.** Keep a one-line claim and a link; runtime, install,
  release, and history detail belongs in the document that owns it.
- **Describe current behavior only.** "Since X" statements belong in the
  changelog. A README edit is not a release note.
- **Three legal moves, in this order:**
  1. rewrite the section that already owns the fact;
  2. move detail to `<readme_docs_root>/<topic>.md`, or to
     `<readme_docs_root>/<area>/<topic>.md` when the topic already has sibling
     pages, and replace the README text with one index row plus a link;
  3. add one new section only when no existing section owns the fact, the table
     of contents is updated in the same edit, and the line budget still holds.
- **Never append.** A trailing paragraph, an unregistered section, or a second
  copy of an existing table is drift even when the content is correct. Moving
  content out of the README is a normal, expected edit; growing it is not.
- **Respect `readme_max_lines` and `readme_sections`.** When the budget is
  exhausted, split first. Raising the budget is a reviewed decision, not a
  convenience.

Run the deterministic guard and quote its output verbatim:

```bash
python .specify/extensions/docs-sync/scripts/readme_structure.py README.md \
  --base <repository base ref> --max-lines <readme_max_lines> \
  --docs-root <readme_docs_root>
```

`SECTIONS:` in that output is the split worklist: move the largest non-index
section out first and keep the README an index of links. The guard treats a
section titled `目录`, `Contents`, or `Table of contents` as the index; pass
`--sections` only when the project fixes its section list. `required` blocks
completion on `README_STRUCTURE: blocked`; `auto` reports the blockers without
blocking. A missing script, git base, or docs root is a reported limitation,
never a pass.

## New packages: compare before writing

For a new package, inspect two or three comparable public projects in the same
ecosystem and role, using available README sources. Record each source and what
was adopted or rejected (section order, quick-start depth, API reference style,
maintenance sections). Do not copy prose, badges, or marketing claims. If network
or comparable examples are unavailable, write from the actual package contents
and report the research limitation; do not fabricate references.

## Changed packages: judge drift explicitly

For each in-scope package, produce a table of changed surface, README section,
and outcome: `updated`, `unchanged-with-reason`, or `gap`. A change that touches a
README-affecting surface cannot be `unchanged-with-reason` unless the existing
text is still accurate and you cite the lines that remain correct.

## Output

```text
PACKAGE_README_VERDICT: pass | updated | blocked | not-applicable
README_STRUCTURE: pass | blocked | not-applicable
LANE / SCOPE / REPAIR: <supplied lane, package/outgoing scope, repair flag and attempt>
INPUT_IDENTITY: <actual base/head/content/config identity and method used>
PACKAGES:
- <package>: created | updated | unchanged | missing | blocked — <reason> — <README path>
README_MOVES:
- <README path#section>: replaced | split to <doc path> | added (reason) | unchanged-with-reason
RESEARCH:
- <source or skipped>: <adopted/rejected or reason>
GAPS:
- <package#section or README#section>: <missing fact and owner>
```

The command is complete when every in-scope package has an explicit outcome,
every new package has either the full contract or named gaps, every reported
command, API, and default was verified against package contents, and every
project README edit either passes the structure guard or reports why it does not
apply. Do not commit, push, or publish.
