---
description: "Render a durable pull-request handoff from final requirements, decisions, review, and evidence"
---

# Delivery Handoff

## Input and run/output binding

Read `$ARGUMENTS`. A direct delivery workflow must supply
`lane=feature|bugfix|lightweight` and an explicit `delivery_run=<id>`. Validate
the id as one safe path segment and use only the exact canonical
`.specify/delivery/<delivery_run>/` run root and its supplied slice/exploration
paths. Never infer another active Feature/run from recency, branch, or directory
contents and never relocate a packet after Feature/Bug identity is known. A
standalone invocation without `delivery_run` renders the body inline only; it
must not discover or create a Feature path. Report `PR_BODY_PATH: inline` in that
case.

Per-run operational state/results belong under
`.specify/delivery/<delivery_run>/runtime/`, while
`exploration.md`, `slices.md`, `decision-context.md`, `code-context.md`,
`simplifications.md`, and `evidence.md` remain at the run root. Use the central
runtime owner at
`.specify/extensions/delivery/templates/runtime.md`. When either `runtime_stage` or `runtime_result` is supplied, require the
canonical `delivery_run`, read `.specify/extensions/delivery/templates/runtime.md`
in full, and follow that runtime contract; do not invent helper flags, paths, or
result schemas. With neither argument, do not create runtime state here.

If `delivery_run=<id>` is supplied, use its canonical run reports/checkpoint and
exploration reference; validate the safe id and do not silently select another
Feature/run's pass. Include Bugfix continuation evidence when repairs followed
the original official fix/test reports.

Resolve the final `base_revision`/`reviewed_head` diff and read the durable
Issue, accepted ADRs, final review verdict, evidence report, documentation
status, compatibility impact, and rollback path. Keep the historical
`reviewed_head` explicit in the handoff. If a published PR head is already
verified, record it separately as `original_pr_head`/`published_head`; otherwise
say that publication has not yet established it. Handoff must never invent or
substitute a future `merged_revision`.

## Template resolution

Use the first applicable source, and never mix sections from two:

1. `pull_request_template` from
   `.specify/extensions/delivery/delivery-config.yml` when it names an existing
   file (project-relative or absolute);
2. `.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE.md`, or
   `docs/pull_request_template.md`;
3. the installed Delivery fallback
   `.specify/extensions/delivery/templates/pull-request.md`;
4. the section contract below.

A configured path that does not exist is a reported gap, not a reason to
invent a template.

The selected template is a formatting contract for the body rendered here. It
does not install a GitHub pull-request template: GitHub UI and `gh pr create`
without `--body-file` read the target repository's `.github` template. Only
`speckit.delivery.init`, with explicit user approval, may install a static
project template; this command always renders the current change.

## Slice and publication modes

Read the approved
`.specify/delivery/<delivery_run>/slices.md` when present. The Delivery Slice
command owns the resolved `Execution mode`, `Publication mode`, and explicit
publication-group map; Handoff only renders that approved plan and must not
choose single versus stacked, create a late rollup, or repartition slices to
match observed PRs.

Require both modes, the requested `pr_slicing` value, the complete group map,
and the unchanged slice approval/snapshot before rendering. A missing, stale,
`undecided`, or classification-inconsistent value blocks. Slice approval is not
remote publication authorization.

- `slice=<id>`: render the approved internal layer/review artifact. State its
  goal, base branch, dependencies, reviewed task range, "not in this layer"
  deferrals, classification/probe evidence, flag or migration behavior, merge
  method, publication group, and rollback. Include the stack map when available.
  Under `Publication mode: single`, this artifact is an internal boundary
  summary; it is not a separate PR request.
- `mode=rollup`: render the approved integration-to-target publication group
  only when the plan contains a `rollup` group. List every mapped slice and its
  review evidence, aggregate CI/review evidence,
  green checkpoints, sync state, final merge method, and whole-feature rollback.
  State plainly that slice-level reviews are linked internal evidence or linked
  PRs according to the approved publication groups, and do not request a second
  review of unchanged lines.
