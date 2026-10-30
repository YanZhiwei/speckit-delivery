---
description: "Render a durable pull-request handoff from final requirements, decisions, review, and evidence"
---

# Delivery Handoff

If `delivery_run=<id>` is supplied, use its canonical `.specify/delivery/<id>/`
reports/checkpoint and exploration reference; validate the safe id and do not
silently select another Feature/run's pass. Include Bugfix continuation evidence
when repairs followed the original official fix/test reports.

Resolve the final base/head diff and read the durable Issue, accepted ADRs,
final review verdict, evidence report, documentation status, compatibility
impact, and rollback path.

## Template resolution

Use the first applicable source, and never mix sections from two:

1. `pull_request_template` from
   `.specify/extensions/delivery/delivery-config.yml` when it names an existing
   file (project-relative or absolute);
2. `.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE.md`, or
   `docs/pull_request_template.md`;
3. the extension's own `templates/pull-request.md`;
4. the section contract below.

A configured path that does not exist is a reported gap, not a reason to
invent a template.

The selected template is a formatting contract for the body rendered here. It
does not install a GitHub pull-request template: GitHub UI and `gh pr create`
without `--body-file` read the target repository's `.github` template. Only
`speckit.delivery.init`, with explicit user approval, may install a static
project template; this command always renders the current change.

## Slice and rollup modes

Read the approved `.specify/delivery/<run>/slices.md` when present and select the
mode from the actual request, not from a default:

- `slice=<id>`: render one layer's PR body. State its goal, base branch,
  dependencies, reviewed task range, "not in this layer" deferrals, flag or
  migration behavior, merge method, and rollback. Include the stack map when
  available. This body must stand alone for a reviewer who has not read lower
  layers.
- `mode=rollup`: render the integration-to-target PR body. List every slice and
  its reviewed PR, aggregate CI/review evidence, green checkpoints, sync state,
  final merge method, and whole-feature rollback. State plainly that slice-level
  reviews are in the linked PRs and this body is an integration review, not a
  request to re-review unchanged lines.
- `mode=auto`: use the last release slice (or the final slice when none is marked
  release) for `merge_mode: stacked`, and the rollup for
  `merge_mode: integration`. A single-slice or `single` plan uses the ordinary
  PR body.
- If the merge mode, slice approval, or exact `slices.md` path is missing or
  stale, stop. Do not infer a stack from branch names or a rollup from the
  outgoing diff.

The PR body must include a **Slice / stack** table for a layer and a **Rollup**
table for the final integration PR. Lower layers use `Part of #<issue>`; only the
release or rollup uses `Closes #<issue>`. Never cite internal task IDs as the
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
- **Verification**: build, tests, standards and spec review, ADR consistency,
  diff-scoped simplification, and any repository-specific install check.
- **Documentation**, **Rollback**, **AI assistance**, **Review notes**, and a
  **Checklist**.

For bugfixes add root cause, reproduction, and regression coverage. For
lightweight changes omit irrelevant sections without removing Summary, Scope,
Impact, Verification, and Checklist.

## Merge plan

For a sliced delivery, include a merge plan derived from `slices.md` and the
project's `merge_policy`:

- order and base branch of every slice;
- slice merge method (default `squash`) and final merge method (default
  `merge-commit` for integration, never `squash`);
- target-to-integration sync method (default `merge`, never rebase a shared
  branch);
- merge queue/freeze/delete-branch behavior;
- per-slice and whole-feature rollback;
- issue-closing rule (`Part of` versus `Closes`).

Emit suggested commands only when they are applicable to the verified provider.
A native stack command, a manual bottom-up rebase sequence, and an integration
rollup command are alternatives, not a script to run blindly. Do not execute
`git push`, `gh pr create`, `gh pr merge`, or a queue mutation; publishing and
merging require separate user authorization. If the repository requires linear
history, do not recommend a final merge commit; report the policy conflict
instead of silently choosing a squash that destroys slice boundaries.

## Output

Write the complete body to a real local file under the actual run or feature
directory, honoring `artifact_policy`:

- single, final, or rollup: `.specify/delivery/<run>/pull-request.md`
- one slice: `.specify/delivery/<run>/pull-request-<slice>.md`

Use the resolved feature/run directory when no `delivery_run` was supplied; never
invent a path. Overwrite only the same mode/slice's prior body, and never clobber
unrelated delivery records. A chat-only body is not a durable handoff when a run
directory exists.

Print:

```text
PR_BODY_PATH: <actual path>
PR_CREATE_HINT: gh pr create --base <target> --head <branch> --title "<title>" --body-file <actual path>
```

Use the verified provider, target branch, head branch, and title. If any field
cannot be verified, print the body path and the unresolved fields instead of a
fabricated command. The hint is not executed; pushing, creating, and merging a PR
still require separate user authorization.

## Boundaries

Before final handoff, require the Review template's complete current
`REVIEW_VERDICT: pass` across six dimensions with coverage, accepted actual
independence, and verified prior-finding closure. Compare content/requirements
fingerprints including uncommitted files, not just HEAD. If ADR finalization,
documentation, evidence generation, or another late step changed governed inputs,
refresh review/check evidence; only explicitly declared report bookkeeping may
be excluded. Stale, blocked, or incomplete results stop handoff even if a human
clicked the earlier gate. Do not reset the repair budget to obtain a pass.

Do not cite ignored Spec/Plan files, task identifiers, review rounds, agent
identities, conversation history, or obsolete command output. Link durable
Issues and ADRs instead.

Write the body locally and report `PR_BODY_PATH`. Publishing or creating the PR
requires separate user authorization. The command is complete when every
statement reflects the actual reviewed contents, all evidence links or commands
are resolvable, and the reported body file contains the same rendered content.
