# Spec Kit Delivery Core

Creates project-local delivery configuration, checks installed components,
investigates and scopes a request, plans internal review slices plus an
execution/publication policy, routes delivery, and renders slice or rollup PR
handoffs. Distributed defaults do not assume a language, framework, ADR path,
stack provider, or check.

## Commands and installation

Install this root with `specify extension add --dev /absolute/path/to/extensions/delivery`
in a clean target Spec Kit project, or install the version-pinned distribution.
Invoke commands through the active host, not as shell executables:

- `speckit.delivery.init`: discover and draft project-local policy.
- `speckit.delivery.doctor`: detect missing/stale components, profiles, and rule owners.
- `speckit.delivery.explore`: investigate code, history, and references; show candidate scope.
- `speckit.delivery.method`: apply a configured design, diagnosis/testing, or review method inside the existing phase.
- `speckit.delivery.slice`: plan internal review slices, classify trunk safety, and resolve execution/publication modes.
- `speckit.delivery.context`: optionally assemble an implementation-context brief.
- `speckit.delivery.route`: orchestrate the selected lane and user approvals.
- `speckit.delivery.lightweight`: perform a bounded mechanical change.
- `speckit.delivery.review-fix`: coordinate one verified, lane-owned repair pass.
- `speckit.delivery.handoff`: render an evidence-backed PR body locally.
- `speckit.delivery.close`: record the actual PR outcome and retire abandoned
  run-workspace artifacts.

Starting with `0.4.0`, the manifest declares `sd` as an alias of
`speckit.delivery.route`. The installer creates `/sd` in OpenCode,
`$speckit-sd` in Codex Skills mode, and `/speckit-sd` in Claude Code from the
same router source, with the same request input and Delivery ownership. Installing
this extension directly or through the Bundle supplies the alias; refresh and
removal manage both entries together. No facade skills need to be copied.

The router owns lane transitions and approval; Explore owns investigation, not
implementation or Bug assessment; Slice owns internal review boundaries,
execution/publication planning, and policy,
not execution. Core Spec Kit continues to own spec, plan, and tasks; Decision
owns ADRs.

## Evidence-first exploration

Explore follows the single execution contract in
[its command](commands/speckit.delivery.explore.md), using the shipped
[scope packet template](templates/exploration.md). It distinguishes existing
capability, new capability, and defect investigations from delivery lanes.
Investigations include relevant source/tests, current-project Issues/PRs/commit
diffs, and proportionate GitHub reference research with fixed versions/SHAs and
actual implementation paths. New capabilities get external research by default;
new mechanisms/architecture choices also need it. Small understood extensions
may skip with a reason. Bugfixes prioritize local evidence and implicated upstream
history. Unavailable research is a limitation, not a fabricated success.

The user sees two repository-relative trees in the conversation: current code
and candidate changes, including tests. Candidate paths are marked new, modify,
reuse, no-change, or uncertain. Complex relationships may use Mermaid/SVG;
directory trees remain required, and AI image generation is not used.

## Checkpoints and handoff

Feature runs Doctor and decision discovery, then Explore and a **scope gate before
specify**. Specify/clarify consume approved evidence. The existing **plan gate**
reviews finalized paths, file responsibilities, interfaces, tests, risks, and
scope differences before task generation. A scope decision is not detailed
design approval. Material expansion renews approval rather than silently growing
the task queue.

