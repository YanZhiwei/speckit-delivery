# Delivery slice plan

Use this format for `speckit.delivery.slice`. Replace placeholders with verified
tasks, paths, commands, and policy evidence; remove example rows rather than
presenting them as repository facts. This file is the approved internal review
boundary and execution/publication plan, not an execution queue. The
[Delivery Slice command](../commands/speckit.delivery.slice.md) is the sole
owner of the derivation and validation policy; Ralph and Handoff consume this
snapshot and must not infer or repartition publication at the end.

## Identity and approval

- Delivery run / canonical path: <id and `.specify/delivery/<id>/`>
- Feature / spec / plan / tasks: <actual references>
- Baseline HEAD / relevant working-tree changes: <SHA and paths>
- Design approval: <plan-gate choice, approved snapshot, accepted limitations>
- Artifact policy: tracked | ephemeral
- Planning timestamp: <date>

## Execution and publication decision

- `pr_slicing` request: off | single | auto | stacked | integration
- Internal review slicing: single | multiple
- Execution mode: single | stacked | integration | undecided
- Merge mode (legacy alias for execution mode): single | stacked | integration | undecided
- Publication mode: single | stacked | integration | undecided
- Publication grouping: <one PR for all slices | one PR/layer | slice PRs plus integration rollup>
- Publication authorization: pending — slice approval does not authorize remote publication
- Target branch: <branch>
- Integration branch: <branch or N/A>
- Stack provider: github-native | ghstack | graphite | manual | N/A
- Slice merge method: squash | rebase | merge
- Final merge method: merge-commit | fast-forward | N/A
- Target sync method: merge | N/A
- Merge queue: yes | no
- Delete branch after merge: yes | no
- Freeze integration before final review: yes | no
- Why this execution/publication choice: <rule and evidence, not preference>

## Slice table

| ID | Goal | Kind | Depends on | Task IDs | Paths | Trunk-safe | Flag | Merge order | Publication group |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | <one concern / acceptance outcome> | design/foundation/behavior/release | - | <task ids> | <paths> | standalone/flagged/integration-only/unknown | <flag or -> | 1 | P1 |

## Publication groups

Map every internal slice to exactly one group before the slice gate. This is a
plan for later, separately authorized remote publication; it is not a PR
creation instruction.

| Group | Kind | Internal slices | Remote base/head shape | Publication artifact | Issue relation | Authorization |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | layer | S1, S2, ... | <ordinary branch → target / ordered layer / integration branch> | <one PR / layer PR> | <Part of / Closes / N/A> | pending |
| P-final | rollup | <all slices; reference only> | <integration branch → target> | <rollup PR> | Closes | pending |

For `pr_slicing: single`, use one `layer` group containing all internal slices
and Ralph uses the ordinary feature branch. For `stacked`, use one ordered
`layer` group per slice. For `integration`, use one `layer` group per slice and
one `rollup` group whose all-slice reference is not a second slice assignment.
Do not change this map during Handoff to match available PRs.

## Slice details

### S1 — <goal>

- Acceptance outcome: <observable result>
- Task IDs: <every task exactly once>
- Expected paths: <source/test/docs/migration; mark new vs modify>
- Trunk-safe: standalone | flagged | integration-only | unknown
- Publication group: <P1; every slice must map exactly once>
- Evidence: <why this classification is credible>
- Target verification: <exact build/test commands, or N/A with reason>
- Flag: <name, default, kill switch, flag-off behavior, flag-off test, or N/A>
- Integration checkpoints: <required only for integration-only>
- Risk probes: <assembly/concurrency/recovery commands and expected evidence, or N/A with reason>
- Review focus: <what the reviewer must verify>
- Not in this slice: <deferred behavior and owning slice>
- Rollback: <flag off, revert, forward migration, or restore procedure>
- Diff budget: <files / changed lines; exclusions and any accepted exception>

## Coverage and validation

- Task coverage: <every task mapped exactly once; unmapped/spanned tasks listed>
- Requirement coverage: <acceptance requirement -> slice>
- Classification coverage: <standalone/flagged/integration-only evidence and owning checks>
- Behavioral probe coverage: <applicable assembly/concurrency/recovery probe -> changing task/slice; N/A reasons>
- Dependency order: <acyclic and linear for stacked; checkpoint order for integration>
- Publication coverage: <every slice -> exactly one layer group; any rollup is reference-only; every group has base/head/artifact>
- Budget exceptions: <none or explicit accepted reason>
- Policy compatibility: <branch protection, linear history, merge queue, signed commits>
- User authorization boundary: <slice approval recorded separately; publication pending>
- Open decisions: <none or options with cost/benefit and recommendation>

## Merge and publication plan

- Execution order: <S1, S2, ...>
- Ralph branch/topology: <ordinary feature branch / ordered slice branches / integration branches>
- Per-slice merge: <method and base, or N/A for one publication group>
- Publication groups: <P1... with included slices and intended remote target>
- Final rollup: <merge commit / fast-forward / N/A>
- Target sync: <merge target into integration, frequency>
- Queue/freeze: <policy>
- Issue closure: <`Part of #...` on lower layers; `Closes #...` only on the final published group>
- Rollback per slice/group: <summary table or references>

## Approval record

- SLICE_PLAN_VERDICT: ready | blocked | needs_decision
- SLICE_PLAN_FINGERPRINT: <method and digest of the presented plan>
- SLICE_APPROVAL: pending | approved | rejected
- Approved by: <human user; recorded by the post-gate writer, not this template>
- Choice / accepted risks: <actual user decision>
- Approved execution mode: <single | stacked | integration>
- Approved publication mode: <single | stacked | integration>
- Approved publication groups: <P1... map and content fingerprint>
- Publication authorization: pending | separately recorded later
- Approved mode / snapshot: <execution/publication/group modes plus HEAD/content fingerprint>
- Approved at: <gate decision time>

The gate displays this exact plan. After the gate, Delivery's
`action=record-approval` writer records the actual choice and current snapshot
here; the gate itself does not edit this file. A ready plan, a successful
command, or an agent recommendation is not approval, and context-only approval
cannot authorize Ralph or remote publication. Re-run slice planning when
material scope, task mapping, a prefix/checkpoint probe, a publication-group
map, or the merge policy changes.
