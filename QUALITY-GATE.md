# Quality Gate configuration

`speckit.quality.check` executes project-owned quality profiles and returns a
task-closure verdict. It does not replace native language tooling.

Before editing, `speckit.quality.brief` reads the same Profile and returns the
rules, architecture constraints, anti-patterns, and post-edit commands relevant
to the target paths. It is advisory context; it never claims that code is
already compliant.

## Configuration

Create `.specify/extensions/quality/quality-config.yml` with one profile per
source family:

```yaml
policy_sources:
  architecture: [Docs/architecture/repo-structure.md]
  style: [Docs/architecture/code-style.md]
standards:
  - id: layer-boundaries
    owner: review
    mechanism: "speckit.review.standards against the architecture policy"
  - id: avoid-duplication
    owner: simplify
    mechanism: "speckit.simplify.scan before final review"
profiles:
  - id: python
    match: ["backend/**/*.py"]
    discovery_files: ["pyproject.toml", "uv.lock"]
    commands:
      format: "uv run ruff format --check {changed_files}"
      lint: "uv run ruff check {changed_files}"
      typecheck: "uv run mypy backend"
      test: "uv run pytest {affected_tests}"
    rules:
      complexity_max: 10
unprofiled_changed_paths: block
reuse_passing_hooks: true
```

`match` selects changed files; `discovery_files` proves the toolchain; commands
run from repository root; `rules` is metadata unless a configured command
actually enforces it. Do not execute unknown literal placeholders.

`standards` makes semantic rules explicit. Every stated rule needs an owner and
an evidence-producing mechanism, or `speckit.delivery.doctor` blocks the
workflow before planning. It is deliberately not a fake linter configuration.

## Ownership

Formatting, lint, types, tests, and complexity belong in Ruff, ESLint, Go,
Maven/Gradle, .NET, or the project's existing CI configuration. DRY, duplicate
state, ownership, directory boundaries, and architecture consistency belong to
Simplify, Review, and ADRs. See [examples](examples/quality-gate/) for native
configuration plus matching Profile fragments.

Ralph may mark a task `[X]` only after both current-HEAD reports say:

```text
QUALITY_VERDICT: pass
STANDARDS_VERDICT: pass
HEAD: <current SHA>
SCOPE: T014
```

Missing profiles, unavailable required commands, failed checks, or stale scope
are `blocked`, never an implicit pass. The quality verdict covers executable
checks; the standards verdict covers DRY, ownership, layer direction, public
surface, comment intent, and whether an ADR must change.
