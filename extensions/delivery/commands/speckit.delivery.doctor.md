---
description: "Check delivery component installation, policy coverage, and workflow readiness before implementation"
---

# Delivery Doctor

## Input and run binding

Read `$ARGUMENTS`. A direct workflow invocation must supply
`lane=feature|bugfix|lightweight` and an explicit `delivery_run=<id>`. Validate
that id as one safe path segment and resolve exactly
`.specify/delivery/<delivery_run>/`; the run id is not a Feature slug. Validate
any supplied output path against that run and never choose a different run by
recency, branch, directory scan, or a single matching record. A standalone
invocation without `delivery_run` may inspect project-wide installation and
policy, but returns its findings inline and must not infer an active Feature or
create a run record. A missing run in a direct workflow is a recovery blocker.

The canonical run artifacts remain at the run root, including
`exploration.md`, `slices.md`, `decision-context.md`, `code-context.md`,
`simplifications.md`, and `evidence.md`. Per-run operational state and command
results belong under `.specify/delivery/<delivery_run>/runtime/` and are local
ignored state; use the central runtime owner at
`.specify/extensions/delivery/templates/runtime.md` for their lifecycle. When either `runtime_stage` or `runtime_result` is supplied, require the
canonical `delivery_run`, read `.specify/extensions/delivery/templates/runtime.md`
in full, and follow that runtime contract; do not invent helper flags, paths, or
result schemas. With neither argument, do not create runtime state here.

Direct Bugfix also requires an explicit `bug_slug`, normalized to lowercase
kebab-case and separately identified from the run. A fresh assessment needs an
unused output path; stop on a collision before invoking the official assessor,
whose automated fallback could otherwise choose a different slug. Resume uses
the same verified recorded identity and completed checkpoint, not a fresh assess
or an unrelated existing assessment. Verify the coordinator, not official Assess,
owns persistence of the external Delivery mapping and its approval receipt.

Read `.specify/extensions.yml`, extension and workflow registries, installed
component manifests, `delivery-config.yml`, `quality-config.yml`, and the
active integration. Verify that Delivery, Decision, Ralph, Review, Simplify,
Evidence, and Quality are installed when their selected lane needs them, and that
Docs Sync is installed for every lane because each one runs the package README
node. For Bugfix, also verify the official Bug extension and its assess/fix/test
commands. Verify that Feature, Bugfix, and Lightweight workflows reference the
installed commands rather than an obsolete copy. Feature and Bugfix need the
installed `speckit.delivery.explore` command and its
`templates/exploration.md` resource. Check that Feature places exploration and
scope approval before specify, and that Bugfix consumes exploration before its
assessment/scope gate. The existing Feature plan gate must require presentation
of the finalized tree, responsibilities, interfaces, tests, and the template's
Architecture constraints coverage. Verify the final presented plan/input identity
is recorded after Decision Propose and before the plan gate, Tasks validates it
before binding the actual choice, and the workflow carries the exact packet/plan
reference, constraint IDs, and verification work into later consumers. Brief and
Standards invocations must carry explicit lane/run context; Feature supplies its
canonical exploration reference. Report an old
installation missing these contracts as stale; do not modify it silently.

Also verify Delivery ships `speckit.delivery.slice`, `templates/slices.md`, the
central `templates/runtime.md`, `templates/core-adapter.md`, and
`scripts/delivery_runtime.py`. Confirm the guarded workflows use a verified
Python 3.11+ invocation and the Spec Kit `>=1.2.3` control-flow surface; a missing
runtime resource or older host is stale, not compatible by assumption. Verify the
Feature workflow uses this exact order after plan approval/task generation:

`Slice plan → Analyze → one combined execution/slice gate →
Delivery-owned approval writer → runtime checkpoint → Ralph`.

