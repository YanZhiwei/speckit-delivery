---
description: "Select, run, and report the narrowest credible verification for the actual outgoing diff"
---

# Delivery Evidence

## Input

```text
$ARGUMENTS
```

Direct delivery workflows pass an explicit identity and output contract. Treat
these arguments as transport, not as a suggestion to discover a different run:

- `lane=feature|bugfix|lightweight`
- `delivery_run=<safe-id>`
- `evidence=.specify/delivery/<delivery_run>/evidence.md`
- `exploration=.specify/delivery/<delivery_run>/exploration.md` for Feature and
  Bugfix only
- the lane's request text (Feature spec, Bugfix report, or Lightweight change);
  Bugfix must also pass its explicit `bug_slug` and official assessment path
- optional `pr=<number|url>` when a pull-request reference is already known

## Execution sequence

### 1. Establish the run and canonical output

For a direct workflow, require `lane`, `delivery_run`, and `evidence`. Accept
only a lane named above. Validate `delivery_run` as one safe path segment matching
`[A-Za-z0-9][A-Za-z0-9._-]*`; reject separators, `..`, absolute paths, traversal,
and reserved device names. The host engine's run id and a Feature slug are not a
substitute for this value.

Resolve paths from the project root and require the supplied `evidence` value to
be the project-relative, normalized, forward-slash path exactly equal to
`.specify/delivery/<delivery_run>/evidence.md`. Reject an absolute path, a path
that escapes the project, a symlinked/out-of-root destination, or a path derived
from a later Feature location or Bug slug. This exact path is authoritative for
both reading and writing; never move a packet after identity becomes known.

Feature and Bugfix direct workflows must also pass the exact project-relative
`exploration=.specify/delivery/<delivery_run>/exploration.md` path. Verify that
packet's recorded run identity before using it. Lightweight deliberately has no
exploration requirement and must not create or require Feature Spec/Plan/tasks or
an exploration packet. For Bugfix, require the explicit safe `bug_slug` and exact
project-relative `assessment=.specify/bugs/<slug>/assessment.md`; verify that
assessment exists, belongs to this run's packet, and record its content hash. They
identify the requirement source, not the Delivery output directory. Missing or
mismatched Bug identity blocks rather than choosing another Bug.

The independently installed command has one narrow legacy fallback: only when
no `delivery_run` was assigned may an explicitly supplied `feature=<safe-id>` be
used, and only when the host/project has already established that exact Feature
as the one active Feature and its matching record is present. Use the matching
`.specify/delivery/<feature>/evidence.md` path and record that legacy identity.
A bare feature name, branch name, directory scan, newest file, or single
candidate is not an established identity. If the active Feature cannot be
resolved unambiguously, stop with concrete guidance to rerun with
`delivery_run=<safe-id> evidence=.specify/delivery/<safe-id>/evidence.md` (and the
exact `exploration` path for Feature/Bugfix). Never use this fallback when an
assigned `delivery_run` exists.

If an existing canonical file's identity conflicts with the supplied lane, run,
canonical path, Feature identity, or Bug slug, stop. Do not relocate, overwrite,
choose the newest record, or repair the mismatch by changing metadata.

### 2. Bind evidence to this reviewed change

Resolve the live base, HEAD, merge-base, outgoing diff, and changed paths,
including staged, unstaged, deleted, and relevant untracked content. Read the
applicable project verification configuration, CI definitions, hooks, and changed
code. Map every material surface to the narrowest credible evidence: build or
typecheck for compiled code, focused tests for behavior, integration or migration
checks for data boundaries, contract checks for APIs, browser evidence for user
flows, documentation/link checks for docs, and security checks for trust-boundary
changes. Record commands, working directory, relevant environment, exit status,
and concise results, including disclosed CI or human follow-up gaps.

Read the actual requirement source for the lane: Feature's approved exploration
and Spec/Plan/ADR inputs, Bugfix's exact exploration and assessment plus the
original official fix/test reports, or Lightweight's bounded request and
applicable policy. Do not make Bugfix or Lightweight depend on Feature artifacts.
Use the final Review and Standards reports as evidence consumers, not as a reason
to create another review or task queue.

Record deterministic identities for the evidence:

- base, HEAD, merge-base, scope, changed-path manifest, and a content fingerprint
  of the reviewed bytes/modes;
- the requirements/design/policy inputs and a requirements fingerprint, including
  the selected optional method config/resource identity when one was used;
- `lane`, `delivery_run`, and the exact `evidence_path`;
- the actual pull-request number or URL when known, or an explicit pending/not-yet-
  published value when publication has not happened.

The fingerprints must cover actual reviewed content and requirements, not HEAD
alone. A new commit, relevant working-tree change, changed requirement, or changed
policy invalidates stale evidence. Do not invent a squash merge or other future
revision. If a supplied `pr=` conflicts with the existing same-run record, stop.

### 3. Reuse checks without relabeling old work

Read the installed Quality Check receipt contract. Reuse a passing hook or check
only when its original checked-input/content identity, configuration identity,
scope, command, working directory, relevant environment, and execution commit
still match this run. Preserve the original Quality receipts and their source;
HEAD/path-only evidence is insufficient. Missing identity, changed inputs, or a
receipt that cannot prove same-content execution requires rerunning the affected
check or reporting the concrete gap. Never stamp current hashes onto an old hook
result, relabel an old hook as this run, or silently dismiss an environment
failure.

Evidence does not own Quality, Standards, Review, task closure, repair routing, or
PR publication. It consumes their current, scope-bound records and reports gaps;
it does not edit `tasks.md`, review findings, official Bugfix reports, or old
receipts.

### 4. Write one durable same-run record

Before publication, create or update only the exact canonical `evidence` path.
The first record must include unambiguous metadata in this form (omitting only
lane-specific fields that do not apply):

```text
- **delivery_run**: <run id, or the explicitly recorded legacy Feature identity>
- **lane**: feature | bugfix | lightweight
- **evidence_path**: .specify/delivery/<run id>/evidence.md
- **exploration_path**: .specify/delivery/<run id>/exploration.md  # Feature/Bugfix
- **content_fingerprint**: <method and digest>
- **requirements_fingerprint**: <method and digest>
- **method_identity**: <selected builtin or external config/resource receipt, or not-applicable>
- **bug_slug**: <safe slug for Bugfix, or not-applicable>
- **assessment_path**: .specify/bugs/<slug>/assessment.md # Bugfix
- **assessment_hash**: <hash and method> # Bugfix
- **pull_request**: <number or URL, or explicit pending value>
```

For an existing file, validate these fields before writing. A missing or
malformed same-run identity is a blocking ambiguity, not permission to infer or
relabel. For a matching run, append the new verification/history entry or update
only the current summary while preserving prior history and the original Quality
receipts. Keep the record self-contained and disclose every material evidence
gap. A later Feature location or Bug identity is metadata inside this record; it
never changes the canonical path.

Do not write or change `status`, `outcome_recorded_at`, `merged_revision`,
`superseded_by`, or the retirement reason here. The durable record stays active
until `speckit.delivery.close` verifies the actual PR outcome and records
`delivered`, `abandoned`, or `superseded`.

## Completion

Print the exact `EVIDENCE_PATH`, `DELIVERY_RUN`, `LANE`, reviewed HEAD/content and
requirements identities, pull-request reference state, verification results, and
follow-up gaps. The command is complete only when every material changed surface
has credible evidence or a clearly owned disclosed gap, the on-disk record is at
the validated canonical path, and its metadata matches the same run. A blocked
identity or unverifiable receipt returns concrete recovery guidance instead of a
new or guessed record.
