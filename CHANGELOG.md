# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and Semantic Versioning.

## [0.4.5] - 2026-11-07

### Changed

- Delivery Handoff now renders a concise PR core and includes Slice, Rollup,
  Bugfix, architecture, UI, migration, and release details only when applicable.
- The repository and packaged fallback PR templates now record review identity,
  verification gaps, reviewer focus, and a factual local AI Code Review and repair
  history without requiring empty boilerplate sections.
- Handoff may summarize verified same-run local AI review rounds, repairs, and
  re-reviews by user-facing tool or method name while keeping native Review,
  Quality, Standards, and human approval authoritative.
- UI handoffs require comparable before/after captures labeled with their code
  revisions, or an explicit reason for missing evidence. Bugfix handoffs summarize
  initial and repeated repairs from existing owner records, retaining failed
  attempts, stable finding identities, regression results, and reviewer closure.
- Evidence prose follows the project's output-language convention or the request
  language while machine fields, raw logs, receipts, and historical records stay
  literal and immutable.

### Tests

- Added distribution contract coverage for the synchronized PR templates,
  conditional Handoff sections, verified AI review-history rules, and Evidence
  language behavior. Added behavioral evaluation inputs for repeated Bugfix
  repairs and before/after UI evidence; these have not been run as live model
  comparisons.

## [0.4.4] - 2026-11-07

### Changed

- Delivery Explore bounds concepts, research questions and stopping conditions,
  preserves rejected hypotheses and conflicting evidence, and prepares focused
  phase handoffs from existing owner outputs.
- The existing Feature Plan checkpoint includes cooperation/context planning,
  research versus implementation concurrency, integration ownership/verification,
  and role-specific reading. Ralph and Review strengthen their native input
  contracts without adding runtime fields or an automatic scheduler.
- Review's architecture dimension distinguishes justified implementation details,
  material design changes, evidenced redundancy and unresolved gaps, preserving
  necessary behavior and the existing design/Simplify/repair owners.

### Evaluations

- Added scenarios for missing/stale role context, correlated research sources,
  bounded research termination, cooperation-plan drift, and design deviations
  across Feature, Bugfix and Lightweight. These are behavioral evaluation inputs;
  clean installation and structural checks do not establish model-level results.

## [0.4.3] - 2026-11-06

### Added

- `delivery_runtime.py owner-result` builds the machine native receipt and
  normalized result from the exact pending ticket, native report, and stage
  data. It hashes run-local evidence paths, can fill empty `sha256` fields, and
  optionally delegates to the normal `record` validation, removing manual
  ticket/fingerprint/hash copying without weakening freshness checks.

### Changed

- Feature Delivery no longer dispatches a whole-run Quality Brief before Ralph.
  Ralph's task-scoped Brief remains the pre-edit advisory for each task, so the
  normal Feature path loses one redundant model round while preserving target
  paths and applicable plan constraints.

### Tests

- Runtime regressions cover generated owner results, evidence hashing, and
  one-call recording. Workflow and distribution checks assert that Feature has no
  duplicate global Brief and Ralph retains its task-scoped Brief.

## [0.4.2] - 2026-11-05

### Added

- Executable Ralph task-close transport: lock the task's branch and starting HEAD,
  require task-scoped Quality/Standards/Review receipts, and verify the actual
  committed Git blobs, modes, parent and checkbox transition. Feature completion,
  Converge and Handoff audit every task association; a final review cannot replace
  missing per-task evidence.
- Installed-runtime behavioral probes and a legacy `/sd` forwarding-shim upgrade
  fixture for OpenCode and Codex, preserving project configuration.
- A Close-owned atomic outcome writer that preserves reviewed-head provenance,
  records the verified squash merge revision, and separates current outcome from
  historical validation snapshots.

### Changed

- New inline `/sd` runs use the same runtime admission and machine guards as the
  Workflow path, with explicit same-run state and concrete legacy recovery.
- Internal review slices and remote PR grouping are decided before execution;
  a single PR may retain multiple internal slices. Slice plans identify early
  behavioral verification for high-risk assembly, concurrency and recovery work.
- Validation and release pipelines exercise task-close and outcome regressions,
  in addition to clean-project installation and the real workflow engine.