The slice step must receive the explicit `lane`, canonical `delivery_run`,
approved design choice, and exact `.specify/delivery/<delivery_run>/slices.md`
path. Analyze must resolve blocking task-map and coverage findings before the
combined gate. That gate must cover both execution readiness and slice
boundaries; an analyze result, a context-only choice, or a separate earlier
slice choice is not approval. The post-gate writer must receive the real gate
choice and write `SLICE_APPROVAL: approved|rejected` plus the unchanged plan
fingerprint. The runtime checkpoint must be recorded before Ralph consumes the
approved plan. Ralph, final Review, and Handoff must consume that same path and
run identity. A workflow that skips this order, lets Ralph run before the
checkpoint, or lacks the post-gate approval record is stale.

Validate `pr_slicing`, `slice_warn_files`, `slice_warn_lines`,
`slice_requires_approval`, `stack_provider`, and `merge_policy`. Reject an
unknown slicing mode, non-positive budgets, `integration` with `final: squash`,
a shared integration branch configured for rebase sync, or a stacked mode that
cannot name a provider or documented manual fallback. If `slice_requires_approval`
is true, require a recorded `SLICE_APPROVAL: approved` before Ralph. Verify
`slices.md` is presented as boundary metadata, not as a second execution queue;
`tasks.md` must remain the only source of task selection and ordering.

Verify Docs Sync ships `speckit.docs-sync.run`,
`speckit.docs-sync.package-readme`, and `templates/package-readme.md`, and that
all three lane workflows place `package-readme` after the final code-affecting
step and before `review-loop`. A workflow without it is stale for package
changes. Check `package_readme` is `auto`, `required`, or `off`; a configured
package README rule with no command or template is a blocker.

Verify the configured `pull_request_template` exists when non-null. If
`install_pull_request_template` is true, require the approved static template at
`.github/pull_request_template.md` and report a mismatch as stale; if false, do
not claim GitHub UI will use the extension fallback. Verify Handoff writes a real run-bound
`PR_BODY_PATH` and prints a `gh pr create --body-file` hint; a standalone
no-run result may be inline, but must not claim a durable path or fabricate a
command.

Audit `.specify/delivery/*/evidence.md` when the delivery root exists, but
separate the supplied current run from unrelated-run maintenance. Read the
current run's phase checkpoint/packet using the central runtime contract before
judging a missing record. In a legitimate pre-Evidence active phase, an absent
`evidence.md` is allowed when no evidence was previously recorded and the
phase's required packet/checkpoint is present. A missing evidence file after
Evidence has already been recorded, a missing file for a final/terminal phase,
or a run whose previously recorded evidence disappeared is a blocker. Absence of
`status` means active only when the record exists; it is not by itself proof that
an unrecorded final run is healthy.

For the current run, report as blockers: missing required pre-Evidence
checkpoint/packet; absent previously recorded or final evidence; a `delivered`
record with no pull-request or merge reference; an `abandoned` record with no
reason; a `superseded` record whose `superseded_by` does not resolve; and an
active record whose reachable tracker shows its PR already merged or closed
without a recorded outcome. An operational one-off record (installation,
upgrade, bootstrap) maintained under the delivery root belongs in the project's
durable evidence root and is a maintenance finding unless it is the requested
run. Report unavailable remote state as `unverified` with its limitation; never
turn it into a passing record. Findings for every other run are maintenance
findings only and must not block the current run or change its identity.

Verify Review ships `.specify/extensions/review/templates/reviewer.md` and
supports task/final scopes, six dimension verdicts, independence/coverage, and
content-bound findings; Delivery ships `speckit.delivery.review-fix`; Ralph
requires `REVIEW_VERDICT` before closing a task. All three lane workflows need
bounded review/repair slots, a final review,
and an aborting review gate before delivery. Verify `max_review_fix_rounds` and
`max_convergence_rounds` are integers from 1 through 3, and explain the portable
three-slot/loop ceiling. A malformed, zero, negative, or out-of-range bound is a
blocker, not permission to default silently. A stale two-verdict Ralph or
report-less review path is a blocker, not compatibility by assumption.

Verify the Bugfix continuation adapter ships; initial official fix/test reports
must not be overwritten or their automated refusal bypassed during re-review.
Quality must emit original checked-input/configuration receipts; HEAD/path-only
hook reuse is stale, not compatible with snapshot-bound task closure.

