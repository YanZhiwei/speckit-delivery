# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and Semantic Versioning.

## [Unreleased]

## [0.2.0] - 2026-10-30

### Added

- `speckit.delivery.slice` and the packaged `templates/slices.md` plan: bind
  real task IDs to independently reviewable slices, classify trunk safety, derive
  `single`/`stacked`/`integration`, and record merge policy and rollback before
  execution.
- Feature workflow `slice`/`slice-gate` between task generation and analysis,
  with the approved `slices.md` path forwarded to analyze, Ralph, review, and
  handoff.
- Slice-aware Ralph boundaries: `standalone` target-branch prefix checks,
  `flagged` flag-off/on evidence, `integration-only` checkpoints, and slice
  receipts without creating or merging PRs.
- Slice and rollup handoff modes, including stack maps, merge plans, issue-closing
  rules, and the prohibition on squashing a final integration rollup.
- Delivery config for `pr_slicing`, slice budgets, stack provider, and
  `merge_policy` (`slice`, `final`, `sync`, queue, branch deletion, freeze).
- Distribution checks, installer checks, and behavioral evaluations for slice
  planning, gate ordering, path propagation, prefix failures, integration
  fallback, and linear-history conflicts.

### Changed

- `speckit.delivery.init` discovers stack/flag/merge-queue/linear-history
  capability before drafting slicing policy.
- `speckit.delivery.doctor` treats a missing slice command/template/gate or an
  invalid integration merge policy as stale or blocked.
- `tasks.md` remains the only execution queue; `slices.md` is boundary metadata
  and may not add, remove, or reorder tasks.

### Upgrade notes

- Upgrade the Bundle, or refresh the Delivery extension and all three delivery
  workflows together. A copied Feature workflow without the new `slice` and
  `slice-gate` steps is stale; run `speckit.delivery.doctor` after upgrading.
- Existing projects keep a single-PR path with `pr_slicing: off`. New or updated
  configurations default to `pr_slicing: auto`, which still requires the slice
  gate when more than one slice is proposed.
- Set `stack_provider: manual` when native stacked PR support is unavailable.
  Do not claim a native provider or a merge queue that the repository does not
  have.

## [0.1.3] - 2026-10-29

Evidence-first exploration and independent review, from scope approval through
bounded repair and snapshot-checked handoff.

### Added

- Shared Reviewer template for task and integrated outgoing-diff review across
  requirements, code quality, architecture/design standards, correctness,
  security/compatibility, and test effectiveness. Reports include independence,
  content/requirements fingerprints, coverage, and stable finding IDs/states.
- `speckit.delivery.review-fix` and bounded lane-owned repair/re-review slots,
  final review gates, and post-finalization freshness checks.
- Synthetic planted-defect, omitted-finding, and stale-task-closure evaluations;
  distribution/clean-install checks for Review, repair, and Ralph resources.
- `speckit.delivery.explore` and a packaged scope template for code/CodeGraph
  investigation, related Issue/PR/commit evidence, proportionate GitHub reference
  research, and current/candidate directory trees.
- Feature scope approval before specification and finalized file/interface/test
  presentation at the existing plan gate; Bugfix structural exploration feeds
  official assessment and its repair-scope gate without duplicating diagnosis.
- Distribution regression fixtures for exploration resources and gate ordering,
  plus clean-project checks for installed command/template/workflow contents.
- Direct-workflow packet/gate dispatch seam tests using the actual Spec Kit
  consumer and isolated fake host consumers.

### Changed

- Ralph requires Quality, Standards, and independent Review before task closure;
  pre-commit receipts stay snapshot-bound and verified against the resulting commit.
- Doctor, router, and handoff reject stale, blocked, incomplete, or uncovered
  reviews. Repair budgets/finding IDs survive resume and new HEADs; Bugfix and
  Lightweight keep proportional artifacts. Portable gates remain guided contracts.
- Router and direct workflows share discovery/exploration/approval order and
  explicitly carry evidence into spec, assessment, plan, and tasks. Lightweight
  changes remain proportional; material expansion renews approval.
- Direct workflows require `delivery_run`, persist a canonical packet before
  host exit, and forward its exact path and actual gate choice. Context-only
  fallback is limited to shared-session routing.
- Bugfix review continuations preserve original official reports through a
  packaged versioned-record adapter; Quality/Standards and callers require
  original content/configuration evidence, not HEAD/path-only reuse.
- Delivery catalog/checklists report all eight commands, retaining the optional
  code-context command introduced in 0.1.2, with count validation.
- Direct Bugfix uses an explicit `bug_slug` and coordinator-verified assessment
  mapping, honoring the official assessor's output boundary. Continuation
  preserves mandatory pre/post hooks with current-round context and outcomes.

### Fixed

- Exploration evidence and actual approval choices are explicitly passed between
  direct-workflow host processes instead of relying on lost conversation context.
- Same-HEAD/same-path changes no longer justify reuse of old Quality evidence;
  original checked-input/configuration identities must match or checks rerun.
- Bugfix review repairs no longer re-invoke official commands that refuse
  automated overwrites of existing `fix.md`/`test.md`. Original reports remain
  immutable; current-round evidence and all four applicable hook phases are retained.
- An omitted finding, partial coverage, stale snapshot, or unaccepted self-review
  cannot silently become a review pass. Fixers cannot approve their own repairs.

### Upgrade notes

- Upgrade the Bundle, or refresh the affected extensions and all three delivery
  workflows together. Old copied prompts/workflows lack the new resources and
  closure contracts; run `speckit.delivery.doctor` through the active host after
  upgrading. Installing the thin `$sd` facade alone does not update these components.
