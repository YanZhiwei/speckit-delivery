# Spec Kit Delivery Core

Creates project-local delivery configuration, checks installed components,
investigates and scopes a request, plans reviewable slices and merge policy,
routes delivery, and renders slice or rollup PR handoffs. Distributed defaults do
not assume a language, framework, ADR path, stack provider, or check.

## Commands and installation

Install this root with `specify extension add --dev /absolute/path/to/extensions/delivery`
in a clean target Spec Kit project, or install the version-pinned distribution.
Invoke commands through the active host, not as shell executables:

- `speckit.delivery.init`: discover and draft project-local policy.
- `speckit.delivery.doctor`: detect missing/stale components, profiles, and rule owners.
- `speckit.delivery.explore`: investigate code, history, and references; show candidate scope.
- `speckit.delivery.slice`: plan reviewable slices, classify trunk safety, and select the merge mode.
- `speckit.delivery.context`: optionally assemble an implementation-context brief.
- `speckit.delivery.route`: orchestrate the selected lane and user approvals.
- `speckit.delivery.lightweight`: perform a bounded mechanical change.
- `speckit.delivery.review-fix`: coordinate one verified, lane-owned repair pass.
- `speckit.delivery.handoff`: render an evidence-backed PR body locally.

The `$sd` facade remains thin. The router owns lane transitions and approval;
Explore owns investigation, not implementation or Bug assessment; Slice owns
review/merge boundaries and policy, not execution. Core Spec Kit continues to own
spec, plan, and tasks; Decision owns ADRs.

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

Bugfix runs the same structural exploration before official `bug.assess`, which
retains ownership of reproduction, diagnosis, and red evidence. Its existing
assessment gate reviews fault path, both trees, repair/test scope, and limitations.
The assessment is enough for a bounded fix; multiple files alone do not force a
Feature spec. Critical evidence gaps block progression. Direct workflows stop
and explain a required lane change; the router can resume the appropriate lane
with the same evidence.

Lightweight states relevant paths and runs targeted checks without full
exploration, external research, or two approval rounds. In `0.1.x`, gates are
guided human checkpoints, not automatic proof of semantic readiness.

## Delivery slices and merge policy

After plan approval and task generation, `speckit.delivery.slice` binds the real
task IDs to independently reviewable slices and writes
`.specify/delivery/<run>/slices.md`. It does not create a second queue:
`tasks.md` remains Ralph's only execution source, and `slices.md` may not add,
remove, or reorder tasks.

Each slice is classified as `standalone`, `flagged`, `integration-only`, or
`unknown`, with executable evidence. The merge mode is derived, not chosen by
preference:

- all slices standalone/flagged and linear → `stacked`;
- any integration-only slice → `integration`;
- insufficient evidence or a policy conflict → `needs_decision`.

The slice gate approves boundaries, order, classification, merge method, and
accepted risks. Ralph stops at each slice boundary and verifies the declaration:
a standalone slice gets a target-branch prefix build/test, a flagged slice gets
flag-off and flag-on evidence, and an integration-only slice gets its declared
checkpoint. A failed check returns to slice planning for reclassification.

`speckit.delivery.handoff` renders either one slice PR body or the final rollup.
Use `handoff slice=<id>` at each verified boundary to render that layer's PR
body; the workflow's final handoff uses `mode=auto` for the release slice or
rollup. Publishing and merging remain separately authorized. Stacked deliveries
merge each layer with the configured slice method; an integration delivery
squash-merges slices into the integration branch and merges the final rollup with
a merge commit. Never squash the final rollup, never rebase a shared integration
branch, and never merge the target into a stack branch. See the
[slice command](commands/speckit.delivery.slice.md) and
[plan template](templates/slices.md).

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

Each lane YAML supplies up to three safe review/repair slots, followed by final
review and an aborting gate. Actual repairs use the smaller configured
`max_review_fix_rounds` limit (default 3) and slot ceiling; attempts persist across
resume/new HEAD. Current complete pass makes remaining slots no-ops, not extra
repairs. Coverage/evidence gaps need investigation, not speculative patches.
Blocked/incomplete or exhausted unresolved findings stop delivery. These remain
guided `0.1.x` contracts, not automatic semantic evaluation by the YAML engine.

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

Once an actual feature/run identity is known, the record lives at
`.specify/delivery/<feature-or-run>/exploration.md` under the configured
`artifact_policy`; before that it stays in explicitly preserved context. Do not
invent feature paths. Update the same record; keep exact design in `plan.md` and
durable summaries self-contained when working records are ephemeral. Resume
checks the recorded HEAD and relevant working-tree changes before reusing evidence
or approval. See [artifact lifecycle](../../LIFECYCLE.md).

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
