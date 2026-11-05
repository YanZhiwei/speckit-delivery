---
description: "Plan independently reviewable delivery slices, classify trunk safety, resolve execution/publication modes, and record the actual slice approval"
---

# Delivery Slice

## Input

```text
$ARGUMENTS
```

Use this command after the plan gate has approved the design and `tasks.md` has
been generated, and before analysis/Ralph execution. It is the single policy
owner for internal review-slice boundaries, task mapping, trunk-safety
classification, and the resolved execution/publication plan. It does not own
requirements, detailed design, task generation, source edits, review verdicts,
branches, or pull requests. Internal review slices and remote PR grouping are
separate decisions: do not suppress a useful review boundary merely to obtain
one PR, and do not create a remote PR boundary merely because a review slice
exists.

The plan written here must contain both a resolved `Execution mode` (the Ralph
branch/topology) and a resolved `Publication mode` plus an explicit
slice-to-publication-group map. The slice gate approves that complete plan
before execution. A slice approval never authorizes PR creation, publication,
merge, or any other remote mutation; those remain separately user-authorized.
This command owns the derivation and validation rule. Ralph and Handoff consume
the approved fields and must not infer, amend, or repartition them at the final
handoff.

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

Resolve `pr_slicing` before deriving slices. The values have these meanings:

- `off`: preserve the legacy path: create one internal slice covering the full
  queue, use `Execution mode: single`, and map it to one publication group.
- `single`: derive multiple internal slices when concern, dependency, or risk
  makes them independently reviewable, but use the ordinary Ralph branch and
  one publication group containing all approved slices. A one-slice plan is
  still valid for a small change.
- `auto`: derive internal slices first, then resolve the publication grouping
  from the verified classifications, branch/merge policy, and provider facts;
  record the result before the gate and before Ralph.
- `stacked`: request one ordered publication layer per approved slice. It is
  valid only when the classifications and repository policy prove a linear
  target-safe stack; otherwise return `needs_decision`.
- `integration`: request integration-branch publication. It requires the
  declared integration branch, protected merge policy, and the exact
  integration checkpoints; an `integration-only` classification always keeps
  those protections.

A configured request is not evidence. `auto`, `stacked`, and `integration` must
still pass the classification and policy validation below; never downgrade or
upgrade the requested grouping silently. If `pr_slicing` is missing or outside
this set, block with the exact configuration path and accepted values.

## Record the gate choice

`action=record-approval` is the Delivery-owned post-gate writer for the actual
`slice-gate` decision. It does not replan or re-approve. Require the exact
canonical `slices.md`, the real `slice_approval=approve|reject` value, and the
unchanged `SLICE_PLAN_FINGERPRINT` written before the gate. Record
`SLICE_APPROVAL: approved|rejected`, the actual choice, `Approved by` (the human
user, not the agent), `Approved at`, and the current approved mode/content
snapshot in that same file. A missing fingerprint, changed plan, missing choice,
or context-only approval is `SLICE_APPROVAL_RECORD: blocked`; never infer
approval or rewrite the plan to match a stale choice. A rejected choice records
rejection and stops the lane. This post-gate write is the only approval record
Ralph may consume; it does not edit tasks, source, branches, or PRs.

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
  feature, unless that slice is explicitly `integration-only`;
- do not merge otherwise meaningful internal boundaries just to fit a desired
  PR count. `pr_slicing: single` is the supported way to keep those boundaries
  while publishing one PR.

Every task in `tasks.md` must map to exactly one slice. A task that spans two
slices is a blocking finding: return to `speckit.tasks` to split it, or merge the
slices. Never silently rewrite `tasks.md`, add a second queue, or drop a task.

## 2. Assign early risk-based behavioral probes

Before selecting the execution/publication modes, inspect the changed behavior and
assign the smallest meaningful executable probe to the slice that introduces the
risk. Add the command/test, expected result, and evidence location to that slice
and to its owning task verification. Use only the probes that the change makes
relevant; record `N/A` with a concrete reason when a category does not apply.

- **Assembly/composition:** when independently reviewed pieces are assembled,
  probe the assembled contract at the slice that first makes it executable.
