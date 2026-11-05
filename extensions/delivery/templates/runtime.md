# Delivery runtime protocol

This is the single owner of the portable coordinator checkpoint and conditional
workflow transport. It supplements the native Quality, Standards, Reviewer,
Slice, and Core contracts; their semantic judgments remain authoritative.
`tasks.md` remains Feature's only execution queue.

## Locations and execution

Run from the project root with Python 3.11 or later:

```text
<python> .specify/extensions/delivery/scripts/delivery_runtime.py <operation> --run <id>
```

Portable workflows take a `runtime_python` input, defaulting to `python`. The
project must pass a verified invocation (`python`, `python3`, or Windows `py -3`)
and repair its own shell startup failures; the runtime does not edit global shell
configuration or silently substitute another interpreter. Direct invocations do
the same.

The helper uses only Python's standard library and Git. It never invokes a model,
executes project tests, edits product code/tasks, commits, or contacts a tracker.
A failing operation exits nonzero with a concrete recovery action. Boolean
`needs` operations print exactly `true` or `false` without a newline, for Workflow
conditions; an invalid checkpoint is an error, never a passing/skip decision.

Portable workflows add `--workflow-run {{ context.run_id }}` to every helper
mutation. The helper reads that exact engine state, checks the run identity and
active occurrence, and records an idempotent operation key. If the host dies after
the helper persisted a ticket/attempt/result but before the engine recorded the
step, replaying the same authored step returns the same ticket/attempt/result
instead of allocating a second one. A new loop occurrence or different engine run
gets a new key; never reuse a key to make a real new round look completed. Direct
CLI callers may supply an explicit stable `--operation-id` instead.

The canonical root is `.specify/delivery/<delivery_run>/`. Operational state,
inputs, and normalized transport results live in its `runtime/` directory. Init
adds that exact directory and Spec Kit's operational `.specify/workflows/runs/`
ledger to Git's local `info/exclude`, preserving existing entries. Tracked files
remain tracked; a tracked dirty workflow ledger still requires explicit recovery. Project-owned evidence and approved planning artifacts retain their
existing tracked/ephemeral policy. A missing runtime checkpoint alongside older
artifacts is a legacy run: status reports it without inventing a pass or resetting
repair history. Recover/import the original identity and counters before starting
a new protocol run; do not give interrupted work a new run ID to reset budgets.

## Start, bind, and resume

1. `init --run <id> --lane feature|bugfix|lightweight` creates one checkpoint or
   validates the same existing identity. A Bugfix run also requires its explicit
   lowercase kebab-case `--bug-slug`; other lanes reject one. Init does not
   fabricate final evidence.
2. After Core Specify, the coordinator runs `bind --run <id> --feature-dir <path>`
   with the **actual** Feature path returned by Core. A portable workflow may instead
   use `bind --run <id> --feature-from-packet <run>/exploration.md` only when that
   packet contains exactly one explicit `FEATURE_DIR:`/`FEATURE_PATH:` marker emitted
   by Core. This binds its `spec.md`, `plan.md`, and `tasks.md`; missing later-stage
   files may be bound before they exist, but consumers must require them when needed.
   Bugfix uses `bind --run <id> --assessment <exact-path>`. `--input <path>` adds a
   governed input not otherwise visible to Git (for example an ignored policy file).
3. `phase --run <id> --name <phase>` records the current owner phase, not semantic
   completion. Use `exploration`, `planning`, `tasks`, `execution`, `verification`,
   or `handoff`. A terminal outcome cannot be overwritten by a phase update.
4. `status [--run <id>] [--json]` is read-only. With no ID it lists runs rather
   than guessing one. `resume --run <id> [--json]` returns the same authoritative
   status plus the pending owner/action. Neither command executes that action or
   reopens valid approvals. Unfinished reservations and missing/stale results are
   explicit blockers or next actions, not an empty budget.

For Core Tasks/Analyze/Converge, also read the installed
`.specify/extensions/delivery/templates/core-adapter.md`.

## Present and record an actual decision

Before a human gate, `present --run <id> --name <gate> --input <path> ...` stores
exact hashes of the files being shown. After the gate, `decide --run <id>
--name <gate> --choice approve|reject` verifies those same bytes and records the
actual supplied choice. A changed file requires a fresh presentation; do not
replace the pre-gate fingerprint to make an old choice fit.

