---
description: "Route and orchestrate a complete Spec Kit delivery across feature, bugfix, and lightweight lanes"
---

# Spec Kit Delivery Route

## Input

```text
$ARGUMENTS
```

## Operational actions

The router also owns the small `/sd` control surface. An empty `/sd` or
`/sd help` maps to `action=help`; `/sd status [run]`, `/sd resume <run>`, and
`/sd checkpoint <run> stage=initial|converge|simplify|outgoing-repair` map to the
corresponding actions below. Use an explicit
`delivery_run=<id>` to disambiguate a request containing those ordinary words.
Operational actions return after their own completion; do not fall through into
new delivery routing. They must not start a lane implicitly:

- `action=help` prints the selected lane commands, required durable records,
  runtime location, approval gates, and the next safe action; it does not invoke
  a model or mutate the project.
- `action=status delivery_run=<id>` runs the installed standard-library helper
  from the project root:
  `<verified-python> .specify/extensions/delivery/scripts/delivery_runtime.py status --run <id> --json`.
  With no run, use the same command without `--run` to list runs. Report pending
  owner tickets, stale results, reserved attempts, phase, and the exact next
  action; do not infer a different run from recency.
- `action=resume delivery_run=<id>` runs `resume --run <id> --json`, then resumes
  only the reported owner/action with the same run identity. A pending result,
  reservation, or approval is recovered explicitly; it is never reset or
  allocated again. If the run is legacy/corrupt, report the recovery blocker.
- `action=checkpoint delivery_run=<id> stage=initial|converge|simplify|outgoing-repair`
  reads `.specify/extensions/delivery/templates/core-adapter.md` and the central
  runtime contract in full. Verify the current passing Analyze result, actual
  unchanged scope/design/slice approvals, exact approved planning paths, branch,
  base, and project Git authorization. When project policy or an earlier actual
  user decision already authorizes the exact planning commit, stage only those
  planning paths and create that commit; do not ask again. When the project's
  artifact policy intentionally keeps some approved planning files ignored and no
  commit is required, record `planning_commit: none` with that authorization and
  do not force-add ignored files. If those exact paths are
  already present at the current HEAD with the approved identity and the worktree
  is clean (for example after an interrupted retry), record the existing commit
  instead of creating a duplicate. Declared run operational records (runtime,
  reviews, receipts, verdicts, evidence, PR bodies) and Spec Kit's workflow-run
  ledger may remain local; any source, planning, test, policy, or unrelated dirty
  path blocks. A missing authorization, changed design/mapping, or branch/base
  conflict blocks with the adapter's concrete recovery. Never stash/reset or stage a broad glob.
  Write the exact native planning-input manifest at
  `.specify/delivery/<delivery_run>/runtime/planning-inputs-<checkpoint-ticket>.json`
  (the ticket from `input-checkpoint.json`, or an explicit stable
  `checkpoint_id` for a native nested outgoing-repair checkpoint; one immutable
  file per checkpoint) with
  `schema_version: 1`, this run/lane, the actual authorization statement/evidence,
  and every exact path plus `source_owner` (`core`, `decision`, or `adr`). Only
  bound Spec/Plan/Tasks, actual Core outputs (research/data-model/quickstart/
  contracts/checklist), this run's canonical planning files (`exploration.md`,
  `code-context.md`, `decision-context.md`, `slices.md`), or a Proposed ADR under
  the configured ADR directory may appear; no wildcard or unrelated path.
  Save the native `SD_CORE_HANDOFF: PASS|BLOCKED` at exactly
  `.specify/delivery/<delivery_run>/runtime/core-handoff.md` and, when runtime
  arguments are supplied, reference that file from the `checkpoint` result with the
  actual planning stage, approved paths, entry base, branch, and authorization
  citation. The helper verifies the manifest, commit range, and unchanged Analyze
  content, then associates it with the resulting HEAD. It never commits or grants
  permission itself.
- `action=bind-assessment lane=bugfix delivery_run=<id> bug_slug=<slug>` is the
  Delivery-owned post-gate writer. Verify the exact bound official assessment,
  actual `assessment_approval` choice, and runtime presentation bytes; append its
  path/hash, approved repair scope, and accepted limitations to this run's
  `exploration.md`. A mismatch blocks before writing. Official Assess and Decision
  Context do not own this external packet write.