- **Concurrency:** when ordering, locking, retries, workers, or shared state can
  race, probe the smallest meaningful interleaving/serialization or isolation
  behavior in the changing slice.
- **Recovery:** when failure, restart, rollback, resume, or partial persistence
  is affected, probe the first recoverable boundary and its invariant in the
  changing slice.

These are risk-based behavioral probes, not a request for a blanket new full
suite. A final outgoing review or rollup may repeat an integration check, but it
cannot be the first execution of a required probe. Executable checks belong to
the task/slice that changes the behavior; do not defer them to `mode=rollup` or
an end-of-delivery amendment.

## 3. Classify trunk safety

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
- `unknown`: the evidence is insufficient. Do not approve an execution or
  publication mode from an unknown classification; request a spike/gate decision.

A classification is a hypothesis until the slice boundary executes the declared
check. `standalone` without executable target-branch verification is not
evidence. Do not invent flags, commands, profiles, or platform capabilities.

## 4. Resolve execution and publication modes

Resolve both modes now, before the slice gate, checkpoint, or Ralph execution.
The internal slice count is independent from the number of remote PRs.
`Execution mode` controls Ralph's branch/topology; `Publication mode` controls
how the approved internal slices are grouped for a later, separately authorized
remote publication. Derive them from evidence and the configured request; do not
choose either merely from preference.

```text
one slice or pr_slicing=off                 -> execution=single, publication=single
pr_slicing=single                           -> execution=single, publication=single
all slices standalone|flagged, linear order -> execution=stacked, publication=stacked
any slice integration-only                   -> execution=integration, publication=integration
unknown, incompatible chains, or policy
conflict                                    -> execution=undecided, publication=undecided
```

The table is the `auto` derivation rule. Apply explicit requests as constraints:

- `single` is always one ordinary Ralph branch and one publication group, even
  when it has multiple internal slices. Keep every slice boundary and its
  classification evidence; a single PR does not make an `integration-only`
  slice target-safe.
- `stacked` is valid only when every prefix is target-safe under the declared
  `standalone`/`flagged` checks, the dependency order is one linear chain, the
  provider/manual fallback is documented, and branch protection accepts the
  configured slice merge method. If one layer is not safe, return
  `needs_decision`; do not partially stack it.
- `integration` requires the configured integration branch and protected policy.
  Each slice uses the declared integration checkpoints and the final rollup uses
  a merge commit, never a squash. Preserve the reason stacked is impossible.
- Do not mix `stacked` and `integration` inside one feature. Independent work
  may be represented as separate internal slices, but one approved feature plan
  has one execution/publication topology.
- A single publication group still requires the final outgoing/integration
  evidence appropriate to its classifications. It is not permission to skip an
  `integration-only` checkpoint or to call an unsafe prefix `standalone`.
- Respect project policy: if the target requires linear history, a configured
  integration final merge commit conflicts with policy; return `needs_decision`
  instead of silently selecting a squash that destroys slice boundaries.
- If the configured stack provider or merge queue is unavailable, use the
  documented manual fallback; do not claim native support.

Record the requested config value, the resolved modes, the reason/evidence, and
one explicit publication group for every internal slice. For `single`, that map
must show all slices in the same group and the ordinary Ralph branch. For
`stacked`, map one group/layer per slice. For `integration`, map the slice
layers plus one rollup group whose all-slice listing is reference-only, not a
second assignment. No mode may remain `undecided` in a plan that is approved
for execution.

When the result is `needs_decision`, present at most three options with evidence,
cost, benefit, and a recommendation. Do not mark the plan ready until the gate
records the selected execution and publication modes. Handoff may render the
approved plan but cannot resolve or amend this decision.

## 5. Validate before writing

Block or return `needs_decision` when any of these fails:

- every task is mapped exactly once; every acceptance requirement is covered;
- the dependency graph is acyclic; a stacked plan has a single linear order;
- every slice has a goal, review focus, verification command/test, and rollback;
- every `standalone` slice has target-branch verification;
- every `flagged` slice has a flag name/default/kill switch and flag-off test;
- every `integration-only` slice has a concrete reason and green checkpoints;
- no `unknown` remains in an approved mode;
- every applicable assembly, concurrency, or recovery probe is assigned to the
  behavior-changing task/slice with an executable command and expected evidence;