The native scope/design/Slice writer still records its required receipt and
semantic input manifest. Runtime decision receipts record what was presented and
chosen; they do not grant authority to later changed scope/design. Present bound
requirements with `--binding spec|plan|tasks|assessment` when their real paths are
already bound. The native scope/design/slice receipt still covers its complete
semantic input manifest.

A workflow begins `checkpoint`, dispatches Delivery Route `action=checkpoint`,
and records its normalized result before `require --kind planning`. The native
handoff evidence is exactly
`.specify/delivery/<delivery_run>/runtime/core-handoff.md`; the checkpoint result
references it as `report`, and Ralph reads that same file before task selection.
The coordinator
may create a planning commit only under already established project Git
permission for the exact displayed paths. The helper verifies that this operation
changed no reviewed input bytes and that the committed range contains only the
explicit approved planning files; it associates those unchanged Analyze inputs
with the resulting HEAD. Missing authorization, unrelated dirtiness, changed
approvals, or incorrect branch/base blocks. A script never authorizes or creates
its own commit.

## Structured owner results

When a command receives `runtime_stage=<stage>` and `runtime_result=<path>`, the
coordinator follows this sequence. The independent reviewer remains read-only.

1. A workflow `begin --stage <stage>` writes
   `runtime/input-<stage>.json`. Resume reuses an unfinished input only with the
   explicit `--resume` flag and unchanged inputs; otherwise inspect the pending
   stage and recover it. Do not silently replace it.
2. Read that input file. Execute the native owner contract. Preserve native
   findings, reports, and original check receipts.
3. The coordinator writes the result JSON at the supplied exact path (normally
   `runtime/result-<stage>.json`) and the separate machine `native_receipt`. Both
   use the exact stage, `scope`, ticket, and input fingerprint from the begin
   file and reference the real native report; the receipt additionally binds its
   exact HEAD, `evidence` list, and `data`. The owner never upgrades an
   incomplete/blocked native report to pass.
4. Workflow `record --stage <stage>` validates and consumes that result. Missing,
   malformed, stale, mismatched-run/lane/stage/ticket, conflicting native verdict,
   or tampered report/receipt/evidence references stop the workflow even when the
   host CLI exited zero. A resumed consumer does not rely on another process's
   conversation or stdout.

Instead of hand-writing the envelope and receipt, a coordinator may run:

```text
<python> .specify/extensions/delivery/scripts/delivery_runtime.py owner-result --run <id> \
  --stage <stage> --report <native-report> --data <data.json> --verdict <verdict> \
  [--output runtime/result-<stage>.json] [--receipt runtime/native-receipt-<stage>-<ticket>.json] \
  [--record-result]
```

`owner-result` copies the exact pending ticket, scope, input fingerprint, lane,
and input HEAD into both files, hashes the real report bytes, and collects
evidence recursively from `data`. A data evidence value may use
`{"path": "...", "sha256": ""}` to ask the helper to hash that run-local file;
nonempty hashes are preserved and still validated. `--record-result` delegates to
the same `record` validation described below; it is not a bypass. Workflows that
already declare adjacent `begin` and `record` steps should build without
`--record-result` and keep that explicit transition. The native owner still
supplies the verdict and semantic report; the helper makes no quality judgment.

Envelope (exact keys; no extras):

```json
{
  "schema_version": 1,
  "delivery_run": "run-01",
  "lane": "feature",
  "stage": "review",
  "scope": "outgoing-diff",
  "ticket": "copy from input-review.json",
  "input_fingerprint": "copy from input-review.json",
  "verdict": "pass",
  "report": {"path": ".specify/delivery/run-01/reviews/outgoing-diff/review.yml", "sha256": "hex SHA-256 of original bytes"},
  "native_receipt": {"path": ".specify/delivery/run-01/runtime/native-review-<ticket>.json", "sha256": "hex SHA-256 of receipt bytes"},
  "data": {}
}
```

The normalized envelope is transport, not the native report. The owner also
writes exactly one machine receipt that binds its actual output:

```json
{
  "schema_version": 1,
  "receipt_type": "delivery-native-owner",
  "delivery_run": "run-01",
  "lane": "feature",
  "stage": "review",
  "scope": "outgoing-diff",
  "ticket": "copy from input-review.json",
  "input_fingerprint": "copy from input-review.json",
  "verdict": "pass",
  "report": {"path": "same report reference as the envelope", "sha256": "same hash"},
  "head": "actual output HEAD for checkpoint, otherwise the pending input HEAD",
  "evidence": [{"path": "...", "sha256": "..."}],
  "data": {}
}
```

`receipt_type`, `head`, `evidence`, and the exact identity/verdict/report/data
values prevent a fresh envelope from relabeling an old/blocked/native report.
`evidence` is the ordered list of every `{path,sha256}` reference found under
`data`, and no other evidence may be added. A machine-readable native verdict
header (`QUALITY_VERDICT`, `STANDARDS_VERDICT`, `REVIEW_VERDICT`,
`ANALYZE_VERDICT`, `CONVERGE_VERDICT`, `CLARIFY_VERDICT`, `SIMPLIFY_VERDICT`,
`SIMPLIFY_VERIFY_VERDICT`, or `SD_CORE_HANDOFF`) must agree with the envelope.
`report`, `native_receipt`, and evidence references must be real regular files
within this run; source bytes are hashed, not re-labeled. Fields under `data`
depend on stage:

| Stage | Verdicts | Required data |
| --- | --- | --- |
| `quality` | `pass`, `blocked` | `checks`: array of `{command, exit_code, evidence:{path,sha256}}`; a pass requires integer zero for every actual check. An empty passing list requires `applicability: not-applicable` and a concrete policy-backed `reason`; never fabricate a check for a low-impact change. |
| `standards` | `pass`, `blocked`, `incomplete` | `coverage`: `complete` or `incomplete` |
| `review` | `pass`, `blocked`, `incomplete` | `dimensions`: all six native dimension keys; `coverage`; `independence`: `independent`, `accepted-self-review`, or `self-review`; `findings`: `{id,status,blocking,evidence?}` array; `repairable`: boolean. Accepted self-review also needs an `acceptance` file reference to the actual user decision. A pass needs current passing Quality/Standards records, full coverage, all axes pass, accepted independence, and no unresolved blocker. Every previously unresolved finding must be explicitly accounted for; resolved/dismissed findings need evidence references. |
| `converge` | `converged`, `tasks-appended`, `blocked` | `appended_tasks`: exact appended Task IDs. Only append-only changes to the bound `tasks.md` are allowed; converged leaves it byte-identical. |
| `clarify` | `ready`, `blocked` | `needs_approval`: boolean, true only for an actual remaining/material requirements decision; the bound Spec is its only permitted non-workspace mutation |
| `analyze` | `pass`, `blocked`, `incomplete` | `coverage`: complete/incomplete; actual blocking findings still block execution |
| `simplify` | `none`, `candidates`, `blocked` | `candidates`: unique array of candidate IDs; no source or Task mutation during the scan |
| `simplify-verify` | `pass`, `fail`, `not-applicable`, `blocked` | `accepted_candidates`: exact IDs from the immutable proposal and actual same-run Simplify decision receipt; an accepted candidate cannot close as not-applicable; `fail` records a real failed verification and blocks closure. Native verification covers actual lane-owned application. |
| `checkpoint` | `pass`, `blocked` | `planning_stage`: `initial`, `converge`, `simplify`, or `outgoing-repair`; `approved_paths`: exact subset of this checkpoint ticket's native `runtime/planning-inputs-<ticket>.json` manifest; `branch`: actual verified branch; `base_head`: the pending checkpoint's entry HEAD; `authorization`: actual project policy/user decision citation; optional `planning_commit`, `task_ids`, `slice_mapping`, and association identity. A pass needs a clean execution entry, unchanged passing Analyze inputs, and only approved manifest paths in any intervening commit. Declared run operational records (`runtime/`, `reviews/`, `receipts/`, task/slice verdicts, `evidence.md`, PR bodies) and Spec Kit's workflow-run ledger do not block; source, planning, test, policy, or unrelated paths do. The manifest lists each exact path and `source_owner` (`core`, `decision`, or `adr`); a Proposed ADR must live directly under the project's configured ADR directory. |

