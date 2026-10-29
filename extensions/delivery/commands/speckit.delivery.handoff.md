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

## Required sections

Write a self-contained body that covers:

- **Summary** and **Motivation**, including the linked Issue.
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

Generate the body locally. Publishing or creating the PR requires separate user
authorization. The command is complete when every statement reflects the actual
reviewed contents and all evidence links or commands are resolvable.
