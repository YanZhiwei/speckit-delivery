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

`evidence.md` has two deliberately separate layers:

- the **current outcome block** is the only Close-owned statement of the run's
  current terminal status and effective delivered revision;
- validation, review, CI, and limitation entries are **historical snapshots**.
  They retain the head, requirements, observation time, and limitations that were
  true when they were recorded. A sentence such as "awaits CI" or "not merged"
  must not be read as the current outcome when it belongs to such a snapshot.

Close may create or replace only the delimited current outcome block described
below. On a legacy file with no block, the writer may add one historical-snapshot
heading/notice around the untouched remainder so its scope is explicit; it must
not rewrite native review receipts, evidence history, limitation text,
fingerprints, or a historical `reviewed_head` to make them look like the merged
revision. The machine writer is the only writer of the current block.

## Head identity and outcome proof

Keep these identities explicit and never collapse them into one `HEAD` field:

- `reviewed_head` is the concrete local revision whose bytes and requirements
  the native Review and Evidence validated. It is historical provenance.
- `original_pr_head` is the pull request's historical head at the verified
  tracker observation (`head_revision` in the observed tracker file). It may be
  equal to `reviewed_head`, but it is not renamed to `merged_revision`.
- `base_revision` is the tracker-verified target/base revision used for the
  merge-content comparison.
- `merged_revision` is the tracker-verified merge commit and the effective
  delivered revision. It may be a new squash or merge commit and must remain
  distinct from both historical heads.

A passing native review is never retagged as a review of `merged_revision`.
If the PR head changed after review, preserve both values and require explicit
content-equivalence evidence before claiming that the reviewed change was the
change delivered. A matching SHA is sufficient only where it is actually the
same revision; otherwise compare content, not labels.

For a PR outcome, Close must establish all of the following before a terminal
write:

1. The configured tracker reports the exact PR as `MERGED` or `CLOSED`, and the
   read-only observation supplies the actual merge commit when the state is
   `MERGED`.
2. `merged_revision` is a locally available, reachable commit. Do not make the
   old PR branch reachable by resetting, rewriting, deleting, or force-updating
   refs, and do not fetch an arbitrary remote branch as a workaround.
3. The merged content is proven equivalent to the verified PR content: when the
   PR head object is available locally, compare the complete base-to-head and
   base-to-merged path/mode/byte content; commit identity alone is not enough.
   If the old head object is unavailable, use an exact immutable evidence archive
   that records the same base, PR head, changed paths/modes, bytes or patch, and
   archive digest when one exists. A bare fingerprint, review report, URL, or
   limitation note is not an archive proof. When the trusted tracker head equals
   `reviewed_head`, that verified observation is the permitted clean-clone
   historical mapping (`tracker-head-mapped`); it does not claim a new Review of
   the merge commit.
4. If `reviewed_head` and `original_pr_head` differ, `published_head` must be
   explicitly bound and the same comparison, bookkeeping proof, or exact archive
   must establish that the reviewed bytes are the bytes represented by the PR
   head. Otherwise fail closed with `PR_OUTCOME: unverified`; do not relabel the
   review.

An exact archive binding uses the historical Evidence fields
`reviewed_diff_archive`, `reviewed_diff_archive_sha256`,
`reviewed_diff_archive_base`, `reviewed_diff_archive_head`, and
`reviewed_diff_archive_reviewed_head`; the archive must be an in-run regular
file containing the captured binary patch/content and its digest must match.
These fields are optional, but a partial or mismatched archive is a blocker.

Missing historical Git objects are therefore a proof limitation, not a reason
for destructive history repair. Missing proof always stops Close before status,
history, or retirement changes.

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
`superseded`. `merged_revision=<sha>` may replace `pr` only for an authorized
direct merge with no pull request; it is not a substitute for the tracker
observation of a PR merge. `override=true` plus `reason="..."` is required to
change an outcome already recorded in `evidence.md`.

