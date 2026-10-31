---
description: "Keep package READMEs true to their package contents for both users and maintainers"
---

# Package README

Run after `speckit.docs-sync.run` and before review, or directly when a package
is created or its public surface changes. This command owns the package-level
README contract; `speckit.docs-sync.run` still owns manifests, generated
projections, and inbound links. It edits documentation only.

## Input

`scope=outgoing-diff` (default) inspects the change against the repository base.
`package=<path>` limits the run to one package. `delivery_run=<id>` may be
supplied for traceability but does not create a new durable record.

Read `.specify/extensions/docs-sync/docs-sync-config.yml` when present. Honor
`package_readme: auto | required | off` (default `auto`) and `package_roots`.
`off` reports `not-applicable` and stops. `required` turns a missing section or an
unresolved fact gap into a blocker; `auto` reports it without blocking.

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
commands, defaults, or APIs that the package does not expose.

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
PACKAGES:
- <package>: created | updated | unchanged | missing | blocked — <reason> — <README path>
RESEARCH:
- <source or skipped>: <adopted/rejected or reason>
GAPS:
- <package#section>: <missing fact and owner>
```

The command is complete when every in-scope package has an explicit outcome,
every new package has either the full contract or named gaps, and every reported
command, API, and default was verified against package contents. Do not commit,
push, or publish.