## [0.4.1] - 2026-11-04

### Changed

- Feature Delivery now guards the pre-review Quality and Standards refreshes
  with the runtime `needs` check. A current passing receipt is reused instead of
  being dispatched again, removing two redundant model rounds from the normal
  Feature path and more from resumed runs.

### Fixed

- A no-candidate Simplify scan is coordinator bookkeeping, not a new content
  input. Its `simplifications.md` report is excluded from the canonical snapshot
  when the recorded result has no candidates, so it no longer invalidates
  current Quality/Standards receipts. Reports with candidates remain governed
  inputs.

### Tests

- Full-workflow regression coverage now asserts one Quality/Standards pass on
  the happy path, a forced refresh when package documentation changes, and the
  expected refresh count after a post-review ADR mutation.

## [0.4.0] - 2026-11-04

### Added

- Added the portable Delivery runtime contract and standard-library helper for
  explicit run identity, phase/checkpoint state, native result fingerprints,
  approval receipts, stale-result rejection, and durable review/convergence
  attempt accounting under `.specify/delivery/<run>/runtime/`.
- Added `/sd` operational actions for help, status, resume, phase, and planning
  checkpoints, plus an SD-owned Core/Ralph compatibility contract that preserves
  Core command ownership and `tasks.md` as the sole execution queue.
- Added behavioral runtime and full Spec Kit engine regression coverage using
  real shell/helper transport and fake native consumers for zero/one/capped
  repair, stale results, accepted-simplification routing, and no-op convergence.
- Added an explicit planning-input manifest and authorized exact-path planning
  commit checkpoint that associates unchanged Analyze content with the resulting
  execution HEAD, without restamping changed approvals.

### Changed

- Reworked Feature, Bugfix, and Lightweight workflows to use actual runtime
  guards and conditional loops. Review repairs, convergence reassessment, and
  simplification verification are dispatched only when current results require
  them; final machine guards reject unresolved work after a successful loop cap.
- Feature slice execution now follows Slice plan → Analyze → one combined
  execution/slice gate → approval writer → planning checkpoint → Ralph.
- Quality, Standards, Review, Explore, Simplify, Ralph, Close, and Handoff
  contracts now transport same-run runtime results without replacing their
  semantic ownership or publication authorization.
- Simplify candidates are optional: a recorded rejection skips application, while
  accepted IDs are applied by the existing lane owner and verified by native
  `simplify.verify`; the native proposal remains immutable. Post-review ADR and
  decision changes refresh current Quality, Standards, Review, and simplification
  verification before Evidence/Handoff.
- Guarded workflows now require Spec Kit `>=1.2.3` and a project-verified Python
  `>=3.11` invocation (`runtime_python`); the runtime does not silently alter
  shell configuration.

### Fixed

- Delivery declares `sd` as an installer-managed alias of
  `speckit.delivery.route`, so a fresh Bundle or extension install provides
  OpenCode's `/sd` without copying facade skills. Spec Kit 1.2.3 renders the
  same alias as `$speckit-sd` in Codex Skills mode and `/speckit-sd` in Claude Code.
- Installation checks verify that the shortcut shares the router input/body,
  belongs to Delivery in the registry, is restored by reinstall, and is removed
  with the extension while project configuration is preserved.
- Quick-start and configuration guides use the actual installed host names.

## [0.3.2] - 2026-11-04

### Added

- `speckit.delivery.method` and the shared method-adapter contract add optional,
  verified design, diagnosis/testing, and review methods inside existing phases.
  Builtin remains the default; explicit local providers require fixed provenance
  and SHA-256 resource receipts and return analysis only.
- Delivery's Plan checkpoint now records sourced architecture constraints, design
  responses, verification owners/mechanisms, and honest evidence gaps, with
  stable IDs carried into Tasks, Brief, Standards, and Review.
- Feature analysis now resolves blocking slice-map/coverage findings before the
  slice gate; a Delivery-owned post-gate writer records the actual choice and
  unchanged plan fingerprint in `slices.md` for Ralph.
- Package README/projection refresh now runs before final Quality/Standards, so
  those receipts cover the documentation that Review sees.
