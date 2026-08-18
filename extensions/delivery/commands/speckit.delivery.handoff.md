---
description: "Render a durable pull-request handoff from final requirements, decisions, review, and evidence"
---

# Delivery Handoff

Resolve the final base/head diff and read the durable Issue, accepted ADRs, final review verdict, evidence report, documentation status, compatibility impact, and rollback path. Use the project's PR template or the installed default.

Write a self-contained PR body covering summary, motivation, included/excluded scope, acceptance-to-evidence mapping, final implementation, architecture decision links, risk/compatibility, verification, documentation, rollback, and reviewer focus.

Do not cite ignored Spec/Plan files, task identifiers, review rounds, agent identities, conversation history, or obsolete command output. Link durable Issues and ADRs instead. For bugfixes add root cause, reproduction, and regression coverage. For lightweight changes omit irrelevant sections without removing Summary, Scope, Risk, Verification, and Checklist.

Generate the body locally. Publishing or creating the PR requires separate user authorization. The command is complete when every statement reflects repository HEAD and all evidence links or commands are resolvable.