- **Direct-workflow input change:** all three lanes now require `delivery_run`,
  a unique safe single-segment run ID. Bugfix additionally requires a separate
  normalized `bug_slug` with an unused assessment path for a fresh run. Reuse
  the same identities on resume; do not choose new IDs to reset repair budgets.

  ```bash
  specify workflow run feature-delivery --input delivery_run=audit-trail-01 --input spec="Add an audit trail"
  specify workflow run bugfix-delivery --input delivery_run=retry-fix-01 --input bug_slug=duplicate-retry --input report="Retries duplicate notifications"
  specify workflow run lightweight-delivery --input delivery_run=docs-fix-01 --input change="Correct a documentation heading"
  ```

- Direct workflows persist their packet under `.specify/delivery/<delivery_run>/`
  before host exit, even with ephemeral artifacts; keep the local ignored files
  for resume. Bugfix does not need full Feature Spec/Plan/Tasks solely for repairs.
- Ralph task closure now needs current Quality, Standards, and independent Review
  passes. Legacy HEAD/path-only receipts are insufficient. Repair slots are capped
  at three (or a lower configured limit); exhausting the budget never waives blockers.
- Minimum CLI requirements are unchanged: Spec Kit `>=0.16.4` for individual
  components and `>=1.2.3` for Bundle installation.

### Verification and limitations

- Local validation includes 23 distribution contract/mutation tests, five actual
  Spec Kit command/gate handoff tests with fake host consumers, four release-stamp
  tests, link/diff checks, and clean OpenCode/Codex Skills Bundle installations.
- Isolated probes exercised same-HEAD stale-hook rejection and a real Bugfix
  red-to-green repair with four mandatory hooks, immutable originals, and an
  incompatible-hook rejection. Repairs correctly remain pending independent review.
- These checks are not full business/provider integration or autonomous delivery
  end-to-end proof. `0.1.x` remains guided prompt/workflow contracts, not a new
  machine-enforced semantic state engine or equivalent execution across all hosts.

## [0.1.2] - 2026-10-28

### Added

- Delivery Diagrams extension and `speckit.diagram.render`: Mermaid by default,
  a rendered SVG/PNG/HTML asset only when the project installed a renderer, and
  an explicit `N/A` instead of an invented diagram.
- Optional pinned renderer skills under `skills/`: `archify` (v3.2.0) and
  `fireworks-tech-graph` (v1.2.0), each with provenance, commit, and SHA-256.
- PR handoff template sections for current design, change map, impact, design
  diagram, and AI assistance disclosure.
- `speckit.delivery.context`: an optional code-context brief before planning or
  diagnosis. It uses the project's local `.codegraph/` index when present,
  reports entry points, callers, and affected tests, and degrades to a partial
  brief without initializing an index.

### Changed

- `speckit.delivery.handoff` now resolves the project path, then the repository
  `.github` template, then the extension default, then its section contract.
- Code Review and Standards Review now apply four discipline checks: behavior
  over implementation tests, cause over symptom, subtraction before addition,
  and independently verifiable units.
- Quality Gate documentation explains when CRAP, duplication, and mutation
  thresholds are real gates: only through a project-owned wrapper that exits
  non-zero, never by a report-only tool.
- The Bundle now contains 10 extensions. Diagram adds no workflow step.
- Feature and Bugfix workflows add a non-blocking code-context step before
  `plan` and `assess`. A missing index or tool degrades the brief; it does not
  stop delivery. Set `code_context: off` to skip it.

### Fixed

- The `pull_request_template` default no longer points at a non-existent root
  `templates/` path. The template ships with the delivery extension, the default
  is `null`, and the handoff falls back to the repository template.

## [0.1.1] - 2026-10-28

### Added

- `Prepare release PR` workflow and `stamp_release.py` preflight: stamp all
  component/catalog versions, validate, and open a reviewed release branch
  without tagging or publishing.
- Project Quality Gate extension with project-local profiles, executable check
  discovery, and a current-HEAD task-closure verdict.
- Pre-edit Quality Brief command for injecting file-scoped rules before model
  editing.
- Standards Review command with a task-or-batch semantic closure verdict.
- Delivery Doctor command that detects stale components, missing profiles, and
  unowned documented rules before workflow execution.

### Fixed

- Workflow catalog `requires` now matches each workflow YAML, so Bundle
  installation works on Spec Kit 1.2.3 instead of failing before component
  installation.
- Bundle installation now requires Spec Kit `>=1.2.3`; individual extensions and
  workflows retain their `>=0.16.4` floor.
- Distribution validation now checks catalog URLs, manifest/workflow versions,
  workflow requirements, bundle component pins, and performs a real Bundle
  install from local release-shaped catalogs.

### Changed

- Ralph and all delivery lanes now require both mechanical quality and semantic
  standards verification before task or outgoing-diff closure.
- Ralph now bridges Spec Kit tasks with a sequential per-task loop: it creates
  or reuses a `ralph/<feature>` branch, requires a verified Git commit before
  closing each task, and emits a machine-readable completion promise only when
  the committed task queue is empty.

## [0.1.0] - 2026-08-18

### Added

- Initial Spec Kit Delivery distribution scaffold.
- Decision memory, Ralph, review, simplification, evidence, documentation sync, and handoff extensions.
- Feature, bugfix, and lightweight workflow definitions.
- Versioned catalog templates and bundle manifest.
- Agent-native router skill, PR template, documentation, and evaluation prompts.
