# Artifact lifecycle

| Artifact | Owner | Default lifetime | Final property |
| --- | --- | --- | --- |
| Constitution | Project | Durable | Governs every feature without duplicating ADRs |
| Issue | Tracker | Durable | Problem, scope, acceptance, outcome |
| `.specify/delivery/<feature-or-run>/exploration.md` | Delivery | Follows `artifact_policy` | Code/history/reference evidence, current/candidate trees, actual scope approval and limitations |
| `spec.md` / `plan.md` | Feature | Project-configurable | Behavior contract and current approach |
| `tasks.md` | Feature/Ralph | Project-configurable | Single execution queue; closure requires current verdict receipts |
| `.specify/delivery/<run>/slices.md` | Delivery Slice | Follows `artifact_policy` | Approved slice boundaries, trunk-safety evidence, merge policy, and rollback; never a second execution queue |
| `.specify/delivery/<feature>/task-verdicts.yml` | Ralph | Ephemeral | Task snapshot, Quality/Standards/Review receipts, and verified commit association |
| `.specify/delivery/<feature>/slice-verdicts.yml` | Ralph | Ephemeral | Slice base/head, task range, prefix/flag/checkpoint evidence, and merge-mode verdict |
| Proposed ADR | Architecture | Tracked | Implementation baseline before coding |
| Accepted ADR | Architecture | Tracked | Self-contained truth reconciled with HEAD |
| `reviews/<scope>/review.yml` under the actual delivery run | Coordinator | Follows `artifact_policy` | Snapshot, six verdicts, independence, coverage, stable finding IDs |
| Review repair checkpoint | Coordinator | Same run lifetime | Attempt count/cap and unresolved IDs preserved across resume/new HEAD |
| Quality verdict | Task/Ralph run | Ephemeral by default | HEAD, scope, profiles, checks, pass/blocked |
| Standards verdict | Task/Ralph run | Ephemeral by default | Snapshot/scope, semantic rules and blockers |
| Evidence report | Delivery run/PR | Durable summary | Commands, results, caveats |
| `.specify/delivery/<run>/pull-request.md` | Delivery Handoff | Follows `artifact_policy` | Rendered PR body and body path for `gh pr create --body-file`; not the GitHub UI template |
| PR body | Pull request | Durable | Change, risk, decisions, evidence |

`slices.md` is a review and merge-boundary plan. It binds the real `tasks.md`
IDs, but it never adds, removes, or reorders tasks. A slice receipt is evidence
for one boundary; it does not replace task receipts or the final integrated
review. Delete or refresh stale slice plans when scope, design, task mapping, a
prefix check, or the merge policy changes.

## Ephemeral Spec mode

Ignoring Spec artifacts is supported, but resume then depends on the original
workspace. Cross-worktree workers need injected task packets or copied excerpts.
Issues and PRs retain the stable requirement and acceptance summary, and ADRs
must never link to ignored feature paths. Cleanup happens only after handoff,
review, and ADR reconciliation.

Tracked mode remains the safer default for distributed teams.

Before the actual feature/run identity exists, preserve the exploration packet
in context without inventing a path. Persist it when the location is known, then
update the same record. Spec and plan consume its evidence; exact implementation
design stays in plan. Revalidate the HEAD and relevant working-tree changes on
resume; material scope changes need renewed approval. If the packet is ephemeral,
durable Issues, ADRs, and handoff summaries cannot depend on its path or chat history.

That context-only fallback applies only to a shared-session router. Direct YAML
entry obtains an explicit `delivery_run` first and persists the packet at its
canonical path before dispatch returns. Ephemeral policy still needs an ignored
local file. Later Feature/bug identity is recorded in that packet, not a reason
to relocate it. Consumers receive exact references and actual gate choices;
gates do not edit the packet or implicitly approve ready output.

## Review and repair records

The [Reviewer contract](extensions/review/templates/reviewer.md) owns finding and
snapshot rules. A report is bound to base/HEAD/merge-base plus actual contents and
requirements, not HEAD alone. Uncommitted and relevant untracked files count.
Only declared bookkeeping may be excluded; ADR/spec/test/source changes invalidate
reuse. Preserve `open → fixed-pending-review → resolved` or evidence-backed
`dismissed` dispositions. Omission, a new snapshot, or a fixer's claim closes nothing.

Task receipts identify pre-commit review and may associate it with the resulting
commit only after content equivalence is verified. They are not relabeled as final
HEAD reviews; final Review owns integration coverage. Coordinator records must
not create tracked post-commit dirtiness. Keep the repair budget through resume,
and preserve unresolved findings on exhaustion. Late governed changes require
fresh review before handoff; ephemeral reports need self-contained durable summaries.

Bugfix review continuations preserve the original assessment/fix/test reports.
Per-round repair/regression evidence lives under the actual bug's
`review-repairs/<delivery-run>/round-<n>/`, linked from the coordinator checkpoint.
Original hook/check receipts retain the identity of the inputs/configuration
actually executed; missing identity forces a rerun, not a current-hash relabel.