Six review keys are `requirements`, `code_quality`, `architecture`, `correctness`,
`security_compatibility`, and `test_effectiveness`, using the native Reviewer
contract. This transport does not replace the full native report or pretend to
verify its semantic truth. It makes completeness, identity, freshness, and the
existing judgments executable instead of equating process success with approval.

Fingerprints include HEAD, Git-tracked and relevant untracked files (bytes and
modes), explicitly bound ignored inputs, Constitution, Delivery config, Quality
config, and these canonical run-root inputs when present: `exploration.md`,
`slices.md`, `decision-context.md`, `code-context.md`, and `simplifications.md`.
Only `runtime/`, `reviews/`, `receipts/`, task/slice verdict files, `evidence.md`,
and rendered PR bodies are excluded coordinator bookkeeping. For the canonical
`slices.md`, the post-gate receipt lines (`SLICE_APPROVAL`,
`Choice / accepted risks`, `Choice`, `Approved by`, `Approved mode / snapshot`,
`Approved mode`, `Approved at`) are declared receipt metadata excluded from the
runtime content hash; `SLICE_PLAN_FINGERPRINT` and all plan content remain
included, so a plan change still invalidates reuse while the required approval
write does not create a false stale state. Approved requirements
and any other meaningful ignored inputs must be bound explicitly. Original
report/check evidence hashes are rechecked on reuse. Product code must not live in
the Delivery workspace. Project checks must leave generated caches/artifacts
ignored (normal `.gitignore` practice); an unignored file written during a
read-only owner stage invalidates that result, and the run must clean/ignore it or
refresh the owner rather than restamp the fingerprint. Do not use this rule to
hide real source changes.

Each result records the snapshot it validated. A stored pass is reusable only
while that snapshot still matches, its native report/evidence bytes are unchanged,
the stage has no unfinished pending ticket, and any declared dependency receipts
remain current. Review depends on current Quality and Standards results.
## Task-close transport

Ralph owns the task outcome and Git commit. For every SD Feature task, the
coordinator must execute these helper operations, using the project's verified
Python invocation. A human-readable `task-verdicts.yml` remains Ralph's native
receipt; machine associations live only under `runtime/task-closures/<TaskID>.json`.
They are evidence for the existing queue, never a second queue.

1. Before edits, `task-start --run <run> --task T001 --branch <approved-branch>
   --input <allowed-path> ...` requires the selected unchecked Task ID, actual
   branch, clean entry, and exact allowed paths/directory prefixes. It preserves
   the original task-start HEAD and queue. A resumed task cannot reset these.
2. After implementation, use the existing owner `begin`/`record` transport for
   Quality, Standards and Review with runtime `--scope task-T001`. The native
   commands still receive `scope=task task=T001`, their pending input and exact
   result path. Keep each task/ticket's native reports and check evidence immutable.
   All three passes must bind the same current pre-commit code/requirements
   snapshot, complete six-dimensional review, and accepted actual independence.
3. Write `runtime/docs-refresh-T001.json`: either
   `{"required": false, "reason": "concrete applicability reason"}` or
   `{"required": true, "verdict": "pass", "input_fingerprint": "exact pending fingerprint", "report": {"path": "native run-local report", "sha256": "original hash"}}`.
   `updated` and `unchanged` are also accepted passing docs verdicts; blocked or
   stale docs cannot close. Then run `task-gate --run <run> --task T001 --file
   <exact applicability path>`. The helper archives the owner results and reviewed
   Git blob/mode projection without editing the queue or creating a commit.
4. Only after the gate passes may Ralph change that task's checkbox, persist its
   native receipt, stage the verified task paths and create its one-task commit.
   `task-record --run <run> --task T001 --commit <full-SHA>` verifies the sole
   parent, exact Task ID, actual committed blobs/modes, unchanged requirements,
   selected-checkbox-only queue transition and clean execution worktree. It
   associates the original reports with that commit without relabeling them as
   reviews of a later HEAD. It never commits or marks a task itself.
5. Before `ALL_TASKS_DONE`, Converge closure, Evidence and Handoff, run
   `require --run <run> --kind task-closure`. Every checked Task ID must have its
   own complete, reachable, hash-valid committed association in queue order.
   Checkbox-only completion, a final outgoing-diff report, missing/tampered
   native evidence or a mismatched commit cannot replace a task receipt. The
   Feature Workflow invokes this read-only guard after every Ralph dispatch and
   before Evidence, independently of the agent's completion claim.

