# Architecture

Spec Kit Delivery is a distribution layer over Spec Kit. It adds independently
installable delivery capabilities without replacing Spec Kit or a project's
existing workflow.

| Component | Owns | Does not own |
| --- | --- | --- |
| Core Spec Kit | Spec, Plan, Tasks, core implementation | ADR lifecycle, evidence, provider orchestration |
| Workflow | Phase order, gates, bounded loops, resume points | Semantic judgment hidden in prose |
| Extension | One narrow command family and artifact contract | Whole delivery orchestration |
| Bundle | Pinned component composition | Component implementation or host integration |
| Quality Gate | Project-local executable checks and closure verdict | DRY or architectural judgment |
| Ralph | Dependency-ready task dispatch and task completion | Planning or self-authorized task closure |

The system has three control planes:

```text
Agent skills       Semantic work
Spec Kit workflow  Phase order, gates, and bounded loops
Machine state      Verdicts that prose or exit status cannot safely express
```

In `0.1.x`, workflows use explicit gates and bounded loops. The planned `0.2.x`
state file will carry machine-readable phase and verdict transitions.

## Decision and closure lifecycle

```text
discover decisions → specify/clarify → resolve ADRs → plan
→ Proposed ADR → implement → review → reconcile HEAD → Accepted ADR
```

An ADR is thematic and durable; a Spec is feature-scoped; a Constitution is
cross-feature governance. Accepted ADRs must stand alone without ignored Spec
files, task identifiers, review rounds, or conversation history.

Ralph schedules only `tasks.md`. It may dispatch independent tasks, but only the
orchestrator can mark `[X]`, after checking changed paths, evidence, and a
current-HEAD `QUALITY_VERDICT: pass` for that task scope.

Quality checks formatting, lint, types, tests, and configured complexity. DRY,
ownership, directory boundaries, public-surface growth, and architecture
consistency remain semantic findings for Simplify, Review, and ADRs.

`speckit.quality.brief` is the pre-edit advisory layer; `speckit.quality.check`
is the post-edit closure gate. Host hooks may call the brief, but the workflow
also invokes it so the portable path does not depend on hook support.
