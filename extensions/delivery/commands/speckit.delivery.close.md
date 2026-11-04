---
description: "Retire a delivery run against the actual pull-request outcome and remove abandoned working artifacts"
---

# Delivery Close

Run this command after the pull request's outcome is known. Handoff renders the PR
body before publication; this command records only the verified outcome and
retires the named run workspace. It never pushes, creates, closes, or merges a
pull request, and it does not grant, request, or exercise any extra remote
permission. It may inspect the configured tracker only with already available
read access; all remote mutation remains outside this command.

## Input and run binding

Read `$ARGUMENTS`. A direct invocation must supply
`lane=feature|bugfix|lightweight` and `delivery_run=<id>`, plus
`outcome=merged|closed|superseded`. Validate the run id as one safe path segment
(no separators, `..`, absolute paths, traversal, or reserved device names) and
resolve exactly `.specify/delivery/<delivery_run>/`. Validate the recorded lane
against the explicit lane; a mismatch is a blocker. A standalone invocation
without a run cannot perform a terminal operation: return the blocker inline and
do not infer an active Feature, create a record, or write another run.

`pr=<number|url>` is required for `closed` and for `merged` when a pull request
was used. `reason="<why>"` is required for `closed` and `superseded`.
`superseded_by=<run-id|ADR|PR|durable evidence path>` is required for
`superseded`. `merged_revision=<sha>` may replace `pr` for an authorized direct
merge with no pull request. `override=true` plus `reason="..."` is required to
change an outcome already recorded in `evidence.md`.

The only durable output is the exact
`.specify/delivery/<delivery_run>/evidence.md`. Per-run operational state and
results use `.specify/delivery/<delivery_run>/runtime/` under the central runtime
contract at `.specify/extensions/delivery/templates/runtime.md`; exploration,
slices, decision-context, code-context, simplifications, and evidence stay at
the run root. When either `runtime_stage` or `runtime_result` is supplied, require the
canonical `delivery_run`, read `.specify/extensions/delivery/templates/runtime.md`
in full, and follow that runtime contract; do not invent helper flags, paths, or
result schemas. With neither argument, do not create runtime state here.

If the run directory is absent and the outcome is `closed`, report
`DELIVERY_STATUS: absent` and stop; do not create a record for a run that never
existed. For every other absent or unsafe path, stop with a concrete recovery
blocker.

## Verify the outcome before any terminal write

Read the run's `evidence.md` and resolve the reported base/head. Verify the PR
through the configured tracker when it is available. Tracker access and an
observed outcome are a hard precondition for terminal evidence updates and any
retirement deletion:

- `merged`: the PR state is merged; capture the PR reference, merged revision,
  and merged time. A closed-unmerged PR is a conflict, not a delivered run.
- `closed`: the PR state is closed with no merged revision. If the tracker shows
  it was merged, stop and require `outcome=merged`.
- `superseded`: the replacement named by `superseded_by` must resolve to an
  existing run directory, accepted ADR, pull request, or durable evidence file.
  A superseded run is not automatically abandoned: state whether its PR closed
  unmerged or its work was replaced before merge. If its PR is still open, report
  closing it under `FOLLOW_UP`; this command does not mutate the remote.

If credentials, the configured tracker, the PR reference, or the actual outcome
are unavailable, return `PR_OUTCOME: unverified` and the concrete limitation,
then **stop before writing terminal status fields, updating outcome history, or
deleting anything**. Do not claim a merge that was not observed.

An existing `pull_request` value of `pending`, `not-yet-published`, or another
explicit non-concrete marker may be bound to the first concrete `pr=` reference
only after that reference's tracker outcome has been verified. If the record and
input both contain concrete references, normalize a numeric reference and a URL
to a canonical provider/repository/number and accept them only when they are
provably the same PR (`samePR`). A different concrete PR is an identity
conflict and stops before any write; never rewrite the record to make it fit. The same normalization
applies when a verified tracker URL and numeric input are equivalent.

