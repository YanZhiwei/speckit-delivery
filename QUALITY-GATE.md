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
  - id: test-layout
    owner: quality
    mechanism: "pnpm check:test-layout"
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
excluded_paths: ["poc/**"] # Outside governed product scope; reported, never passed.
reuse_passing_hooks: true
```

`match` selects changed files; `discovery_files` proves the toolchain; commands
run from repository root; `rules` is metadata unless a configured command
actually enforces it. Do not execute unknown literal placeholders.

`standards` makes semantic rules explicit. Every stated rule needs an owner and
an evidence-producing mechanism, or `speckit.delivery.doctor` blocks the
workflow before planning. It is deliberately not a fake linter configuration.

Use `excluded_paths` only for deliberately out-of-scope code such as throwaway
prototypes. Quality Brief, Quality Check, and Standards Review report excluded
paths but do not treat them as verified. When a prototype becomes product code,
move it out of the excluded path and create a Profile.

## Structural thresholds beyond lint

CRAP, duplication similarity, and mutation coverage can be Profile commands,
but only when the project owns a command that fails the process. A tool that
prints a table or writes `.metrics/` reports is not a gate by itself: wrap it in
a small project script that parses the report, compares the configured
threshold, prints the offending functions, and exits non-zero.

```yaml
profiles:
  - id: python
    match: ["backend/**/*.py"]
    discovery_files: ["pyproject.toml", "uv.lock"]
    commands:
      complexity: "uv run python tools/crap_gate.py --max 10"
      duplication: "uv run python tools/duplication_gate.py --max 0.8"
      mutation: "uv run python tools/mutation_gate.py --changed"
    rules:
      complexity_max: 10
      duplication_max: 0.8
```

- The wrapper owns the tool invocation; this distribution ships none.
- `rules` stays metadata until a configured command enforces it. Without a
  wrapper, report the threshold as an explicit gap, never as a pass.
- Run mutation on the changed scope first. A full-tree first run is expensive
  and proves less about the outgoing diff.
- A threshold is project-owned. Do not copy `10` or `0.8` into a project that
  never agreed to them.

## Ownership

Formatting, lint, types, tests, and complexity belong in Ruff, ESLint, Go,
Maven/Gradle, .NET, or the project's existing CI configuration. DRY, duplicate
state, ownership, and architecture consistency belong to Simplify, Review, and
ADRs. Directory boundaries belong there too unless the repository provides a
narrow, credible structural checker; a test-layout checker is a useful example.
See [examples](examples/quality-gate/) for native configuration plus matching
Profile fragments.

Ralph may mark a task `[X]` only after three current-snapshot reports say:

```text
QUALITY_VERDICT: pass
STANDARDS_VERDICT: pass
REVIEW_VERDICT: pass
HEAD: <current SHA>
SCOPE: T014
```

Missing profiles, unavailable required commands, failed checks, or stale scope
are `blocked`, never an implicit pass. The quality verdict covers executable
checks; the standards verdict covers DRY, ownership, layer direction, public
surface, comment intent, and whether an ADR must change.

Independent task Review adds six-dimensional analysis, not another mechanical
suite. Receipts must match current code/requirements, including uncommitted and
relevant untracked contents, not just HEAD. See the
[Reviewer contract](extensions/review/templates/reviewer.md).

Quality's [execution-receipt contract](extensions/quality/commands/speckit.quality.check.md)
binds the original check to its checked inputs and configuration, including
relevant untracked inputs and staged/worktree distinctions. HEAD/path-only hooks
must be rerun; attaching today's hash to an old result does not prove execution.
