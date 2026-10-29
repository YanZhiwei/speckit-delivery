# Delivery slice plan

Use this format for `speckit.delivery.slice`. Replace placeholders with verified
tasks, paths, commands, and policy evidence; remove example rows rather than
presenting them as repository facts. This file is a review and merge-boundary
plan, not an execution queue.

## Identity and approval

- Delivery run / canonical path: <id and `.specify/delivery/<id>/`>
- Feature / spec / plan / tasks: <actual references>
- Baseline HEAD / relevant working-tree changes: <SHA and paths>
- Design approval: <plan-gate choice, approved snapshot, accepted limitations>
- Artifact policy: tracked | ephemeral
- Planning timestamp: <date>

## Merge decision

- PR slicing: off | auto | stacked | integration
- Merge mode: single | stacked | integration | undecided
- Target branch: <branch>
- Integration branch: <branch or N/A>
- Stack provider: github-native | ghstack | graphite | manual | N/A
- Slice merge method: squash | rebase | merge
- Final merge method: merge-commit | fast-forward | N/A
- Target sync method: merge | N/A
- Merge queue: yes | no
- Delete branch after merge: yes | no
- Freeze integration before final review: yes | no
- Why this mode: <rule and evidence, not preference>

## Slice table

| ID | Goal | Kind | Depends on | Task IDs | Paths | Trunk-safe | Flag | Merge order |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | <one concern / acceptance outcome> | design/foundation/behavior/release | - | <task ids> | <paths> | standalone/flagged/integration-only/unknown | <flag or -> | 1 |

## Slice details

### S1 — <goal>

- Acceptance outcome: <observable result>
- Task IDs: <every task exactly once>
- Expected paths: <source/test/docs/migration; mark new vs modify>
- Trunk-safe: standalone | flagged | integration-only | unknown
- Evidence: <why this classification is credible>
- Target verification: <exact build/test commands, or N/A with reason>
- Flag: <name, default, kill switch, flag-off behavior, flag-off test, or N/A>
- Integration checkpoints: <required only for integration-only>
- Review focus: <what the reviewer must verify>
- Not in this slice: <deferred behavior and owning slice>
- Rollback: <flag off, revert, forward migration, or restore procedure>
- Diff budget: <files / changed lines; exclusions and any accepted exception>

## Coverage and validation

- Task coverage: <every task mapped exactly once; unmapped/spanned tasks listed>
- Requirement coverage: <acceptance requirement -> slice>
- Dependency order: <acyclic and linear for stacked; checkpoint order for integration>
- Budget exceptions: <none or explicit accepted reason>
- Policy compatibility: <branch protection, linear history, merge queue, signed commits>
- Open decisions: <none or options with cost/benefit and recommendation>

## Merge plan

- Order: <S1, S2, ...>
- Per-slice merge: <method and base>
- Final rollup: <merge commit / fast-forward / N/A>
- Target sync: <merge target into integration, frequency>
- Queue/freeze: <policy>
- Issue closure: <`Part of #...` on lower slices; `Closes #...` on the release/rollup>
- Rollback per slice: <summary table or references>

## Approval record

- SLICE_PLAN_VERDICT: ready | blocked | needs_decision
- SLICE_APPROVAL: pending
- Approved by: <recorded by the gate, not this template>
- Choice / accepted risks: <actual user decision>
- Approved mode / snapshot: <mode and HEAD/content fingerprint>

The gate records the actual approval here or in preserved context. A ready plan,
a successful command, or an agent recommendation is not approval. Re-run slice
planning when material scope, task mapping, a prefix check, or the merge policy
changes.