- `action=apply-simplification delivery_run=<id>` consumes only the candidate IDs
  from the immutable native proposal and the actual same-run Simplify gate receipt.
  Preserve that proposal; keep execution/acceptance bookkeeping in runtime.
  Feature routes the accepted local work through the Core task owner (regenerated
  Tasks or append-only Converge, never the read-only scan), then renewed Slice
  mapping, Analyze, the combined gate, the authorized planning checkpoint, and
  Ralph. Bugfix uses the assessment-bound continuation
  adapter with a reserved attempt and preserves original official fix/test reports;
  Lightweight delegates the same bounded work to `delivery.lightweight`. Scope,
  design, or durable-contract expansion stops for its owning approval. This action
  owns routing through existing lane owners; it does not hand-edit the queue or
  replace their closure checks. After application, return to native Simplify Verify,
  fresh Quality/Standards, and independent Review; never self-approve resolution.
- `action=phase delivery_run=<id> name=<phase>` records only the current owner
  phase through `phase`; it does not assert semantic completion. `handoff` is
  accepted only after current Review and same-run Evidence pass.

`action=help|status|resume|checkpoint|phase` with no explicit run is an inline
response (except status listing); do not create a run or guess an active Feature.
The runtime helper never invokes a model, edits product code/tasks, commits, or
contacts a tracker. Read `.specify/extensions/delivery/templates/runtime.md`
when a command receives `runtime_stage`/`runtime_result`; native Quality,
Standards, Reviewer, Core, Ralph, Evidence, and Close contracts remain their
owners.

Read project governance and `.specify/extensions/delivery/delivery-config.yml`
when present. Identify the requested change and repository state. Select one
provisional, proportional lane; confirm or change it after investigation:

- **Feature** for new behavior, cross-module work, durable data, public API,
  security, or architectural change.
- **Bugfix** for a reported defect expected to have bounded scope; assessment
  must establish reproduction/red evidence before the correction. Multiple
  affected files alone do not require Feature.
- **Lightweight** for a mechanical, documentation-only, or
  behavior-preserving change.

Before mutation, announce the lane, durable records, Spec artifact policy,
integration capability, and verification entry points.

## Runtime admission for new work

For every new delivery run, including inline `/sd` orchestration, verify the
installed runtime and its task/outcome companion helpers before planning or
execution. Resolve and announce one explicit safe `delivery_run`; a new run may
use a descriptive or generated safe ID without an extra approval question.
Reuse a supplied ID unchanged. Run the helper's `init` for the selected lane,
and use the same `begin`/`record`, decision, checkpoint and `require` transitions
as the installed lane Workflow. Once Core emits the real Feature path, bind that
path; never derive or relocate the run from it. Prefer running the installed
Workflow when the host supports it; inline orchestration has the same machine
guards and may not replace them with prose verdicts.

An older installation or a legacy run without original state/receipts must be
reported before execution with its concrete upgrade/recovery action. Version
registration and an installed `/sd` alias alone are insufficient. Do not upgrade
an active run by inventing task passes or resetting its repair counters. Preserve
project configuration and already recorded approvals on a controlled update.
Feature continuation must run `require --kind task-closure` after Ralph, before
Converge closes, and before Evidence/Handoff. The central runtime contract owns
the task-close transport; native Ralph remains its task/commit owner.

When invoking direct YAML workflows, obtain an explicit safe `delivery_run` id
and pass it unchanged (including resume and lane changes). Their command steps
are separate host processes: Explore must persist the canonical run packet before
returning, and consumers receive its exact path plus the actual gate choice. Use
the command/template's transport contract; context alone does not cross processes.
In shared-session orchestration, explicitly preserved context remains allowed
until a real run location is assigned. Never move an assigned canonical packet
when the Feature/bug identity later becomes known.

## Investigation and approval

For Feature and Bugfix, invoke `speckit.delivery.explore` after Doctor and
`speckit.decision.context mode=discover`. That command owns code/history/reference
research and the scope packet format; do not duplicate its investigation or
make GitHub/CodeGraph availability an unconditional installation requirement.

Before Feature specification, show the exploration packet's current directory
tree and candidate change tree in the conversation, with evidence, alternatives,
excluded scope, risks, and open questions. Obtain explicit user scope approval;
`EXPLORATION_VERDICT: ready` is not approval. Stop on decision-critical evidence
gaps or rejection. Record the approved scope, actual user decision, and explicitly
accepted non-critical research limitations in the packet or preserved context.
If the capability already exists, narrow the request instead of rebuilding it.

For Bugfix, pass exploration to `speckit.bug.assess`, which retains ownership of
reproduction and root-cause diagnosis. At its assessment gate, show both trees,
the fault path, red evidence, proposed repair, and excluded scope before asking
for scope approval. Missing reproduction is not a confirmed diagnosis or
permission to fix. Escalate to Feature only for new capability, material
architecture, or durable-contract decisions; carry evidence forward rather than
repeating the investigation. If a direct workflow must change lanes, stop it and
resume the appropriate workflow after explaining the reason.
Do not add a separate pre-assessment scope-approval round for Bugfix; the existing
assessment gate is its scope checkpoint. A blocked packet can still feed
authorized read-only assessment to collect missing evidence, but cannot authorize
specification or repair.