- `mode=auto`: follow the approved publication groups: one ordinary PR for
  `Publication mode: single`, one layer body per group for `stacked`, and the
  approved slice groups plus rollup for `integration`. This mode renders; it
  never resolves a missing mode or amends the plan.
- If the execution/publication mode, publication groups, slice approval, or exact
  `slices.md` path is missing or stale, stop. Do not infer a stack from branch
  names, a rollup from the outgoing diff, or single publication from a one-slice
  observation.

The body must include a **Slice / stack** table for each approved layer or
internal boundary and a **Rollup** table for the final integration group when
one exists. Lower published layers use `Part of #<issue>`; only the final
published group uses `Closes #<issue>`. Never cite internal task IDs as the
requirement source.

## Required sections

Write a self-contained body that covers:

- **Summary** and **Motivation**, including the linked Issue.
- **Slice / stack** for one layer, or **Rollup** for the final integration PR,
  when the delivery is sliced.
- **Change type**: feature, bugfix, refactor, documentation, or release.
- **Current design (before)**: the entry point or component, its owner and
  dependency direction, and the invariant that constrained the change. Link the
  owning document; do not restate it.
- **What changed**: a table of location, change, and reason. One row per module
  or contract, never the raw diff.
- **Impact**: public API, commands, and config; persistence or migration;
  compatibility and upgrade path; security and permissions; performance and
  resources; dependencies and supply chain. Each row states "none" with a
  reason or names its evidence.
- **Design**: optional. Include a Mermaid block from
  `speckit.diagram.render`, or link a committed SVG. Write `N/A` with the reason
  when no durable structure changed. Never paste generated HTML into the body.
- **Architecture decisions**: links to the ADRs that constrain this work, or an
  explicit statement that no decision changed.
- **Behavior and acceptance**: requirement, result, evidence.
- **Review provenance and PR head**: `base_revision`, `reviewed_head`, content
  and requirements fingerprints, native report references, and the verified
  `original_pr_head`/`published_head` when available. State plainly that these
  are historical review/publication identities; `merged_revision` is absent
  until Close verifies the tracker outcome.
- **Verification**: build, tests, standards and spec review, ADR consistency,
  diff-scoped simplification, and any repository-specific install check.
- **Documentation**, **Rollback**, **AI assistance**, **Review notes**, and a
  **Checklist**.

For bugfixes add root cause, reproduction, and regression coverage. For
lightweight changes omit irrelevant sections without removing Summary, Scope,
Impact, Verification, and Checklist.

## Merge plan

For a sliced delivery, include the approved execution/publication plan from
`slices.md` and the project's `merge_policy`:

- resolved execution mode and Ralph branch/topology;
- publication mode and the exact slice-to-publication-group map;
- order and base branch of every slice;
- slice merge method (default `squash`) and final merge method (default
  `merge-commit` for integration, never `squash`);
- target-to-integration sync method (default `merge`, never rebase a shared
  branch);
- merge queue/freeze/delete-branch behavior;
- per-slice, per-group, and whole-feature rollback;
- issue-closing rule (`Part of` versus `Closes`);
- explicit statement that publication/merge still requires separate user
  authorization.

Emit suggested commands only when they are applicable to the verified provider.
A native stack command, a manual bottom-up rebase sequence, and an integration
rollup command are alternatives, not a script to run blindly. Do not execute
`git push`, `gh pr create`, `gh pr merge`, or a queue mutation; publishing and
merging require separate user authorization. If the repository requires linear
history, do not recommend a final merge commit; report the policy conflict
instead of silently choosing a squash that destroys slice boundaries.

## Output

When `delivery_run` is supplied, write the complete body only to the exact run
workspace path, honoring `artifact_policy`:

- single, final, or rollup: `.specify/delivery/<delivery_run>/pull-request.md`
- one approved layer or internal boundary: `.specify/delivery/<delivery_run>/pull-request-<slice>.md`