- Method adapters distinguish invalid configuration (always blocked) from an
  unavailable valid resource (explicit builtin fallback only), and Review carries
  a structured method receipt.
- Review repairs refresh affected package README/projection evidence inside the
  same reserved attempt instead of relying on a pre-repair result.
- Ralph ships a packaged slice-execution contract so direct sliced invocations
  follow the same branch, boundary-check, and receipt sequence as workflow runs.
  Its task-closure gate also carries the applicable documentation-refresh receipt.
- Evidence requires an explicit lane/run and canonical output path, with a
  same-run identity check and a narrow legacy active-Feature fallback.

### Changed

- Restructured the README for both audiences: a Chinese default at `README.md`
  and an English version at `README.en.md`. `README.zh-CN.md` is now a redirect
  page. The new structure follows comparable Spec Kit ecosystem projects:
  positioning, capability map, three-gate delivery flow, copy-ready quick start,
  command reference, durable/ephemeral boundary, compatibility, maintainer
  workflow, and a documentation map.
- Workflows now pass explicit lane/run context to Brief, Standards, Quality,
  Docs Sync, and Evidence consumers, and preserve the design approval snapshot
  through Tasks before accepting the real gate choice.

## [0.3.1] - 2026-11-01

### Added

- `speckit.docs-sync.package-readme` creates or refreshes a package README from
  the package's real manifest, public exports, CLI, configuration, dependencies,
  and test commands. It serves users (install, quick start, API/CLI/config,
  limits, compatibility) and maintainers (boundaries, dependency direction,
  development, release, ownership).
- `extensions/docs-sync/templates/package-readme.md` is the packaged structure for
  that contract.

### Changed

- All three lane workflows run the package README node after the final
  code-affecting step and before review. For a new package, the node records two
  or three comparable public READMEs and what was adopted or rejected; for a
  changed package it reports `updated`, `unchanged-with-reason`, or `gap` per
  changed surface.
- Docs Sync configuration adds `package_readme: auto | required | off` and
  `package_roots`. `required` blocks on a missing README or unresolved fact gap;
  `auto` reports it.
- `speckit.delivery.doctor` now requires Docs Sync for every lane and verifies
  the package README command, template, and pre-review placement.
- Route, lifecycle, architecture, READMEs, evals, and distribution checks cover
  the new node.

### Upgrade notes

- Refresh Docs Sync (or the Bundle) to get the command, template, and workflow
  steps. Existing package READMEs are not rewritten automatically; the node runs
  on the next package change.
- Projects that do not want the node can set `package_readme: off`, at the cost of
  losing the explicit README-drift judgment.

## [0.3.0] - 2026-10-31

### Added

- `speckit.delivery.close` records the actual pull-request outcome and retires a
  delivery run. `merged` becomes `delivered`; a PR closed without merging becomes
  `abandoned` with one self-contained `evidence.md` retirement note; a replaced
  run becomes `superseded` with a resolvable reference.

### Changed

- Evidence now binds to the reviewed head the PR publishes plus the PR reference
  instead of requiring a merge commit that does not exist before publication;
  `speckit.delivery.close` records the outcome afterwards. This removes the
  post-merge evidence-rewrite cycle.
- Delivery commands now separate the durable `evidence.md` from run workspace
  (`exploration.md`, `slices.md`, `receipts/`, verdicts, reviews, and the
  rendered PR body). Under `artifact_policy: ephemeral` the workspace stays local.
- `speckit.delivery.doctor` reports stale or contradictory delivery records:
  workspace without evidence, an outcome missing a required reference or reason,
  an unresolved `superseded_by`, and installation/upgrade records kept under the
  delivery root instead of the project's durable evidence root.
- Route, handoff, lane references, `LIFECYCLE`, and READMEs define close-out as
  part of delivery completion; a record whose status contradicts the real PR
  outcome is not closed.

### Upgrade notes

- Existing tracked run workspaces are not removed automatically. Run
  `speckit.delivery.close` for runs whose PR already merged or closed, and let
  `speckit.delivery.doctor` list records with a missing or contradictory outcome
  before the next delivery.