Pass the latest exploration packet to assessment; pass the scope-approved packet
(or explicitly preserved evidence when no feature path exists yet) to specify,
clarify, plan, and task generation.
Persist the packet once the real feature/run location is known, honoring
`artifact_policy`; do not invent a feature path before specify creates one.
Before choosing the Feature design, follow the plan-checkpoint section of the
installed `delivery/templates/exploration.md`. It owns architecture constraint
sources, optional skill methods, comparison, and verification coverage. Keep the
`Architecture constraints` table in the actual feature's `plan.md`; present it
with the finalized tree, file responsibilities, interfaces, test paths/commands,
risks, and scope differences at the existing plan gate. Pass its applicable IDs
and verification work into Tasks, check coverage in Analyze, and carry those rows
into the pre-edit brief and task/final review. After Decision Propose, record the
presented snapshot before the plan gate; verify it before consuming that gate's
choice, using the shared checkpoint contract. Pass explicit lane/run context and
the canonical Feature packet or exact plan excerpts to Brief/Standards consumers;
do not infer an active Feature from historical files. A changed constraint or verification
mechanism changes the reviewed design; refresh affected approval and receipts.
Optional `method_adapters` for design, diagnosis/testing, or review run inside
those existing phases, not as new lanes or approval rounds. The default is
builtin; an explicit external provider must pass the shared method contract's
local-resource and provenance checks. It returns analysis only and cannot take
over Plan/Tasks, official Bug assessment, review closure, or execution.
Scope approval does not approve this detailed design. Reuse an explicit prior
approval only when it covers the unchanged evidence and design; do not ask the
same question after every command. Material expansion during planning or execution
reopens scope/design approval; ordinary in-scope test additions do not.

## Feature

Run the installed Spec Kit commands in this sequence, honoring the scope,
clarification, plan, and analysis gates just as the Feature YAML workflow does:

`runtime init → doctor → decision.context (discover) → explore → scope approval → specify/bind → clarify → clarification approval (only for a real decision) → decision.context (resolve) → plan → decision.propose → plan approval → tasks → delivery.slice → analyze → combined execution/slice approval → slice approval writer → planning checkpoint → ralph.run (task-scoped quality.brief inside each iteration) → quality.check → review.standards → converge (execute/reassess only if tasks appended) → simplify.scan (approve/apply/verify only if candidates accepted) → docs-sync.run (when configured) → docs-sync.package-readme → current Quality/Standards → guarded Review/repair → final review gate → decision.finalize → decision.check → freshness checks → evidence.collect → delivery.handoff → (after the authorized PR outcome) delivery.close`.

Slice planning runs after task generation so it binds real task IDs. It does not
rewrite or replace `tasks.md`; `tasks.md` remains the only execution queue and
`slices.md` supplies internal review boundaries plus the approved execution/
publication plan. Present the slice table, trunk-safety evidence, resolved
execution/publication modes, publication-group map, merge policy, and any
exception or open decision at `slice-gate` after analysis has resolved blocking
task-map/coverage findings. After the gate, the Delivery-owned
`action=record-approval` writer records the actual choice and unchanged
fingerprint; Ralph consumes that record, not a context-only or pre-analysis
approval. A `needs_decision` result is not approval: present bounded options with
a recommendation and stop until the user chooses. If a task spans slices,
return to `speckit.tasks`; do not hand-edit the queue. Material scope or design
changes reopen the relevant approval and slice planning.

At each verified slice boundary, `speckit.delivery.handoff slice=<id>` may
render an internal boundary artifact or an approved layer body; under
`Publication mode: single` it does not imply a separate remote PR. The final
handoff uses `mode=auto` strictly according to the approved publication groups.
Do not push, create, or merge a PR without separate user authorization.

Treat `tasks.md` as the only execution queue. When a standards, review, or convergence
finding remains, have the Core task owner (append-only Converge or a Tasks
regeneration) add or reopen work, then repeat the renewed Slice → Analyze →
combined gate → approval writer → authorized planning checkpoint → Ralph →
Quality/Standards/Review path. Never hand-edit or reorder the Core queue. A
quality blocker, missing profile, unavailable configured check, or blocked
standards verdict is a delivery blocker, not a passing warning.
Keep an ADR Proposed until the reviewed repository HEAD matches it; Accepted
ADRs must be self-contained and cannot depend on ignored Spec artifacts.

