# Delivery Spec Kit hook contract

This is the single owner of Delivery's Spec Kit extension-hook behavior. The
`speckit.delivery.hook-*` commands are argument-less adapters bound to Core and
Bug lifecycle events in `extension.yml`. They prepare and reuse native owner
artifacts when a user invokes Core/Bug commands directly; the portable
workflows and Delivery Route remain the orchestrators, and the native Explore,
Decision, Slice, Quality, Simplify, Review, Evidence, and Close contracts keep
their semantic authority.

Hooks are prompts surfaced in the current session. They are not machine gates,
cannot receive `key=value` arguments, and an optional hook may be skipped. A
disabled, skipped, or failed hook is never evidence of completion, and no hook
may weaken an existing quality, review, or approval requirement.

## Run resolution without arguments

1. Run the read-only discovery from the project root with the project's
   verified Python invocation:

   ```text
   <python> .specify/extensions/delivery/scripts/delivery_runtime.py active
   ```

2. `selection: single` gives the one active run; use its exact `delivery_run`,
   `lane`, `phase`, `bindings`, `approvals`, `blockers`, and `next_action`.
   Every later helper call passes that explicit `--run`; never guess the newest
   run, a Feature directory name, or a Bug slug from the filesystem.
3. `selection: none` means there is no active Delivery run. Report
   `SD_HOOK: skipped` with `REASON: no-active-run` in one or two lines and let
   the surrounding Core/Bug command continue unchanged. Do not initialize a
   run, invent an id, or create Delivery artifacts.
4. `selection: ambiguous` means more than one active run exists. Ask the user
   which run the current request belongs to and stop the adapter; never pick
   one by recency or name.
5. A selected run with blockers or `status: verification-required`/`legacy`
   needs recovery first: report the recorded blocker and stop the adapter
   instead of producing fresh artifacts over an inconsistent checkpoint.
6. When the selected run's lane does not own the surrounding command (for
   example `before_specify` in a Bugfix run), report `SD_HOOK: skipped` with
   `REASON: lane-not-applicable`; never create Feature artifacts for another
   lane.

## Event context

Spec Kit injects no variables. Use only the selected run's checkpoint plus the
actual surrounding conversation: the Feature directory Core Specify really
reported, the Bug extension's resolved `BUG_SLUG`/`BUG_DIR` and report paths,
and, during a Bugfix review-repair continuation, the current round's
`review-repairs/<delivery-run>/round-<n>/` fix/test reports. The bound
`spec.md`/`plan.md` and canonical exploration packet replace the original
request text. Never relabel a continuation round's artifacts as the original
official Bug reports, and never feed a hook stale originals.

## Reuse before dispatch

Each adapter checks its native artifact and recorded identity before
dispatching the native owner command:

- A current artifact whose recorded inputs are unchanged is **reused**: report
  `ACTION: reused`, cite the artifact, and do not dispatch the owner again.
- A portable workflow dispatches the same Core/Bug commands, so its explicit
  steps may find the hook's artifact already present. Those steps reuse the
  native artifact and still perform their own runtime transport; the hook and
  the workflow step must not produce two investigations, two ADR baselines, or
  two slice plans for the same inputs.
- A missing artifact, changed input identity, or an explicit unresolved gap is
  the only reason to dispatch the native owner again.

## Mutation and approval limits

- Adapters write only the native owner's canonical artifact for the selected
  run: `exploration.md`, `decision-context.md`, `code-context.md`, `slices.md`,
  `simplifications.md`, Proposed ADR records, or an inline brief.
- Helper calls are direct CLI invocations without `--workflow-run` or
  `--operation-id`. Adapters may use `bind` for the actual Feature/assessment
  identity. They never use `begin`, `record`, `owner-result`, `reserve`,
  `complete`, `require`, `phase`, `outcome`, `close-record`, or any task-*
  operation; runtime stage tickets, attempt budgets, and closure audits belong
  to the workflow/coordinator.
- The only approval an adapter may record is **scope**, through
  `present --name scope` followed by `decide --name scope --choice <actual>`
  after the user explicitly approves the exact presented packet. A portable
  workflow records scope before Specify, so its `before_specify` hook always
  takes the reuse path. Design, assessment, execution/slice, simplify, and
  review approvals are never presented or recorded by a hook; their gates stay
  in the workflow or Delivery Route.
- An adapter never applies simplification candidates, edits `tasks.md`, source,
  or tests, commits, dispatches Ralph, starts a repair/convergence loop, or
  publishes anything. A `blocked` adapter output instructs the agent to stop
  the surrounding command and return to `/sd` (Delivery Route); it is a
  prompt-level stop, not a mechanical veto.

## Output

Every adapter ends with one block:

```text
SD_HOOK: <before_specify|after_specify|before_plan|after_plan|after_tasks|after_converge|before_implement|after_implement|before_bug_assess|before_bug_fix|after_bug_test>
DELIVERY_RUN: <id or none>
ACTION: reused | prepared | bound | briefed | scanned | skipped | blocked
REASON: <no-active-run | lane-not-applicable | current-artifact | recovered-inputs | ...>
ARTIFACTS:
- <canonical native artifact or inline>
NEXT: <the one owning next step; gates stay with the workflow or /sd>
```

`prepared`, `bound`, `briefed`, and `scanned` describe native preparation only;
none of them is an approval, a quality/review verdict, or task closure.