A legacy run without these original task receipts needs explicit recovery from
its original evidence. Do not fabricate task passes or import a final review as
historical task approvals. A standalone Ralph installation with no Delivery run
retains its native closure contract and must report that it lacks this machine
transport. A current version number or successful installation is not proof that
an existing run used the helper.

## Conditional loops and persistent budgets

`needs --kind review` is true until a complete current pass exists. It never
skips missing/invalid coverage. `needs --kind repair` is true only for a current
blocked Review with confirmed repairable blockers; incomplete evidence requires
recovery, not speculative edits. `require --kind review` is the final machine
guard, followed by the native human review gate.

`reserve --kind review|convergence [--scope <scope>]` persists an attempt before
an edit/execute pass and enforces the configured integer limit (1–3). Default
scope is `outgoing-diff`; Task repairs use `task-<id>`. A pending reservation
survives a new process/HEAD. `reserve --resume <attempt>` returns that same
reservation rather than allocating another; a bare `--resume` is invalid.
Workflows may add `--plain` to print only the reserved integer for a later command.
`complete --kind <kind> --attempt <n>` marks its completion; it does not produce a
passing Review.
The native Review Fix owner consumes the reserved attempt, never double-counts
it, and still stops for scope/design changes. A Feature outgoing repair that
changes `tasks.md` or its slice mapping must pass the same Slice → Analyze →
combined gate → approval writer → authorized planning checkpoint → Ralph path
before the repaired queue runs; a source-only repair within the unchanged queue
does not create a planning transition. Because the repair owner is already inside
a bounded review pass, this outgoing-repair checkpoint may be the native nested
form: the Route writes a unique `planning-inputs-outgoing-repair-<attempt>.json`
and native handoff, and performs only the authorized commit; it must not create a
pending runtime checkpoint ticket it cannot record. Ralph consumes the native
handoff. Initial/converge/simplify checkpoints still use the recorded runtime
stage.

Convergence starts with one Core assessment. A `tasks-appended` result may enter
at most the configured number of Analyze→planning checkpoint→Ralph→checks→Core
reassessment passes. Reassessment is included in the reserved pass. At the cap,
unresolved or newly appended work blocks; it is not silently marked converged.
`needs --kind convergence` checks this same state and budget;
`require --kind convergence` requires a current `converged` result.

`needs --kind clarification` / `simplification` expose genuine decision/candidate
results. For Simplify, `present --name simplify --input <canonical-proposal>` saves
the current proposal bytes and candidate IDs. `decide --name simplify` records
the actual choice; rejection skips optional simplification and continues the lane.
`needs --kind accepted-simplification` gates lane-owned application. Keep that
proposal immutable after the decision and put application bookkeeping in runtime;
changed proposals require renewed presentation. Record native `simplify-verify`
and require its pass after application. `needs --kind simplification-verification`
refreshes only accepted candidates when their verified inputs become stale.

`needs --kind quality|standards|review` detects missing/stale owner receipts.
`needs --kind tasks` reads the bound queue for unchecked tasks but does not select,
reorder, or close them. No candidates/appended tasks means downstream model
processes can be skipped. Project-required approvals remain mandatory.

## Handoff and outcome

After native Evidence/Handoff succeed, `require --kind evidence` verifies and
persists the same-run evidence identity; `phase --name handoff` reports
`handoff-ready` only with a current complete Review, current evidence, and the
actual nonempty native `pull-request.md`/`pull-request-<slice>.md` body observed
at that content. This means ready to publish/review, not published or delivered.
Status identifies the external event still pending and reports a previously
observed Evidence/PR body that disappeared or changed as a blocker.

Before terminal native Close writes, `outcome --outcome merged|closed|superseded
--verified --pr <reference>` validates the transition. `unverified` always exits
nonzero without changing state or artifacts. A concrete existing PR cannot be
replaced by a different one; pending may bind to the first verified PR. The
native Close owner still verifies the configured tracker, writes durable evidence,
and applies its exact retirement allowlist; the helper never deletes artifacts.
`--verified` records the native owner's observed fact; it does not query a tracker
or turn a user assertion into observed evidence.