## Review and repair orchestration

Ralph requires task-scoped `speckit.review.run` before its checkbox/commit gate,
in addition to Quality and Standards. Slice boundaries add the declared
prefix/flag/checkpoint verification, but they do not replace final integrated
review. Final review uses `scope=outgoing-diff` and the installed Review
template's six dimensions, including cross-slice contracts and end-to-end
behavior; task or slice approvals do not prove integration correctness. The
reviewer is read-only and independent where possible; unavailable independence
must be declared, not silently simulated.

Match each lane's YAML: record one initial native Review, then use runtime
`needs --kind repair` to enter the bounded repair loop only when a current
confirmed repairable blocker exists. Reserve its attempt before editing and pass
`attempt=<n>` unchanged to the repair owner. Refresh Quality/Standards and the
independent Review, complete that reservation, and recheck runtime need. A current
complete pass skips all further model repair/review dispatches. The final runtime
`require --kind review` and human review gate both remain mandatory. Honor the
lower configured `max_review_fix_rounds` and hard three-pass ceiling; never reset
attempts after a resume/new HEAD. A review without a repair consumes no budget.
Cap exhaustion, incomplete coverage, and unrepairable scope/design blockers stop
instead of being waived.

Persist the reviewer report and stable finding states as coordinator-owned local
records. The report template owns snapshot/coverage/aggregation rules. Before
accepting a task or final pass, verify all dimensions, actual independence or
accepted degradation, the current content/requirements fingerprints, coverage,
and every earlier finding's explicit disposition. No report prose or exit code
replaces this gate. Reviewer fixes cannot be self-approved.

After ADR finalization, decision checks, or other post-review mutations, invoke
`review.run` again if needed to refresh the final snapshot; reuse an unchanged
complete pass instead of repeating the same review. Do not hide ADR/spec/source
changes as bookkeeping or reset the repair budget. Evidence/handoff cannot
proceed on stale, blocked, or incomplete review.

## Outcome and retirement

Handoff ends before publication. Once the user separately authorizes publishing
and the pull request actually merges or closes, run `speckit.delivery.close` with
the observed outcome. A merged run becomes `delivered`; a PR closed without
merging becomes `abandoned` and keeps one self-contained `evidence.md`
retirement note; a replaced run becomes `superseded` with a resolvable reference.
Delete only the run-workspace artifacts inside that run, never `evidence.md` or
another run.

One-off operational records (installation, upgrade, bootstrap, or manual
governance action) are not delivery runs. Keep their authoritative record in the
project's durable evidence root instead of maintaining a second copy under
`.specify/delivery/`.

Do not report a delivery as complete while its durable record still has no
`status` or contradicts the actual pull-request outcome.

## Package README

Before review, `speckit.docs-sync.package-readme` judges every package touched by
the outgoing diff. It derives the README from the manifest, public exports, CLI,
configuration, dependencies, and real test commands; for a new package it records
two or three comparable public READMEs and what was adopted or rejected. It emits
`PACKAGE_README_VERDICT` plus per-package `created | updated | unchanged |
missing | blocked`. A README-affecting surface cannot be `unchanged` without the
still-correct lines cited. Under `package_readme: required`, a missing section or
unresolved fact gap blocks review; `auto` reports it. Internal-only changes no-op.

## Bugfix

Run `doctor → decision.context (discover) → explore → bug.assess → assessment/scope
approval → decision.context (resolve) → quality.brief → bug.fix → bug.test`, then
the Bugfix workflow's quality, standards, simplification, package README,
bounded review/fix loop, review gate, decision check, review freshness check,
evidence, and handoff steps. After the authorized PR outcome, close the run with
`speckit.delivery.close`. Reuse the assessment as the bounded repair contract;
do not require a full Feature spec or a second root-cause report.

## Lightweight and completion

For Lightweight, follow its existing YAML sequence:
`doctor → quality.brief → delivery.lightweight → simplify.scan (apply/verify only
accepted candidates) → docs-sync.package-readme → quality.check →
review.standards → bounded review/fix loop → final review gate → evidence.collect
→ delivery.handoff`, then close the run after the authorized PR outcome. State the relevant paths and intended small scope;
do not require full exploration, external research, or two approval rounds for a
mechanical change. The local routing command completes at `HANDOFF_READY` only when the selected
lane has no blocker, current Review/Quality/Standards and evidence match the
outgoing contents, and a usable PR body exists. Report the separately authorized
publication/outcome as the exact pending action. Terminal delivery completion
requires Close's recorded status to match the observed external outcome.