Validate `method_adapters` when present. Only `design`, `diagnose`, and `review`
are valid keys; each must be an object with `provider: builtin|skill`; an absent
key defaults to builtin, while an unknown phase key is invalid. For `skill`, require
a project-relative/absolute `entrypoint` in a non-empty `resources` list, `origin`,
immutable `revision`, and one well-formed `sha256` digest per unique path; verify
exact local bytes and that all needed profile guidance is manifested. A `builtin`
entry must not claim external resources. Malformed/unknown fields, duplicate paths,
bad digests, or a missing entrypoint are invalid and always block. A valid
selection whose resource is missing/unreadable or whose host capability is
unavailable may use `fallback: builtin` only when explicitly configured; otherwise
it blocks. `fallback` defaults to `block`. Do not require or install an external
skill for the builtin default. Record phase/provider and either `skill-verified`,
`builtin-fallback`, or `blocked` with concrete remediation. A missing optional
method map is not a gap.

CodeGraph, network access, and GitHub credentials are investigation capabilities,
not unconditional installation prerequisites. Exploration reports fallback or
research limitations and whether they block the actual scope decision.

For every configured changed-code family, verify a Quality profile matches it,
each required command is executable as written, and every listed rule has an
owner and credible mechanism. Mechanical rules belong to Quality; semantic
rules such as DRY, ownership, and architecture must name Standards Review,
Simplify, or ADR as their owner. A rule with no mechanism is a governance gap,
not a passing rule.

For the known target area, follow architecture-policy references from agent
instructions, Constitution, active ADRs, Delivery context, Quality policy sources,
and owning-module docs. Do not require a file named `ARCHITECTURE.md` or every
source in every configuration list. A policy already reachable through a verified
reference is discovered. Report `architecture-context-unwired` when an applicable
authoritative source is missing/unreadable or will not reach its Plan/Brief/Review
consumer; cite the source, affected paths, and missing link. Report
`architecture-policy-uncovered` when a discovered binding architecture rule lacks
a verification owner or credible mechanism for those paths. Distinguish existing
executable enforcement from semantic review and planned enforcement; no checker
means no automated coverage. An empty source list alone proves neither a gap nor
coverage. When scope is not yet known, state what must be resolved during
exploration/planning instead of claiming architectural coverage. Missing optional
external skills do not block installation. Never generate policy, install skills,
or waive binding rules to make Doctor pass.

Return:

```text
SD_DOCTOR_VERDICT: pass | blocked
LANE: <feature|bugfix|lightweight|standalone>
DELIVERY_RUN: <id or none>
RUN_ROOT: <.specify/delivery/<id>/ or inline>
RUNTIME_ROOT: <.specify/delivery/<id>/runtime/ or not-applicable>
PHASE: <runtime phase or unknown>
INTEGRATION: <active integration>
COMPONENTS:
- <component>: installed | missing | stale — <evidence>
WORKFLOWS:
- <workflow>: ready | stale | missing — <evidence>
POLICY_COVERAGE:
- <rule/profile>: covered | gap — <owner and mechanism>
SLICE_POLICY:
- mode: <off|auto|stacked|integration>; provider: <verified|manual|missing>
- gate: <present|missing>; merge: <slice/final/sync>
METHOD_ADAPTERS:
- <design|diagnose|review>: builtin | skill-verified | builtin-fallback | blocked — <origin/revision/entrypoint, resource status, fallback reason>
CURRENT_RUN_BLOCKERS:
- <id or none>: <remediation>
UNRELATED_RUN_MAINTENANCE:
- <run or none>: <maintenance finding; not a current-run blocker>
BLOCKERS:
- <current-run or global id, or none>: <remediation>
RECORDS:
- <current run and optional maintenance summaries>: active | delivered | abandoned | superseded | unverified — <evidence>
```

`SD_DOCTOR_VERDICT` is blocked by installation/global policy or current-run
blockers only; unrelated-run maintenance findings do not change it. Do not edit
source code, silently install components, or repair another run. The command is
complete only after it reports concrete remediation for every current/global
blocker and labels every unrelated finding as maintenance.