- `Execution mode`, `Publication mode`, the requested `pr_slicing` value, and the
  publication-group map are present and resolved before the gate;
- `pr_slicing: single` has one ordinary-branch publication group containing all
  internal slices; `stacked` has one ordered group per slice; `integration` has
  one slice group per slice plus a reference-only final rollup group;
- slice approval is recorded separately from publication authorization, which
  remains pending until the user authorizes remote publication;
- no slice exceeds `slice_warn_files` or `slice_warn_lines` without an explicit,
  accepted reason (generated/lock/vendor files are excluded from the count);
- the merge policy is valid for the repository's branch protection and merge
  queue; `integration` never selects `final: squash`;
- `tasks.md` remains the only execution queue and `slices.md` does not add,
  remove, or reorder tasks.

Budget thresholds are review heuristics, not hard proof. A large mechanical
rename may be one slice; a small concurrency change may need its own slice.

## 6. Write and present the plan

Use `.specify/extensions/delivery/templates/slices.md` from the installed
extension (or `templates/slices.md` under its resolved root). Write the complete
plan to `.specify/delivery/<run>/slices.md`, honoring `artifact_policy`. Compute
`SLICE_PLAN_FINGERPRINT` over the presented plan content (including task mapping,
classification and required probes, execution/publication modes, publication
groups, merge policy, and required evidence) with a recorded method/manifest
before the gate; the post-gate writer consumes it and never relabels it.

Present a compact table in the conversation before the gate:

```text
SLICE  GOAL                         TASKS        TRUNK-SAFE   FLAG        DEPENDS  PUB-GROUP
S1     event contract + table       T001,T002    standalone   -           -        P1
S2     write path                   T003,T004    flagged      audit.write S1       P1
S3     read API + UI                T005-T007    flagged      audit.read  S2       P1
S4     enable + cleanup             T008         standalone   -           S3       P1
```

Also state the requested `pr_slicing` value, resolved execution mode,
resolved publication mode, target/integration branch, publication-group map,
slice merge method, final merge method, sync method, queue/freeze policy,
publication authorization state (`pending`), and every open decision. Resolve
single vs stacked (or integration) here, not in final handoff.

## Boundaries

- Do not edit `tasks.md`, `spec.md`, `plan.md`, source, tests, branches, or PRs.
- Do not implement, review, approve, merge, push, or create a tracker resource.
- In planning mode, do not replace the slice gate or record approval yourself.
  The separate `action=record-approval` mode only records the actual post-gate
  user choice and unchanged snapshot; it cannot approve on the user's behalf.
- Do not claim a prefix is safe without the declared check; a failed check
  returns to this command for reclassification, not to an ad-hoc patch.
- Do not cite internal task IDs in durable PR text as the requirement source;
  use the linked Issue and user-facing acceptance outcome.

## Completion

Return:

```text
SLICE_PLAN_VERDICT: ready | blocked | needs_decision
EXECUTION_MODE: single | stacked | integration | undecided
PUBLICATION_MODE: single | stacked | integration | undecided
MERGE_MODE: <compatibility alias for EXECUTION_MODE>
SLICE_COUNT: <n>
PUBLICATION_PLAN: <group map and one-line publication shape>
PUBLICATION_AUTHORIZATION: pending
SLICES_PATH: <actual path or preserved context>
SLICE_PLAN_FINGERPRINT: <method and digest of the presented plan>
SLICE_APPROVAL: pending
OPEN_DECISIONS: <none or bounded list with recommended options>
```

For `action=record-approval`, return `SLICE_APPROVAL_RECORD: approved | rejected |
blocked`, the actual gate choice, approver/time, and the recorded snapshot. Never
report `pending` as approval.

`ready` means the plan is coherent enough for the slice gate, with execution and
publication modes already resolved; it does not mean the user approved it or
authorized publication. A blocked plan must name the exact task, evidence, or
policy gap and the command that must run next.