## Update the durable record after verification

When `.specify/delivery/<delivery_run>/runtime/state.json` exists, first run the
installed runtime helper's read-only `outcome --run <id> --outcome <observed>
--verified --pr <verified-reference>` guard from the project root, using the
project's verified Python invocation. A failed guard stops before any terminal
write or deletion. Do not create a new runtime for a legacy Close invocation;
verify its original native identity/history through the same preceding rules.

Only after the outcome and PR identity pass the preceding verification gate, write
to the exact `evidence.md` path; never rewrite its history sections. Add or
update these header fields, preserving the existing field format:

```text
- **status**: delivered | abandoned | superseded
- **pull_request**: <number or URL> (omit only for a direct merge)
- **outcome_recorded_at**: <YYYY-MM-DD>
- **merged_revision**: <sha>            # delivered only
- **superseded_by**: <reference>        # superseded only
- **reason**: <why>                     # abandoned/superseded only
```

Absence of `status` means active. `delivered` requires `status`, the PR or merge
reference, and `outcome_recorded_at`. `abandoned` requires the closed PR and the
reason. `superseded` requires `superseded_by` and the reason. Record what was
actually verified; a successful tests-and-review record does not make an
unmerged change delivered.

## Retire the run workspace

For `closed` and `superseded`, keep only `evidence.md` (and an existing run
`README.md`, if the project uses one) and delete only this exact allowlist inside
the resolved run directory:

- `exploration.md`, `decision-context.md`, `code-context.md`, `slices.md`,
  `simplifications.md`
- `task-verdicts.yml`, `slice-verdicts.yml`
- `receipts/`, `reviews/`
- `pull-request.md`, `pull-request-<slice>.md`
- `runtime/` (the per-run operational state/results directory)

Update the durable record before deleting anything. Validate every file or
named directory independently as a normalized child of the resolved run root;
for `runtime/`, additionally require the exact normalized path
`.specify/delivery/<delivery_run>/runtime/`, an in-root non-symlink directory,
and no junction/symlink escape before removing that directory. Apply the same
containment check to `receipts/` and `reviews/`. Never delete `evidence.md`,
`README.md`, a path not listed above, a sibling run, or the run directory itself.
For `pull-request-<slice>.md`, enumerate only existing files with that exact
run-local form and a slice id recorded in the approved slice plan; do not use a
wildcard to discover deletion targets. Never use a broad glob, recursive run
deletion, or a cleanup command whose target was not independently validated. For
`merged`, do not delete delivered evidence
or working artifacts; keep the record and let the project's artifact policy
govern its workspace. If a deleted path is tracked, report it under
`TRACKED_CHANGES`; the retirement must be committed as its own reviewable change
under the project's normal authorization.

An operational one-off record (installation, upgrade, bootstrap, or a manual
governance action) is not a delivery run. Its durable home is the project's
evidence root. If the run only mirrors such a file, record `superseded_by` as the
durable evidence path and retire the run instead of maintaining a second copy.

## Output

```text
DELIVERY_STATUS: delivered | abandoned | superseded | absent | blocked
DELIVERY_RECORD: <path to evidence.md or none>
PR_OUTCOME: merged | closed | unverified | none
LANE: <feature|bugfix|lightweight|unknown>
DELIVERY_RUN: <id or none>
RETAINED: <paths or none>
RETIRED_PATHS: <paths or none>
TRACKED_CHANGES: <paths or none>
FOLLOW_UP: <exact next action, or none>
```

When verification is unavailable or an identity conflict exists, emit
`DELIVERY_STATUS: blocked` and `PR_OUTCOME: unverified` (or the observed
conflict), report the exact next action, and report no terminal write or
retirement deletion. Handoff readiness is not a terminal outcome. The command
is complete only when the recorded status matches the verified outcome,
`evidence.md` is self-contained, and every deleted workspace path was reported
with its containment check.