For a PR `merged` or `closed` outcome, write the verified read-only tracker
observation to the exact run-relative file
`.specify/delivery/<delivery_run>/runtime/observed-pr.json` (the helper's
`--file` value is `runtime/observed-pr.json`). Do not hand-edit a merge SHA into
Evidence and do not pass a user assertion as tracker evidence. The observation
has exactly this schema; no extra keys are allowed:

```json
{
  "schema_version": 1,
  "delivery_run": "<id>",
  "lane": "feature|bugfix|lightweight",
  "provider": "github",
  "repository": "owner/name",
  "number": 31,
  "state": "MERGED",
  "head_revision": "<tracker PR head SHA>",
  "base_revision": "<tracker base SHA>",
  "merged_revision": "<tracker merge commit SHA>",
  "merged_at": "<RFC3339 timestamp>",
  "observed_at": "<RFC3339 timestamp>",
  "url": "https://github.com/owner/name/pull/31"
}
```

For `state: "CLOSED"`, keep `head_revision`, `base_revision`, `observed_at`,
and `url`, and set `merged_revision` and `merged_at` to `null`. For `MERGED`,
all revision and merge-time values are required. `number`, repository, URL,
run, lane, and PR input must identify the same PR. `observed_at` records when
this exact tracker response was obtained; it is not the merge time.

After the native tracker check, run the standard-library guard from the project
root using the verified Python invocation. The file path is run-relative to the
canonical run root:

```text
<python> .specify/extensions/delivery/scripts/delivery_runtime.py close-record --run <delivery_run> --outcome merged --pr <number-or-url> --verified --file runtime/observed-pr.json
```

Use `--outcome closed` for a verified unmerged closure. The operation validates
the exact JSON identity, checks local merge reachability and proof for
`merged`, and atomically writes the current outcome block; it does not contact the
tracker, create a commit, or retire workspace files. A nonzero result is a
blocker and the native Close must stop before any terminal write or deletion.

The only durable output is the exact
`.specify/delivery/<delivery_run>/evidence.md`. Per-run operational state and
results use `.specify/delivery/<delivery_run>/runtime/` under the central runtime
contract at `.specify/extensions/delivery/templates/runtime.md`; exploration,
slices, decision-context, code-context, simplifications, and evidence stay at
the run root. When either `runtime_stage` or `runtime_result` is supplied, require the
canonical `delivery_run`, read `.specify/extensions/delivery/templates/runtime.md`
in full, and follow that runtime contract; do not invent helper flags, paths, or
result schemas. With neither argument, do not create runtime state here except
the exact `observed-pr.json` input required by verified PR Close.

If the run directory is absent and the outcome is `closed`, report
`DELIVERY_STATUS: absent` and stop; do not create a record for a run that never
existed. For every other absent or unsafe path, stop with a concrete recovery
blocker.

## Verify the outcome before any terminal write

Read the run's `evidence.md` and resolve the historical `reviewed_head`, any
recorded `original_pr_head`, and the relevant `base_revision`. The current
outcome block, when present, is authoritative for the last Close result; older
header/body values are historical and must not be used to manufacture a new
outcome. Verify the PR through the configured tracker and save the exact
observation described above. Tracker access and an observed outcome are a hard
precondition for terminal evidence updates and any retirement deletion:

- `merged`: the observation must be `state: "MERGED"`, with the exact tracker
  `head_revision`, `base_revision`, `merged_revision`, and `merged_at`. Verify
  that the merge commit is locally available and reachable, and complete the
  PR-to-merge content proof before calling `close-record`. A closed-unmerged PR
  is a conflict, not a delivered run.
- `closed`: the observation must be `state: "CLOSED"` with null merge fields.
  If the tracker shows it was merged, stop and require `outcome=merged`; do not
  infer closure from an old Evidence limitation.
- `superseded`: the replacement named by `superseded_by` must resolve to an
  existing run directory, accepted ADR, pull request, or durable evidence file.
  A superseded run is not automatically abandoned: state whether its PR closed
  unmerged or its work was replaced before merge. If its PR is still open, report
  closing it under `FOLLOW_UP`; this command does not mutate the remote.