For `Publication mode: single`, a `pull-request-<slice>.md` file is an internal
review/boundary artifact and the run-level `pull-request.md` is the only body
eligible for the separately authorized one-PR publication. Overwrite only the
same mode/slice's prior body, and never clobber unrelated records. When no run is
supplied, render the complete body inline and do not create or discover a Feature
directory; use `PR_BODY_PATH: inline`.

Handoff readiness is distinct from terminal Delivery. A successful render emits
`HANDOFF_READY: ready`, but this command never writes a delivered/abandoned/
superseded terminal outcome, never changes the Close-owned current outcome block,
and never publishes, merges, closes, or mutates a tracker/PR. Before a concrete
PR is observed, the truthful state is `waiting-for-publication`; after a concrete
PR is recorded but before its merged/closed outcome is verified, it is
`waiting-for-outcome`. If an already terminal record is merely read, report
`terminal-recorded` with its observed status and do not alter it. A blocked or
stale input emits `HANDOFF_READY: blocked` and names the exact refresh or
approval needed.

When rendering validation gaps or limitations, label each one with its
`observed_at` snapshot and `reviewed_head`. For example, write "CI was awaiting
at the 2026-11-05 snapshot for reviewed_head=<sha>" rather than an unscoped
current claim that can contradict a later merge. Preserve the historical wording
in `evidence.md`; Close's unique current outcome block is the only place that
states the current terminal result.

Print:

```text
HANDOFF_READY: ready | blocked
DELIVERY_STATUS: waiting-for-publication | waiting-for-outcome | terminal-recorded | blocked
PR_BODY_PATH: <actual path or inline>
REVIEWED_HEAD: <historical reviewed SHA or unresolved>
ORIGINAL_PR_HEAD: <verified historical PR head, pending, or unresolved>
PR_CREATE_HINT: <run-bound verified gh pr create --body-file hint, or omitted>
PR_CLOSE_HINT: <after verified outcome, run speckit.delivery.close with this lane/run/ref, or omitted>
NEXT_ACTION: <one exact next action; publication or close only after its stated precondition>
```

Use the verified provider, target branch, head branch, and title. If any field
cannot be verified, print the body path/inline body and unresolved fields rather
than a fabricated command. `PR_CREATE_HINT` is omitted when its fields are not
verified; with no run, omit both command hints and make `NEXT_ACTION` the request
to rerun with an explicit `lane` and `delivery_run`. The hints are never executed
and publication/merging/closing still require separate user authorization. The
next action must say whether the user must publish first or wait for and then
verify the outcome before invoking Close.

The rendered body is run workspace, not a second durable record. Under
`artifact_policy: ephemeral`, keep the body local and publish it through
`--body-file`; the durable summary belongs in the canonical run-root
`evidence.md`.

## Boundaries

Before final handoff, require the Review template's complete current
`REVIEW_VERDICT: pass` across six dimensions with coverage, accepted actual
independence, and verified prior-finding closure. Compare content/requirements
fingerprints including uncommitted files, not just HEAD. Keep the native Review
report's `reviewed_head` and content fingerprint immutable. If a publication head
is later different, require an explicit `published_head` binding and
content-equivalence/bookkeeping proof; do not stamp the merged revision onto the
Review report. If ADR finalization, documentation, evidence generation, or
another late step changed governed inputs, refresh review/check evidence; only
explicitly declared report bookkeeping may be excluded. Stale, blocked, or
incomplete results stop handoff even if a human clicked the earlier gate. Do not
reset the repair budget to obtain a pass.

Do not cite ignored Spec/Plan files, task identifiers, review rounds, agent
identities, conversation history, or obsolete command output. Link durable
Issues and ADRs instead.

With a run, write the body locally and report its exact `PR_BODY_PATH`; without
one, report the inline body and `PR_BODY_PATH: inline`. Publishing or creating
the PR requires separate user authorization. The command is complete when every
statement reflects the actual reviewed contents, all evidence links or commands
are resolvable, and the local file (when one exists) contains the same rendered
content.
