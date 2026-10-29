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
| Standards Review | Task or batch semantic standards verdict | Re-running mechanical quality checks |
| Code Review | Independent six-dimensional task/final analysis and finding reconciliation | Source edits, self-approved repairs, task closure |
| Delivery Review Fix | One verified, lane-owned repair pass and persistent attempt accounting | Review verdicts or a second execution queue |
| Delivery Slice | Slice boundaries, task mapping, trunk-safety classification, merge policy, and slice/rollup handoff | Requirements, task generation, source edits, review verdicts, branches, or PR creation |
| Ralph | Dependency-ready task execution, Git task commits, slice-boundary verification, and task completion | Planning or self-authorized task closure |
| Diagram | One evidence-backed view per change, in Mermaid by default | Test evidence, review judgment, or installer behavior |

The system has three control planes:

```text
Agent skills       Semantic work
Spec Kit workflow  Phase order, gates, and bounded loops
Machine state      Verdicts that prose or exit status cannot safely express
```

`0.1.x` and `0.2.x` use explicit gates and bounded loops. `0.2.x` adds delivery
slicing and merge policy; a later state file remains planned to carry
machine-readable phase and verdict transitions.

## Decision and closure lifecycle

```text
discover decisions → explore code/history/references → scope approval
→ specify/clarify → resolve ADRs → plan → Proposed ADR → design approval
→ implement → review → reconcile HEAD → Accepted ADR
```

An ADR is thematic and durable; a Spec is feature-scoped; a Constitution is
cross-feature governance. Accepted ADRs must stand alone without ignored Spec
files, task identifiers, review rounds, or conversation history.

Delivery Explore owns the evidence and candidate scope packet; it does not own
ADR policy, Bug root-cause diagnosis, or exact implementation design. The router
and workflow own scope approval and lane changes; the existing plan gate owns
design approval. Core Spec Kit retains spec/plan/tasks ownership. Current and
candidate directory trees are shown before specification; finalized paths,
responsibilities, interfaces, and tests are reviewed before tasks. See the
[Delivery contract](extensions/delivery/README.md). Lightweight changes do not
inherit the full exploration ceremony.

Direct workflows pass explicit `delivery_run`, a canonical on-disk packet path,
and the actual gate choice across host processes. Only a shared-session router
may temporarily keep context-only evidence; ephemeral direct runs still persist
ignored local files. Consumers record approval; gates do not edit artifacts.
Feature/bug identity does not relocate the run packet. Transport is not semantic judgment.

Ralph consumes only `tasks.md` as its execution queue. An approved `slices.md`
supplies review/merge boundaries only: it cannot add, remove, or reorder tasks.
The portable contract is one dependency-ready task per iteration on a clean
`ralph/<feature>` branch. With slicing enabled, the branch is
`ralph/<feature>/<slice>`: stacked slices build on the previous slice, while
integration slices build on the integration branch. Parallel execution requires
isolated worktrees and a provider-specific integration contract; it is not valid
in the shared worktree. Only the orchestrator can mark `[X]`, after checking
changed paths, evidence, and current `QUALITY_VERDICT: pass`,
`STANDARDS_VERDICT: pass`, and `REVIEW_VERDICT: pass` for that task's code and
requirements snapshot, including uncommitted/untracked contents. At a slice
boundary it also verifies the declared `standalone` prefix build/test,
`flagged` flag-off/on behavior, or `integration-only` checkpoint. It then creates
the task commit and stores the task and slice receipts in local
`.specify/delivery` state.

Delivery Slice runs after task generation so it binds real task IDs. It derives
`single`, `stacked`, or `integration` from evidence rather than preference:
`standalone`/`flagged` slices with a linear order may stack; any
`integration-only` slice forces an integration branch; unknown evidence or a
policy conflict returns `needs_decision`. The gate records actual approval. A
failed slice prefix check reopens slicing instead of silently extending the
stack. Handoff owns per-slice and rollup PR bodies, never PR creation or merges.
The merge policy is explicit: squash slice layers by default, use a merge commit
for an integration rollup, never squash the rollup, never rebase a shared
integration branch, and never merge the target into a stack branch.

Quality checks formatting, lint, types, tests, and configured complexity.
Standards Review checks DRY, ownership, directory boundaries, public-surface
growth, comment intent, and architecture consistency. Code Review reuses valid
receipts while independently assessing requirements, code quality, architecture,
correctness, security/compatibility, and test effectiveness. Plan compliance does
not excuse an evidenced design defect; material redesign returns for approval.
The [Reviewer template](extensions/review/templates/reviewer.md) owns snapshot,
coverage, verdict, and finding lifecycle policy. The coordinator persists reports;
the reviewer remains read-only. Self-review is incomplete unless explicitly accepted.

All lanes use bounded `review.run → delivery.review-fix` slots, a final review,
and an aborting gate. The repair command owns lane routing; Feature keeps
`tasks.md` as its sole queue, while Bugfix/Lightweight avoid forced Feature files.
Portable YAML offers at most three repair slots, capped further by configuration.
Attempts survive resume/new HEAD; a current complete pass makes remaining slots
no-ops. These are guided prompt contracts, not an automatic semantic state engine.
Post-review ADR or other governed changes require freshness review, and handoff
rechecks the actual content/requirements snapshot.

Quality owns original execution identity and exact-input/config hook reuse;
callers cannot relabel old hook output with current hashes. Bugfix review repairs
use Delivery's assessment-bound continuation adapter, preserving original official
fix/test reports and adding per-attempt evidence rather than bypassing their
automated overwrite refusal. Initial Bug commands remain unchanged.

`speckit.quality.brief` is the pre-edit advisory layer; `speckit.quality.check`
is the post-edit closure gate. Host hooks may call the brief, but the workflow
also invokes it so the portable path does not depend on hook support.
