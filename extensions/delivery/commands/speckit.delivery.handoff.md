---
description: "Render a durable pull-request handoff from final requirements, decisions, review, and evidence"
---

# Delivery Handoff

If `delivery_run=<id>` is supplied, use its canonical `.specify/delivery/<id>/`
reports/checkpoint and exploration reference; validate the safe id and do not
silently select another Feature/run's pass. Include Bugfix continuation evidence
when repairs followed the original official fix/test reports.

Resolve the final base/head diff and read the durable Issue, accepted ADRs, final review verdict, evidence report, documentation status, compatibility impact, and rollback path. Use the project's PR template or the installed default.

Write a self-contained PR body covering summary, motivation, included/excluded scope, acceptance-to-evidence mapping, final implementation, architecture decision links, risk/compatibility, verification, documentation, rollback, and reviewer focus.

Do not cite ignored Spec/Plan files, task identifiers, review rounds, agent identities, conversation history, or obsolete command output. Link durable Issues and ADRs instead. For bugfixes add root cause, reproduction, and regression coverage. For lightweight changes omit irrelevant sections without removing Summary, Scope, Risk, Verification, and Checklist.

Before final handoff, require the Review template's complete current
`REVIEW_VERDICT: pass` across six dimensions with coverage, accepted actual
independence, and verified prior-finding closure. Compare content/requirements
fingerprints including uncommitted files, not just HEAD. If ADR finalization,
documentation, evidence generation, or another late step changed governed inputs,
refresh review/check evidence; only explicitly declared report bookkeeping may
be excluded. Stale, blocked, or incomplete results stop handoff even if a human
clicked the earlier gate. Do not reset the repair budget to obtain a pass.

Generate the body locally. Publishing or creating the PR requires separate user authorization. The command is complete when every statement reflects the actual reviewed contents and all evidence links or commands are resolvable.
