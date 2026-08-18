# Decision Memory

Keeps architectural decisions durable while Spec Kit feature artifacts evolve. Configure ADR and context paths in the installed `decision-config.yml`.

## Commands

- `speckit.decision.context`: retrieve governing decisions before specification and planning.
- `speckit.decision.propose`: establish a Proposed implementation baseline after planning.
- `speckit.decision.finalize`: reconcile the final decision with reviewed code at HEAD.
- `speckit.decision.check`: detect broken links, stale citations, contradictory active decisions, and implementation drift.

Final ADRs are self-contained and never depend on ignored `spec.md`, `plan.md`, task IDs, review rounds, or conversation history.
