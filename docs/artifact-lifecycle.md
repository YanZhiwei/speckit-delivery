# Artifact lifecycle

| Artifact | Owner | Default lifetime | Required final property |
| --- | --- | --- | --- |
| Constitution | Project | Durable, tracked | Governs every feature without duplicating ADRs |
| Issue | Tracker | Durable | Problem, scope, acceptance, outcome |
| `spec.md` | Feature | Project-configurable | Technology-independent behavior contract |
| `plan.md` | Feature | Project-configurable | Current implementation approach |
| `tasks.md` | Feature/Ralph | Project-configurable | Single execution queue and completion state |
| Proposed ADR | Architecture | Tracked | Baseline decision before implementation |
| Accepted ADR | Architecture | Tracked | Self-contained truth reconciled with HEAD |
| Review report | Delivery run | Ephemeral by default | Structured verdict and findings |
| Evidence report | Delivery run/PR | Durable summary | Commands, results, environment caveats |
| PR body | Pull request | Durable | Final change, risk, decisions, evidence |

## Ephemeral Spec mode

Projects may ignore Spec Kit feature artifacts, but this changes execution guarantees:

- Resume works only while the original workspace and artifacts remain.
- A worktree worker needs an injected task packet or an explicit artifact copy.
- The Issue and PR must retain the stable requirement and acceptance summary.
- ADRs must not link to ignored feature paths.
- Cleanup occurs after durable handoff, never before final review and ADR reconciliation.

Tracked mode is the safer default for distributed teams. Ephemeral mode is supported when the orchestrator owns artifact transfer and the project accepts local-only resume.