The [Plan checkpoint](templates/exploration.md#architecture-constraints) also owns
an `Architecture constraints` table in the actual feature's `plan.md`: source and
authority, affected paths, design response, verification owner/mechanism, and
existing/planned/semantic-only/unsupported coverage. The same design gate reviews
it; Tasks/Analyze carry its IDs and verification work, and Brief/Standards/Review
consume the applicable rows. Binding-rule exceptions follow project governance;
accepting a check limitation does not waive a rule. Doctor reports unreachable
applicable policy sources and rules with no owner/mechanism, rather than requiring
a particular architecture filename or treating an empty source list as coverage.

## Optional method adapters

`method_adapters` in `delivery-config.yml` can select external design, diagnosis,
and review methods for the existing Core Plan, worker, or reviewer context. The
default is `builtin`: no extra skill, model round, or artifact is required, and
SD works fully without an external method. An explicit `skill` provider must name
a reviewed local entrypoint, immutable revision, resource list, and SHA-256 digests;
the shared [method contract](templates/method-adapter.md) validates selection and
returns scope-bound analysis with provenance. Invalid configuration always blocks;
an unavailable valid resource may use `fallback: builtin` only when explicitly
chosen, otherwise it blocks.

Adapters return analysis only. They do not write a second plan/report, add an
approval or queue, edit tasks/ADRs/Git/tracker state, dispatch reviewers, or
decide closure. The owning phase persists the receipt and applies its normal
verification. Profile guidance is in
[design](templates/method-design.md), [diagnosis](templates/method-diagnose.md),
and [review](templates/method-review.md). The checkpoint remains usable without
them. See the pinned [method review](../../REFERENCE-REVIEW.md#architecture-skill-methods)
for adopted and rejected guidance; external skills are not automatically installed.

Bugfix runs the same structural exploration before official `bug.assess`, which
retains ownership of reproduction, diagnosis, and red evidence. Its existing
assessment gate reviews fault path, both trees, repair/test scope, and limitations.
The assessment is enough for a bounded fix; multiple files alone do not force a
Feature spec. Critical evidence gaps block progression. Direct workflows stop
and explain a required lane change; the router can resume the appropriate lane
with the same evidence.

Lightweight states relevant paths and runs targeted checks without full
exploration, external research, or two approval rounds. Historical `0.1.x`
release notes described gates as guided human checkpoints; current `0.4.x`
transport is conditional and machine-checked for identity/freshness/completeness,
while native owners and required user gates retain semantic readiness authority.

## Runtime state, resume, and conditional dispatch

The portable coordinator is installed with the extension at
`.specify/extensions/delivery/scripts/delivery_runtime.py`; its central contract is
[`templates/runtime.md`](templates/runtime.md). Run it from the project root with
Python 3.11 or later and Git on `PATH`. It uses the standard library and Git only:
it never invokes a model, runs project tests, edits product code/tasks, creates
commits, or contacts a tracker.

Initialize a run with an explicit safe `delivery_run` and lane. The canonical
root is `.specify/delivery/<delivery_run>/`; Feature or Bug slugs are metadata and
must not select or relocate it. The helper stores pending owner inputs, normalized
results, approval receipts, phase, fingerprints, and bounded-attempt counters only
under the exact `.specify/delivery/<run>/runtime/` directory. `init` adds that
exact directory and Spec Kit's operational `.specify/workflows/runs/` ledger to
Git's local `.git/info/exclude`, preserving existing entries; tracked files stay
tracked. Exploration, slices, code-context, simplifications, receipts, and
`evidence.md` keep their canonical run-root `artifact_policy`. They also remain
freshness inputs: changing one invalidates a stored Review/receipt that consumed it.

The `/sd` control surface supports five run-safe actions:

- `action=help` explains the selected lane, records, gates, runtime location, and
  next safe action without starting a lane or invoking a model.
- `action=status delivery_run=<id>` is read-only; without a run it lists runs and
  never guesses from recency.
- `action=resume delivery_run=<id>` recovers the same run's pending owner action,
  input ticket, approval, or reserved attempt without resetting identity or
  allocating a replacement.
- `action=checkpoint delivery_run=<id> stage=initial|converge|simplify|outgoing-repair`
  follows the [Core/Ralph adapter](templates/core-adapter.md), checking approved
  paths, fingerprints, Git authorization, the current Analyze result, and a clean
  execution entry. The coordinator may commit only the exact approved planning
  paths under already established project Git authorization; the helper never
  commits. It cannot stage unrelated work, approve design, or start Ralph from a
  dirty entry.
- `action=phase delivery_run=<id> name=<phase>` records the current owner phase;
  it is not a completion assertion. Handoff readiness requires current Review and
  same-run Evidence.

Shell conditions consume newline-free `needs` booleans. A false need skips the
conditional owner/model branch entirely; there are no fixed no-op model slots. A
missing, stale, malformed, or tampered native result blocks even when its host
process returned zero. Review and Converge reservations persist across resume and
new HEAD; the native repair owner consumes the reserved attempt, and the final
`require` guard rejects cap exhaustion while blockers or incomplete evidence
remain. Runtime checks identity, freshness, completeness, report/evidence hashes,
and the exact machine owner receipt that binds a normalized result to its native
report, HEAD, verdict, and evidence; Quality, Standards, Reviewer, Core, and Ralph
remain the semantic owners. A valid envelope or exit code is not automatic
semantic judging. `delivery_runtime.py owner-result` builds both files from the
pending ticket, native report, and a stage data JSON; it can fill empty evidence
hashes and optionally delegate to the normal `record` transition, removing manual
ticket/fingerprint/hash copying without weakening those checks.

Feature execution reads the SD-scoped Core compatibility contract at
[`templates/core-adapter.md`](templates/core-adapter.md). Core Tasks/Analyze/
Converge and Ralph retain their owners, `tasks.md` remains the only queue, and the
clean planning-to-execution checkpoint requires explicit approved paths,
fingerprints, Git authorization, and a clean execution entry. After slice planning,
Analyze resolves blocking map/coverage findings before the one combined
Analyze/execution/Slice gate; the Delivery writer records the actual choice before
Ralph consumes the queue. Handoff reports readiness for separately authorized
publication, not a terminal outcome; Close records only a verified external
outcome. [Doctor](commands/speckit.delivery.doctor.md) uses the current run
phase/checkpoint when judging missing Evidence, allowing a legitimate pre-Evidence
absence only when no Evidence was recorded and the required packet/checkpoint
exists. Missing post-Evidence or final-phase Evidence blocks; unrelated runs are
maintenance findings. Reusing a planning approval or Evidence record requires
unchanged relevant bytes and the same requirements/policy fingerprint; a
project-authorized planning commit may be associated only when it is content-
equivalent and limited to approved paths. Changed inputs require fresh
presentation/approval, never a restamped digest.

## Delivery slices and publication policy

After plan approval and task generation, `speckit.delivery.slice` binds the real
task IDs to independently reviewable internal slices and writes
`.specify/delivery/<run>/slices.md`. It does not create a second queue:
`tasks.md` remains Ralph's only execution source, and `slices.md` may not add,
remove, or reorder tasks.

Internal review boundaries and remote PR grouping are separate. The configured
`pr_slicing` request is `off|single|auto|stacked|integration`:

- `off` preserves one internal slice and one eventual PR;
- `single` permits multiple risk-based internal slices on the ordinary Ralph
  branch and maps all of them to one eventual PR;
- `auto` derives the publication grouping from evidence and policy before Ralph;
- `stacked` requires a target-safe linear stack with a verified provider/manual
  fallback;
- `integration` requires the declared integration branch, protected merge policy,
  and the exact integration checkpoints.

Each internal slice is classified as `standalone`, `flagged`,
`integration-only`, or `unknown`, with executable evidence. The Slice command is
the single policy owner: it resolves both the Ralph `Execution mode` and remote
`Publication mode`, records the explicit slice-to-publication-group map, and
blocks unresolved or incompatible plans. A `single` publication plan may have
multiple internal boundaries but keeps the ordinary Ralph branch; it does not
turn an `integration-only` slice into a target-safe prefix. No final handoff may
amend this choice.

Analyze runs against the planned slices before the one combined
Analyze/execution/Slice gate so blocking task map/coverage findings are resolved
first. That gate approves boundaries, order, classification, execution/publication
modes, publication groups, merge method, and accepted risks; a Delivery-owned
approval writer then records the actual choice and unchanged fingerprint in
`slices.md`. Ralph stops at each internal boundary and verifies the declaration:
a standalone slice gets a target-branch prefix build/test, a flagged slice gets
flag-off and flag-on evidence, and an integration-only slice gets its declared
checkpoint. Applicable assembly, concurrency, and recovery probes run with the
behavior-changing task/slice; a final rollup is not their first execution. A
failed check returns to slice planning for reclassification.

`speckit.delivery.handoff` consumes the approved publication groups and renders
an internal slice artifact, one PR body, stacked layer bodies, or an integration
rollup according to that plan. It writes to
`.specify/delivery/<run>/pull-request.md` (or `pull-request-<slice>.md`) and
prints `PR_BODY_PATH` plus a `gh pr create --body-file` hint. With
`pr_slicing: single`, `handoff slice=<id>` can render boundary evidence but it
does not imply a separate remote PR; final `mode=auto` renders the one approved
PR body. Installing the extension does not change GitHub's UI template: GitHub
reads the target repository's `.github` template unless `--body-file` is
supplied. `speckit.delivery.init` may install a static project template only
with explicit approval; dynamic bodies still come from handoff. Publishing and
merging remain separately authorized. Stacked deliveries merge each layer with
the configured slice method; an integration delivery squash-merges slices into
the integration branch and merges the final rollup with a merge commit. Never
squash the final rollup, never rebase a shared integration branch, and never
merge the target into a stack branch. See the [slice command](commands/speckit.delivery.slice.md)
and [plan template](templates/slices.md).

## Delivery record lifecycle

`evidence.md` is the durable, self-contained record. `exploration.md`,
`decision-context.md`, `slices.md`, `receipts/`, `task-verdicts.yml`,
`slice-verdicts.yml`, `reviews/`, and `pull-request*.md` are run workspace and
follow `artifact_policy`; when it is ephemeral, keep them local instead of
committing them. Bind evidence to the reviewed head the PR publishes plus the PR
reference, not to a merge commit that does not exist before publication. A
successful Handoff reports `HANDOFF_READY: ready` and a waiting-for-publication
or waiting-for-outcome state; it is not a terminal Delivery result.

After the PR merges or closes, run
`speckit.delivery.close outcome=merged|closed|superseded`:

- `merged` → `delivered`, with the PR or merge reference and outcome date;
- `closed` without merge → `abandoned`, with the closed PR and reason; keep one
  self-contained `evidence.md` retirement note and delete that run's workspace
  artifacts;
- `superseded` → `superseded`, with a resolvable `superseded_by` and reason.

If the PR, tracker, credentials, or observed outcome is unavailable, Close
returns `PR_OUTCOME: unverified` and stops before writing terminal status/history
or deleting any workspace. Absence of `status` means active. A record without an
accurate status is not a closed delivery. Installation, upgrade, and bootstrap records are operational
one-offs, not delivery runs; keep their authoritative copy in the project's
durable evidence root instead of maintaining a second copy under
`.specify/delivery/`. See the
[close command](commands/speckit.delivery.close.md).

## Review closure

Ralph requires Quality, Standards, and task-scoped Review before task closure.
All lanes then use integrated Review across six dimensions: requirements, code
quality, architecture/design standards, correctness, security/compatibility, and
test effectiveness. The [Reviewer contract](../review/templates/reviewer.md)
owns snapshot, independence, coverage, and finding policy; Delivery persists its
reports without making the reviewer a writer or a repair self-approver.

The [review-fix command](commands/speckit.delivery.review-fix.md) owns one repair
pass and lane routing. Feature keeps `tasks.md` as the only execution queue and
does not bypass Ralph's clean-worktree preflight; task repairs do not recurse into
Ralph. Bugfix repairs stay assessment-owned; Lightweight stays mechanical.
Design defects requiring material changes return for scope/Plan/ADR approval.

Each lane workflow conditionally dispatches bounded review/repair work, followed
by a final runtime `require` guard and an aborting gate. The configured
`max_review_fix_rounds` limit (default 3) is also capped by the portable workflow;
attempt reservations persist across resume/new HEAD, and a current complete pass
skips further repair dispatch. Coverage/evidence gaps need investigation, not
speculative patches. Blocked/incomplete or exhausted unresolved findings stop
Delivery. The runtime enforces transport and budget state; native Quality,
Standards, Reviewer, Core, and Ralph contracts—not the YAML engine—judge semantic
correctness. See the [runtime contract](templates/runtime.md) for the owner
boundary rather than duplicating workflow flags here.

Bugfix continuation uses the packaged
[adapter](templates/bugfix-review-repair.md): preserve the approved assessment
and original official fix/test reports; append per-attempt fix/regression records
instead of re-invoking commands that refuse automated report overwrites.

The adapter also preserves all four pre/post fix/test hook phases, actual
mandatory invocation/wait/results, and current round report context. Incompatible
hooks that require stale/overwritten originals block for an integration decision.

After ADR/finalization changes, refresh review if contents or requirements changed.
Handoff again checks actual fingerprints, including uncommitted and relevant
untracked contents. Missing findings never count as resolved.

## Outputs, configuration, and safety

Explore emits `EXPLORATION_VERDICT: ready | blocked` and
`SCOPE_APPROVAL: pending`. Ready only permits scope review. The router/workflow
records actual approval, approved scope, and accepted non-critical limitations.
Downstream commands read that packet, not merely the original request.

Once an actual `delivery_run` identity is known, the record lives at
`.specify/delivery/<run>/exploration.md` under the configured `artifact_policy`;
before that it stays in explicitly preserved context. Do not invent Feature
paths or relocate the packet after a Feature/Bug identity appears. Update the same
record; keep exact design in `plan.md` and durable summaries self-contained when
working records are ephemeral. Resume checks the recorded HEAD and relevant
working-tree changes before reusing evidence or approval. See [artifact lifecycle](../../LIFECYCLE.md).

For direct YAML entry, supply a unique safe `delivery_run` id up front, reusing it
on resume. The canonical run packet must be on disk before Explore exits, even
before Feature identity exists; ephemeral means a local ignored file. All direct
consumers receive its exact path; the next consumer receives and records the
actual gate choice against the reviewed scope/snapshot. Gates do not edit files.
Never move this assigned packet on later Feature/bug identification. Context-only
preservation is available only when the router truly shares one host session.

Direct Bugfix additionally requires a separate explicit normalized `bug_slug`.
Explore records the expected reference, official Assess writes only its own Bug
output, and the coordinator verifies and persists the actual assessment reference
and hash. Fresh output collisions or mismatched/missing assessments stop; the
assessor is not asked to write outside its official output boundary.

CodeGraph and network/credential access are capabilities, not mandatory installs.
Use verified source/test fallback when indexing is unavailable. No silent
indexing, dependency/skill installation, private-data upload, tracker mutation,
publishing, or execution of downloaded reference code is authorized by exploration.

## Optional code context

`speckit.delivery.context` is the optional code-context step: when the project
has a local `.codegraph/` index it reports entry points, callers, and affected
tests for the change; otherwise it degrades to a partial brief with the gaps
named. It never initializes an index and never treats the graph as correctness
evidence. `delivery-config.yml` controls it with `code_context: auto | off`.
