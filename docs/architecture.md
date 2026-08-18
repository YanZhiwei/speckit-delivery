# Architecture

## Product boundary

Spec Kit Delivery is a distribution layer over Spec Kit, not a fork of Spec Kit and not a replacement for a project's existing workflow. It contributes independently installable capabilities and composes them through workflows and a bundle.

## Component model

| Component | Owns | Does not own |
| --- | --- | --- |
| Core Spec Kit | Spec, Plan, Tasks, core implementation commands | ADR lifecycle, delivery evidence, provider orchestration |
| Workflow | Phase order, bounded loops, human gates, resume points | Semantic judgment hidden inside agent prose |
| Extension | A narrow command family and its artifact contract | Whole delivery orchestration |
| Bundle | Pinned component composition | Component implementation or agent integration installation |
| Delivery route command | Cross-integration lane routing and semantic loops | Durable project state |
| Router Skill | Optional host-native facade for the delivery route command | Durable project state or portable command rendering |
| Project config | Paths, commands, artifact policy, provider choice | Shared workflow policy |

Spec Kit `0.16.4` bundles can reference extensions, presets, steps, and workflows. They cannot package a coding-agent integration as a provided component. A target project must initialize or select its integration separately.

## Three control planes

```text
Agent skills       Decide and execute semantic work
Spec Kit workflow  Order phases, pause, resume, and bound loops
Machine state      Carry verdicts that prose/exit status cannot safely express
```

Spec Kit command steps stream agent output and cannot reliably branch on semantic prose. The `0.1.x` workflows therefore use explicit review gates and bounded loops. The `0.2.x` design introduces `.specify/delivery/<feature>/state.json`, written atomically by commands and read by a custom workflow step.

Proposed state shape:

```json
{
  "schema_version": "1.0",
  "feature": "cache-policy",
  "phase": "review",
  "verdict": "changes-requested",
  "pending_tasks": ["T031"],
  "blocking_findings": ["REV-004"],
  "decision_status": "proposed",
  "evidence_status": "pending"
}
```

Agent prose never becomes the sole workflow control signal.

## Decision lifecycle

```text
discover existing decisions
→ specify and clarify the problem
→ resolve governing ADRs
→ plan candidate architecture
→ create Proposed ADR
→ implement and review
→ reconcile with repository HEAD
→ finalize Accepted ADR
```

An ADR is thematic and durable. A Spec is feature-scoped. A Constitution is cross-feature governance. Final ADRs must remain understandable without ignored Spec artifacts, task identifiers, review rounds, or conversation history.

## Ralph execution contract

`tasks.md` is the only scheduling source. Ralph parses task identifiers, dependency order, parallel markers, user-story grouping, file overlap, and verification instructions. Workers receive one task or a cohesive TDD bundle. Workers report results; only the orchestrator marks a task complete after checking evidence.

Provider capability levels:

1. Native parallel delegation with isolated workers.
2. Agent-managed sequential workers with fresh task context.
3. Generic sequential execution in the current agent.

Ignored Spec artifacts require task injection. Workers in another worktree cannot assume `spec.md`, `plan.md`, or `tasks.md` exists there.

## Review and convergence

Convergence answers whether the implementation covers Spec, Plan, and Tasks. Review answers whether the resulting change is correct, compliant, secure, and maintainable. Simplification asks whether the same behavior can be carried by less surface area. Evidence selects credible checks for the actual outgoing diff.

These are separate responsibilities even when one provider executes several of them.
