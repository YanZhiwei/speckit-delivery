---
description: "Plan independently reviewable delivery slices, classify trunk safety, and select the merge mode"
---

# Delivery Slice

## Input

```text
$ARGUMENTS
```

Use this command after the plan gate has approved the design and `tasks.md` has
been generated, and before analysis/Ralph execution. It owns the delivery
boundary: slice order, task mapping, trunk-safety classification, and merge
policy. It does not own requirements, detailed design, task generation, source
edits, review verdicts, branches, or pull requests.

If `delivery_run=<id>` is supplied, validate it as one safe path segment and use
`.specify/delivery/<id>/` as the canonical run directory. Read the exact
exploration packet, approved spec/plan, generated `tasks.md`, and
`.specify/extensions/delivery/delivery-config.yml`. Resolve the active feature
from those artifacts; if more than one feature could match, stop instead of
choosing by recency.

Before planning, require the actual plan-gate approval supplied as
`design_approval=<choice>` or recorded against the unchanged plan snapshot.
Missing approval, a changed design, or an unrelated run is a blocker. Do not
infer design approval from a command exit status.

If `pr_slicing: off`, write one slice covering the full task queue with
`merge_mode: single` and return `SLICE_PLAN_VERDICT: ready`; the gate is still a
quick confirmation, not a second design review.

## 1. Derive slices from the approved design

Prefer slices that are independently reviewable and, where possible, safe to
merge into the target branch:

- one slice = one concern with a clear acceptance outcome, not one file or one
  task;
- put shared contracts, schema, and foundational types before consumers;
- keep behavior tests in the slice that changes the behavior; a separate
  characterization/refactor slice is valid only when it preserves behavior;
- do not hide a refactor inside a behavior slice or vice versa;
- keep migrations expand/contract so each deployable prefix remains valid;
- separate the release slice (flag default on, fallback removal, cleanup) from
  the slices that build the dormant capability;
- a design-only baseline slice may carry spec/plan/tasks/ADR changes so later
  code PRs do not repeat a large artifact diff. Skip it when artifacts are
  ephemeral or already landed;
- do not create a slice that cannot be reviewed without reading the entire
  feature, unless that slice is explicitly `integration-only`.

Every task in `tasks.md` must map to exactly one slice. A task that spans two
slices is a blocking finding: return to `speckit.tasks` to split it, or merge the
slices. Never silently rewrite `tasks.md`, add a second queue, or drop a task.

## 2. Classify trunk safety

For each slice choose exactly one classification and record concrete evidence:

- `standalone`: merging only this slice (and its lower dependencies) into the
  target branch keeps build/tests green and either preserves behavior or is
  independently shippable. Record the exact target-branch verification commands.
- `flagged`: the new behavior is dormant behind a named flag with a safe default
  and a kill switch. Record the flag name, default, kill switch, flag-off
  behavior, and flag-off regression test.
- `integration-only`: no meaningful prefix can be trunk-safe because the old and
  new implementations cannot coexist, the intermediate state cannot compile, or
  an equivalent flag/abstraction is genuinely unavailable. Record why, plus the
  green checkpoints on the integration branch.
- `unknown`: the evidence is insufficient. Do not approve a merge mode from an
  unknown classification; request a spike/gate decision.

A classification is a hypothesis until the slice boundary executes the declared
check. `standalone` without executable target-branch verification is not
evidence. Do not invent flags, commands, profiles, or platform capabilities.

## 3. Derive the merge mode

Derive, do not freely choose:

```text
one slice, or pr_slicing=off                    -> single
all slices standalone|flagged, linear order     -> stacked
any slice integration-only                      -> integration
any unknown, mixed incompatible chains, or
merge policy conflict                           -> needs_decision
```

Rules:

- `stacked`: every prefix must remain safe on the target branch. If one layer is
  not safe, the stack cannot partially merge; use `integration` for that
  dependent chain, or add a real flag/abstraction and reclassify.
- `integration`: each slice merges into the configured integration branch; the
  final rollup uses a merge commit, never a squash. Record why stacked is
  impossible.
- Do not mix `stacked` and `integration` inside one feature. Independent
  standalone work may land first as separate PRs, but the remaining dependent
  chain has one mode.
- Respect project policy: if the target requires linear history, a final merge
  commit conflicts with policy; return `needs_decision` instead of silently
  choosing a squash that destroys slice boundaries.
- If the configured stack provider or merge queue is unavailable, use the
  documented manual fallback; do not claim native support.

When the result is `needs_decision`, present at most three options with evidence,
cost, benefit, and a recommendation. Do not mark the plan ready until the gate
records a choice.

## 4. Validate before writing

Block or return `needs_decision` when any of these fails:

- every task is mapped exactly once; every acceptance requirement is covered;
- the dependency graph is acyclic; a stacked plan has a single linear order;
- every slice has a goal, review focus, verification command/test, and rollback;
- every `standalone` slice has target-branch verification;
- every `flagged` slice has a flag name/default/kill switch and flag-off test;
- every `integration-only` slice has a concrete reason and green checkpoints;
- no `unknown` remains in an approved mode;
- no slice exceeds `slice_warn_files` or `slice_warn_lines` without an explicit,
  accepted reason (generated/lock/vendor files are excluded from the count);
- the merge policy is valid for the repository's branch protection and merge
  queue; `integration` never selects `final: squash`;
- `tasks.md` remains the only execution queue and `slices.md` does not add,
  remove, or reorder tasks.

Budget thresholds are review heuristics, not hard proof. A large mechanical
rename may be one slice; a small concurrency change may need its own slice.

## 5. Write and present the plan

Use `.specify/extensions/delivery/templates/slices.md` from the installed
extension (or `templates/slices.md` under its resolved root). Write the complete
plan to `.specify/delivery/<run>/slices.md`, honoring `artifact_policy`.

Present a compact table in the conversation before the gate:

```text
SLICE  GOAL                         TASKS        TRUNK-SAFE   FLAG        DEPENDS
S1     event contract + table       T001,T002    standalone   -           -
S2     write path                   T003,T004    flagged      audit.write S1
S3     read API + UI                T005-T007    flagged      audit.read  S2
S4     enable + cleanup             T008         standalone   -           S3
```

Also state the merge mode, target/integration branch, slice merge method, final
merge method, sync method, queue/freeze policy, and every open decision.

## Boundaries

- Do not edit `tasks.md`, `spec.md`, `plan.md`, source, tests, branches, or PRs.
- Do not implement, review, approve, merge, push, or create a tracker resource.
- Do not replace the slice gate or record approval yourself.
- Do not claim a prefix is safe without the declared check; a failed check
  returns to this command for reclassification, not to an ad-hoc patch.
- Do not cite internal task IDs in durable PR text as the requirement source;
  use the linked Issue and user-facing acceptance outcome.

## Completion

Return:

```text
SLICE_PLAN_VERDICT: ready | blocked | needs_decision
MERGE_MODE: single | stacked | integration | undecided
SLICE_COUNT: <n>
SLICES_PATH: <actual path or preserved context>
SLICE_APPROVAL: pending
OPEN_DECISIONS: <none or bounded list with recommended options>
```

`ready` means the plan is coherent enough for the slice gate, not that the user
approved it. A blocked plan must name the exact task, evidence, or policy gap and
the command that must run next.
