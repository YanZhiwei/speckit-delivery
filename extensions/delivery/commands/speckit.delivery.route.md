---
description: "Route and orchestrate a complete Spec Kit delivery across feature, bugfix, and lightweight lanes"
---

# Spec Kit Delivery Route

## Input

```text
$ARGUMENTS
```

Read project governance and `.specify/extensions/delivery/delivery-config.yml`
when present. Identify the requested change and repository state. Select exactly
one proportional lane:

- **Feature** for new behavior, cross-module work, durable data, public API,
  security, or architectural change.
- **Bugfix** for a reproducible defect with bounded scope; establish red
  evidence before the correction.
- **Lightweight** for a mechanical, documentation-only, or
  behavior-preserving change.

Before mutation, announce the lane, durable records, Spec artifact policy,
integration capability, and verification entry points.

For Feature, run the installed Spec Kit commands in this sequence:

`speckit.specify → speckit.clarify → speckit.decision.context → speckit.plan → speckit.decision.propose → speckit.tasks → speckit.analyze → speckit.ralph.run → speckit.converge → speckit.simplify.scan → speckit.docs-sync.run (when configured) → speckit.review.run → speckit.decision.finalize → speckit.decision.check → speckit.evidence.collect → speckit.delivery.handoff`.

Treat `tasks.md` as the only execution queue. When a review or convergence
finding remains, add or reopen a task and repeat `analyze → ralph → review`.
Keep an ADR Proposed until the reviewed repository HEAD matches it; Accepted
ADRs must be self-contained and cannot depend on ignored Spec artifacts.

For Bugfix, assess, reproduce, write red evidence, correct, verify, review,
and collect evidence. Escalate to Feature when the investigation exposes a
material architecture or durable-contract decision.

For Lightweight, invoke `speckit.delivery.lightweight`, then produce targeted
evidence and a concise handoff. The command is complete only when its selected
lane has no blocking finding, all durable records match repository HEAD, and
the outgoing diff is supported by credible evidence.
