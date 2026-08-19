# Artifact lifecycle

| Artifact | Owner | Default lifetime | Final property |
| --- | --- | --- | --- |
| Constitution | Project | Durable | Governs every feature without duplicating ADRs |
| Issue | Tracker | Durable | Problem, scope, acceptance, outcome |
| `spec.md` / `plan.md` | Feature | Project-configurable | Behavior contract and current approach |
| `tasks.md` | Feature/Ralph | Project-configurable | Single queue and completion state |
| Proposed ADR | Architecture | Tracked | Implementation baseline before coding |
| Accepted ADR | Architecture | Tracked | Self-contained truth reconciled with HEAD |
| Review report | Delivery run | Ephemeral by default | Structured verdict and findings |
| Quality verdict | Task/Ralph run | Ephemeral by default | HEAD, scope, profiles, checks, pass/blocked |
| Evidence report | Delivery run/PR | Durable summary | Commands, results, caveats |
| PR body | Pull request | Durable | Change, risk, decisions, evidence |

## Ephemeral Spec mode

Ignoring Spec artifacts is supported, but resume then depends on the original
workspace. Cross-worktree workers need injected task packets or copied excerpts.
Issues and PRs retain the stable requirement and acceptance summary, and ADRs
must never link to ignored feature paths. Cleanup happens only after handoff,
review, and ADR reconciliation.

Tracked mode remains the safer default for distributed teams.
