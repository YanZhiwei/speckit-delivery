---
description: "Retire a delivery run against the actual pull-request outcome and remove abandoned working artifacts"
---

# Delivery Close

Run this command after the pull request's outcome is known. Handoff renders the PR
body before publication; this command records what actually happened and retires
the run workspace. It never pushes, creates, or merges a pull request.

## Input

`delivery_run=<id>` is required. `outcome=merged|closed|superseded` is required.
`pr=<number|url>` is required for `closed` and for `merged` when a pull request
was used. `reason="<why>"` is required for `closed` and `superseded`.
`superseded_by=<run-id|ADR|PR|durable evidence path>` is required for
`superseded`. `merged_revision=<sha>` may replace `pr` for an authorized direct
merge with no pull request. `override=true` plus `reason="..."` is required to
change an outcome already recorded in `evidence.md`.

Validate the run id as one safe path segment (no separators, `..`, or absolute
path) and resolve `.specify/delivery/<delivery_run>/`. Never touch another run,
a parent directory, or a path outside that directory. If the directory is absent
and the outcome is `closed`, report `DELIVERY_STATUS: absent` and stop; do not
create a record for a run that never existed.

## Verify the outcome

Read the run's `evidence.md` and resolve the reported base/head. Verify the PR
through the configured tracker when it is available:

- `merged`: the PR state is merged; capture the PR reference, merged revision,
  and merged time. A closed-unmerged PR is a conflict, not a delivered run.
- `closed`: the PR state is closed with no merged revision. If the tracker shows
  it was merged, stop and require `outcome=merged`.
- `superseded`: the replacement named by `superseded_by` must resolve to an
  existing run directory, accepted ADR, pull request, or durable evidence file.
  A superseded run is not automatically abandoned: state whether its PR closed
  unmerged or its work was replaced before merge. If its PR is still open, report
  closing it under `FOLLOW_UP`; this command does not mutate the remote.

If credentials or the configured tracker are unavailable, record
`PR_OUTCOME: unverified` and the limitation. Do not claim a merge that was not
observed. An `evidence.md` that names a different PR than `pr=` is an identity
conflict; stop instead of rewriting it.

## Update the durable record

Write to `evidence.md` only; never rewrite its history sections. Add or update
these header fields, preserving the existing field format:

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
`README.md`, if the project uses one) and delete these run-workspace artifacts:

- `exploration.md`, `decision-context.md`, `slices.md`
- `task-verdicts.yml`, `slice-verdicts.yml`
- `receipts/`, `reviews/`
- `pull-request.md`, `pull-request-<slice>.md`

Update the durable record before deleting anything, delete only the exact names
listed above inside the resolved run directory, and never delete `evidence.md`.
Do not remove untracked files by broad glob or recursive deletion of the run
directory. If a deleted path is tracked, report it under `TRACKED_CHANGES`; the
retirement must be committed as its own reviewable change under the project's
normal authorization. For `merged`, do not delete delivered evidence or working
artifacts; keep the record and let the project's artifact policy govern its
workspace.

An operational one-off record (installation, upgrade, bootstrap, or a manual
governance action) is not a delivery run. Its durable home is the project's
evidence root. If the run only mirrors such a file, record `superseded_by` as the
durable evidence path and retire the run instead of maintaining a second copy.

## Output

```text
DELIVERY_STATUS: delivered | abandoned | superseded | absent
DELIVERY_RECORD: <path to evidence.md>
PR_OUTCOME: merged | closed | unverified | none
RETAINED: <paths or none>
RETIRED_PATHS: <paths or none>
TRACKED_CHANGES: <paths or none>
FOLLOW_UP: <commit the retirement, refresh the run, or none>
```

The command is complete when the recorded status matches the verified outcome,
`evidence.md` is self-contained, and every deleted workspace path was reported.