If credentials, the configured tracker, the exact observation file, the PR
reference, the merge commit, or the content proof are unavailable, return
`PR_OUTCOME: unverified` and the concrete limitation, then **stop before
writing terminal status fields, updating outcome history, or deleting anything**.
Do not claim a merge that was not observed or whose effective content cannot be
proved. In particular, an unreachable old PR head does not authorize a fetch,
branch rewrite, or destructive cleanup. If its verified tracker head equals the
historical `reviewed_head`, the tracker mapping is the explicit clean-clone
fallback; otherwise require the exact evidence/archive or content-equivalence
proof and block Close when it is missing.

An existing `pull_request` value of `pending`, `not-yet-published`, or another
explicit non-concrete marker may be bound to the first concrete `pr=` reference
only after that reference's tracker outcome and identity have been verified. If
the record and input both contain concrete references, normalize a numeric
reference and a URL to a canonical provider/repository/number and accept them
only when they are provably the same PR (`samePR`). A different concrete PR is
an identity conflict and stops before any write; never rewrite the record to make
it fit. The same normalization applies when a verified tracker URL and numeric
input are equivalent.

## Update the durable record after verification

When `.specify/delivery/<delivery_run>/runtime/state.json` exists, first run
`close-record` exactly as shown in the input section. The operation validates the
verified JSON, local merged commit, and content/archive proof, and atomically
replaces only the current outcome block. On a successful CLI call, the central
runtime then refreshes its hash-bound `evidence_observation`; a failed guard
stops before any Evidence/state terminal write or deletion. Do not create a new
runtime for a legacy Close
invocation; verify its original native identity/history through the same
preceding rules and use the same fail-closed proof policy.

The current block has stable delimiters so historical occurrences of the same
field names cannot be mistaken for current authority:

```text
<!-- DELIVERY_CURRENT_OUTCOME_BEGIN -->
## Current delivery outcome

- **delivery_run**: <id>
- **lane**: feature | bugfix | lightweight
- **status**: delivered | abandoned | superseded
- **outcome**: merged | closed | superseded
- **pull_request**: <canonical provider/repository/number or URL>
- **reviewed_head**: <historical reviewed SHA>
- **original_pr_head**: <historical tracker head SHA>
- **published_head_proof**: tracker-head-mapped | published-content-equivalent | published-evidence-archive
- **base_revision**: <tracker base SHA>
- **merged_revision**: <reachable effective merge SHA or null>
- **effective_head**: <merged_revision or null>
- **merged_at**: <tracker merge time or null>
- **observed_at**: <tracker observation time>
- **outcome_recorded_at**: <RFC3339 timestamp>
- **verification_file**: .specify/delivery/<delivery_run>/runtime/observed-pr.json
- **merge_proof**: diff-equivalent | evidence-archive | tracker-head-mapped | not-applicable
<!-- DELIVERY_CURRENT_OUTCOME_END -->
```

For `superseded`, retain the same current-block delimiters and add
`superseded_by` and `reason`; for `abandoned`, add `reason` and use null merge
fields. `delivered` requires the verified PR, both historical head identities,
the tracker base, a reachable `merged_revision`, a non-null merge time, and a
`diff-equivalent`, `evidence-archive`, or permitted `tracker-head-mapped` proof.
`abandoned` requires the verified closed PR and reason. `superseded` requires
`superseded_by` and reason.

The current block is the only Close-owned current status. Existing historical
headers, native report references, validation snapshots, and limitations remain
byte-for-byte unchanged. Absence of a current `status` means active. Record
what was actually verified; successful tests or review do not make an
unmerged or content-unproven change delivered.

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
REVIEWED_HEAD: <historical reviewed SHA or none>
ORIGINAL_PR_HEAD: <historical tracker PR head or none>
MERGED_REVISION: <effective reachable merge SHA or none>
EFFECTIVE_HEAD: <merged_revision or none>
MERGE_PROOF: diff-equivalent | evidence-archive | tracker-head-mapped | not-applicable | none
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