- Migrate installation/upgrade records to the project's durable evidence root
  before retiring their `.specify/delivery/<id>/` copy.

## [0.2.2] - 2026-10-30

### Changed

- The packaged Delivery fallback at
  `extensions/delivery/templates/pull-request.md` is now Chinese. It applies only
  when the target project has no configured template and no repository
  `.github/pull_request_template.md`; existing project templates are never
  overwritten. A project can keep another language by setting
  `pull_request_template` or maintaining its own `.github` template.

### Upgrade notes

- Refresh Delivery (or the Bundle) to get the Chinese fallback. Handoff's
  `PR_BODY_PATH` and `--body-file` behavior are unchanged.
- The fallback is a formatting default, not a GitHub UI installation. Init still
  copies it to `.github/pull_request_template.md` only with explicit approval.

### Verification and limitations

- Distribution and installer checks verify the packaged fallback bytes; a
  behavioral evaluation covers fallback selection and project overrides.

## [0.2.1] - 2026-10-30

### Added

- `speckit.delivery.handoff` writes the reviewed body to
  `.specify/delivery/<run>/pull-request.md` (or `pull-request-<slice>.md`),
  reports `PR_BODY_PATH`, and prints a `gh pr create --body-file` hint.
- `install_pull_request_template` in `delivery-config.yml` allows Init to copy
  the packaged static fallback to `.github/pull_request_template.md` only after
  explicit approval and only when no project template exists.
- Eval 28 covers a project that installed Delivery but has no GitHub PR template.

### Fixed

- A chat-only handoff is no longer treated as durable output; the rendered body
  must exist at the reported local path.
- Installing Delivery no longer appears to change GitHub's UI template when it
  does not. GitHub reads the target repository's `.github` file unless a
  `--body-file` is supplied.
- `speckit.delivery.doctor` checks the configured PR template and the Handoff
  body-path contract.

### Changed

- The repository's default GitHub PR template is now Chinese. The extension's
  packaged fallback remains a separate formatting contract and does not replace
  a target project's `.github` template.

### Upgrade notes

- Refresh the Bundle, or Delivery plus the three workflows. Then run Handoff and
  use the printed `PR_BODY_PATH` with `gh pr create --body-file`.
- Existing project PR templates are preserved. Static installation is opt-in;
  existing `.github/pull_request_template.md` is never overwritten.
- The extension's packaged fallback remains English; translating it is a separate
  product decision from the repository's own Chinese template.

### Verification and limitations

- Distribution validation rejects a Handoff command that cannot emit
  `PR_BODY_PATH` and a `--body-file` hint; installer checks assert the rendered
  Handoff command contains the marker.
- This patch does not create, push, or merge PRs. Publishing still requires
  separate user authorization.

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

## [0.1.4] - 2026-10-29

Doctor path correction for the shared Reviewer contract.

### Fixed

- Doctor now names Review's installed
  `.specify/extensions/review/templates/reviewer.md` instead of an
  extension-relative `templates/reviewer.md`. The host rewrites bare relative
  references against the command's own extension, so `0.1.3` produced a
  nonexistent Delivery path and a false readiness blocker even though Review
  shipped and installed the template correctly.
- Distribution validation now rejects a Doctor Reviewer reference that relies on
  implicit Delivery ownership, and clean Bundle installation checks assert the
  rendered Doctor names Review for both OpenCode and Codex Skills.

### Upgrade notes

- Upgrade the Bundle, or refresh Delivery and Review together, then rerun
  `speckit.delivery.doctor` through the active host. Existing installations can
  be identified by the wrong `.specify/extensions/delivery/templates/reviewer.md`
  path in the generated Doctor command.
- No command surface, configuration format, review dimension, snapshot, repair
  budget, or runtime dependency changed. Minimum CLI requirements remain Spec Kit
  `>=0.16.4` for individual components and `>=1.2.3` for Bundle installation.

### Verification and limitations

- Repository validation and the mutation fixture cover the corrected reference;
  clean OpenCode and Codex Skills Bundle installations verify the rendered
  command and installed Review template.
- A missing local quality tool remains an environment blocker, not a Doctor path
  defect. This patch does not install, skip, or relax project quality checks.

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
