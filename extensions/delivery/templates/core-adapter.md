# Core / Ralph adapter for SD Feature runs

This is the SD-scoped compatibility contract for the installed Core Spec Kit
commands. It is installed at `.specify/extensions/delivery/templates/core-adapter.md`.
Read this file in full when an SD Feature run crosses a Core planning stage into
Ralph execution, or when the caller supplies a Core-stage result. It adapts the
installed prompts; it does not replace or edit them.

The active host may render the upstream generated commands in a host-specific
command directory such as `.opencode/commands/speckit.tasks.md`,
`.opencode/commands/speckit.analyze.md`, and `.opencode/commands/speckit.converge.md`.
Invoke the installed command IDs (`speckit.tasks`, `speckit.analyze`, and
`speckit.converge`) and preserve their ownership. Never edit a generated Core
command to make it fit SD. Ralph's detailed slice contract remains at
`.specify/extensions/ralph/templates/slice-execution.md`; independent review
policy remains at `.specify/extensions/review/templates/reviewer.md`.

When the workflow supplies `runtime_stage=checkpoint` and an exact
`runtime_result`, the installed Delivery runtime contract transports and checks
the checkpoint result's identity, freshness, and completeness. Before task
selection, read exactly
`.specify/delivery/<delivery_run>/runtime/core-handoff.md`; when consuming the
current `.specify/delivery/<delivery_run>/runtime/result-checkpoint.json`, use
only its current report reference and resolve it to that exact handoff file.
This is local operational evidence under the ignored `runtime/` area, not a
tracked planning or task artifact. A missing, stale, mismatched, or differently
located handoff blocks execution.

The handoff must say `SD_CORE_HANDOFF: PASS`, and the coordinator must verify
its `planning_commit`, `execution_base`, approved paths/manifest, branch, and
base against the current Git refs and artifact identities before task
selection. The runtime helper transports and validates the checkpoint result;
it does not decide whether the plan is approved, whether a Git commit is
authorized, or whether a branch is a safe Ralph base. Those are native-owner
decisions. The native `SD_CORE_HANDOFF` is the semantic and permission evidence
that authorizes Ralph. Read the runtime contract for its transport details
rather than copying its JSON envelope into this adapter.

The checkpoint consumes a declared native Core-output manifest, not a wildcard.
The native command or phase that produced each entry remains that artifact's
owner; this adapter carries the declaration and verifies its association, while
Ralph consumes it. The exact manifest may include actually produced and
approved outputs such as research, data-model, contracts, quickstart, and a
Proposed ADR, as well as the Feature's Spec/Plan/Tasks and slice artifacts when
those owners declare them. Each entry must name its normalized project-relative
path and producing owner. A repository root, directory glob, "all Core
artifacts" shorthand, or an invented optional output is not an approved path.
Missing or changed declared output blocks the handoff; an output that the native
owner did not declare is not added by Ralph.

## Ownership and compatibility sequence

Use this sequence only for the SD Feature lane. It is an adaptation around Core,
not a second implementation workflow:

1. **Tasks / initial planning — Core owns the queue and native outputs.** Run
   the installed `speckit.tasks` command against the approved Spec, Plan, policy,
   and any delivery slice inputs. Core writes the Feature's `tasks.md` and
   declares the exact native-output manifest. SD may require the task shape and
   checkpoint fields below, but it does not hand-edit, renumber, reorder, merge,
   or invent Core task items. Run the installed `speckit.analyze` command after
   generation and resolve blocking findings in Core planning. When slicing is
   enabled, Delivery Slice then owns the exact task-to-slice mapping; its
   combined execution/slice gate and approval writer must record the actual
   choice before the initial planning-to-execution checkpoint.
2. **Ralph — Feature execution owner.** After the checkpoint, Ralph consumes
   `tasks.md` as the only execution queue. It selects one dependency-ready
   TaskID, performs the task, runs the meaningful project checks, Quality,
   Standards, and independent Review, and creates the task commit. A slice plan
   supplies boundaries only; it cannot become another queue.
3. **Converge — Core remains append-only.** In an SD Feature run, a completed
   Ralph run satisfies Core Converge's precondition that implementation has run.
   The coordinator may then invoke the installed `speckit.converge` command.
   Converge assesses the current code against the Spec, Plan, and Tasks and may
   append a new convergence phase to `tasks.md`; it must not rewrite, renumber,
   reorder, delete, or complete an existing task, and it never edits source code.
   If no gap exists, `tasks.md` remains byte-for-byte unchanged. If
   `appendedTaskIDs` is nonempty, the approved TaskID set/order and therefore the
   planning-to-slice mapping have changed by definition. Even when every new
   task appears to fit an existing slice, the owning Delivery Slice plan must
   revalidate the mapping, Analyze must cover the appended tasks, the combined
   execution/slice gate and approval writer must record a new choice, and the
   planning checkpoint must be renewed before Ralph. Do not invoke Ralph
   recursively from Converge or treat a new ID as approval; the runtime helper
   only transports/validates the native result and does not make this decision.
4. **Simplify and outgoing repairs — planning returns to the same handoff.** An
   accepted Simplify result or an outgoing-review repair that creates or reopens
   work must use the same `speckit.analyze` and checkpoint sequence. A changed
   task map, slice assignment, approved design, requirements input, or policy
   input requires the owning planning gate to be renewed; it cannot be hidden in
   a repair commit or silently attached to an old approval.
5. **Standalone Core Implement — unchanged outside SD.** A project may continue
   to use the installed Core `speckit.implement` command without SD/Ralph. This
   adapter does not remove, rewrite, or redirect that standalone command. The SD
   Feature path uses Ralph as its execution owner and must not use Core Implement
   as a second execution queue.

## SD task contract

A task is one independently verifiable, reviewable green commit. It is not a
TDD step, a test-only phase, or an arbitrary chunk of an implementation plan.
The task description and its approved context must identify:

- exactly one existing TaskID from `tasks.md`, its dependencies, acceptance
  outcome, allowed paths, and the meaningful checks that establish green;
- the user-story or requirement coverage and any applicable Architecture
  constraint IDs, with documentation or migration work when that outcome needs
  it;
- a vertical implementation boundary that can be reviewed and committed on its
  own. When setup, a red regression, implementation/green behavior, and related
  documentation are needed to make the outcome independently verifiable, keep
  them in the same approved vertical task rather than creating TDD-only tasks;
- the project's actual risk-based test policy. Behavior, public contract, data,
  migration, security, and boundary changes must receive the checks required by
  project governance; a documentation-only or otherwise low-risk task is not
  forced into an unrelated test suite. A passing command must be meaningful for
  the changed surface, not a placeholder or an assertion that work was skipped.

Core may regenerate the task breakdown through its own command when the shape is
not independently reviewable. Ralph must not silently merge or reorder existing
TaskIDs to repair a poor breakdown. A task that is only setup, red, green, or
docs work and cannot stand alone returns to Tasks/planning for an explicit,
approved regrouping. `[P]` is a dependency hint, not permission for Ralph to
reorder the queue or use parallel workers in the shared worktree.

`tasks.md` is the sole source of task identifiers, dependency edges, order,
acceptance criteria, allowed paths, and verification instructions. Converge,
slices, receipts, runtime state, reviewer findings, and worker messages cannot
add a second queue or change that source. A task must never be silently merged,
reordered, or marked complete by a worker.

## Planning-to-execution checkpoint

Before Ralph selects a task, the coordinator must establish an explicit
planning-to-execution checkpoint for the current approved artifact set and read
the exact local handoff evidence named above (or the current checkpoint result's
report reference to it). The checkpoint applies at each of these transitions:

| Stage | Required planning result before Ralph |
| --- | --- |
| `initial` | Core Tasks output and native-output manifest, successful Analyze result, Delivery Slice's task mapping, the combined execution/slice gate and approval writer, and the approved plan/task/slice identity when slicing is enabled |
| `converge` | Core Converge's append-only result, Analyze's result for the resulting queue, a renewed Delivery Slice mapping/gate/writer when `appendedTaskIDs` is nonempty, and the renewed task/slice checkpoint |
| `simplify` | Accepted Simplify result, Analyze's result for any task change, and the unchanged or renewed approved slice/design identity |
| `outgoing-repair` | Delivery Review-Fix's task/repair mapping, Analyze's result when the queue changes, and the unchanged or renewed approval identity |

The checkpoint is a control-flow gate, not a prose acknowledgement. For the
current `delivery_run`, record or verify all of the following before task
selection:

1. **Approved artifact manifest.** List the exact normalized
   project-relative paths that the native planning result authorizes, together
   with the producing owner for every entry. This is the declared native
   Core-output manifest; it may contain the actual research, data-model,
   contracts, quickstart, Proposed ADR, Spec/Plan/Tasks, slice plan, or named
   planning receipt paths that their native owners emitted and approved. Do not
   require a paper list of optional outputs, and do not authorize the repository,
   a directory glob, "all Core artifacts," or a later-discovered path. A source,
   Spec, Plan, ADR, task, slice, or other declared output change outside this
   manifest is a stale or changed input and returns to its owning approval.
2. **Fingerprints and association.** Preserve the original content and
   requirements/policy fingerprints from the displayed approval, the declared
   native-output manifest identity, and the TaskID set/order and slice mapping
   when applicable. If a project-authorized planning commit changes only the
   approved paths and the resulting content and requirements are content-
   equivalent, associate the new planning commit SHA with the original approval
   fingerprint explicitly. A new SHA is not permission to replace the
   fingerprint. If any reviewed bytes, path, task mapping, requirement, policy,
   design input, or declared output identity changed, stop for a refreshed
   planning presentation and approval; never restamp a new digest to bless
   changed input.
3. **Git authorization and boundary.** Verify that the project policy or an
   explicit project-authorized decision permits a planning-state commit, and
   record the exact approved paths and owners, target branch and target HEAD,
   declared slice base/mode/prefix, planning branch, planning commit SHA, and
   intended Ralph execution branch/base. For an SD handoff with tracked
   planning paths, `planning_commit` must be a concrete SHA; `none` is not an
   execution baseline. When the project explicitly keeps all planning artifacts
   ephemeral/ignored and records that authorization, `planning_commit: none` is
   allowed with `execution_base` equal to the verified base HEAD and unchanged
   bound-artifact identities; never claim a commit that does not exist. The
   branch and its declared base must be verified before
   any planning commit. After the commit, verify that its changed paths are a
   subset of the approved manifest and that every manifest entry has the
   approved identity at that commit. Stage only the approved planning paths;
   never use `git add -A`, `git add .`, a broad wildcard, or a planning commit to
   absorb unrelated user work. This planning commit is not a Ralph task commit.

### Verified planning-commit transfer

The checkpoint's `planning_commit` is the approved planning baseline, not a
context label. Ralph's `execution_base` is the actual SHA from which the exact
Ralph branch is reused or created. A planning checkpoint is `PASS` only when the
coordinator has recorded and verified the target/slice branch, the resolved
`branch_prefix`, the declared slice base, `planning_commit`, and
`execution_base`, and has proved all of the following:

- `planning_commit` is an ancestor of `execution_base`; the exact approved
  planning bytes and manifest identities are still present at that base;
- the declared base is ancestry-compatible with `planning_commit` and is an
  ancestor of `execution_base`. For no-slice/single and the first stacked slice,
  explicitly verify the approved target HEAD is an ancestor of that execution
  base. Later stacked slices use the previous verified slice HEAD as declared by
  the plan. An integration slice explicitly verifies the declared
  integration-branch HEAD instead, never the target merely because it is
  available;
- when planning is prepared on the intended execution branch, the branch/base
  and prefix were verified before the authorized planning commit. Otherwise the
  exact Ralph branch is created or reused from the approved current
  `planning_commit` (or a verified descendant containing it), and that commit
  itself extends the expected target or declared slice base; and
- after branch creation or reuse, the coordinator reruns branch/HEAD, ancestry,
  and manifest-identity checks on the actual Ralph branch. A planned base is not
  evidence that the branch contains it.

Use equivalent Git checks for these facts, including
`git merge-base --is-ancestor <planning_commit> <execution_base>`, the same
check from the declared base to `<execution_base>`, and then both checks against
the actual Ralph `HEAD` after branch creation/reuse. Compare the declared
manifest's content/path identities at the approved `planning_commit` and the
resulting branch base; a matching filename or a newly recomputed approval
digest is not sufficient.

The only supported transfers are (a) prepare the approved planning paths on the
intended Ralph branch under the existing project-authorized branch policy, then
commit them there, or (b) commit them on the authorized Core Feature branch and
create the exact Ralph branch from that approved planning HEAD when its target
or declared slice-base ancestry is verified. Do not cherry-pick the planning
commit, copy its source changes, merge a convenient target, rebase or reset a
wrong branch, or silently switch away from the verified execution base. These
operations can make artifact names look present while losing the approved
commit identity.

A wrong or existing branch base is a blocked checkpoint/preflight, not a repair
permission. Report the exact branch, observed HEAD/base, expected target or
slice base, `planning_commit`, `execution_base`, prefix, and missing manifest
identity. Recovery is to have the project owner authorize the exact branch
creation/reuse from the approved planning baseline, or return to the owning Core
planning command and prepare/commit the approved paths on the intended branch;
then rerun the checkpoint and clean preflight. Do not claim execution until the
new branch passes the same ancestry and artifact checks.

4. **Clean execution entry.** After the checkpoint, Ralph still runs its normal
   clean-worktree and branch preflight before task selection. The coordinator
   may not stash, reset, clean, discard, or bypass a dirty worktree to reach the
   queue. Declared run operational records (runtime, reviews, receipts, verdicts,
   evidence, PR bodies) and Spec Kit's workflow-run ledger may remain local or be
   committed separately under artifact policy; they do not block execution entry.
   A source, planning, test, policy, or unrelated dirty path, a wrong branch/base,
   or an unverified planning commit is a blocker; use the concrete recovery in
   the transfer contract above.
5. **Local bookkeeping.** Coordinator-only stage, lock, resume, and association
   bookkeeping belongs in the local ignored run runtime area,
   `.specify/delivery/<delivery_run>/runtime/`, and must not be staged as a
   planning or task commit. The central runtime contract at
   `.specify/extensions/delivery/templates/runtime.md` owns its state schema and
   helper integration when runtime arguments are present. Local bookkeeping
   must not make the next planning or execution entry dirty.

If project Git authorization is missing, stop with a concrete recovery rather
than asking Ralph to guess. Emit a blocked checkpoint naming the exact changed
paths, expected branch/base, missing authorization, and this recovery: have the
project owner authorize or create a planning-state commit limited to those
paths, or return the paths to the owning planning command and rerun the
checkpoint; then rerun Ralph from a clean verified branch. Do not stash, reset,
clean, stage unrelated changes, or claim that implementation ran.

A useful handoff is explicit about identity and status:

```text
SD_CORE_HANDOFF: PASS | BLOCKED
core_stage: initial | converge | simplify | outgoing-repair
delivery_run: <safe run id>
handoff_evidence: <exact .specify/delivery/<delivery_run>/runtime/core-handoff.md path or current .specify/delivery/<delivery_run>/runtime/result-checkpoint.json report reference>
approved_paths: <explicit normalized paths with producing owner>
content_fingerprint: <method and digest>
requirements_fingerprint: <method and digest>
native_output_manifest: <exact manifest identity and owner association>
task_ids: <exact IDs and order from tasks.md>
slice_mapping: <unchanged mapping or renewed approval reference>
target_branch: <verified target branch>
target_head: <verified approved target SHA or N/A for integration base>
branch_prefix: <resolved prefix>
branch: <verified Ralph branch>
base_head: <verified declared slice/base SHA>
planning_commit: <actual approved planning baseline SHA>
execution_base: <verified branch creation/reuse SHA containing planning_commit>
approval_association: <original approval fingerprint / content-equivalent commit association>
recovery: <required only when BLOCKED>
```

Do not use a context-only statement, a worker claim, or a changed fingerprint
as the checkpoint. The `handoff_evidence` must resolve to the exact local
`core-handoff.md` path or the current checkpoint result's report reference to
that path, and it must contain `SD_CORE_HANDOFF: PASS`. For a tracked SD
planning handoff, `PASS` also requires the concrete `planning_commit`, verified
`execution_base`, exact native-output manifest, approved paths, branch/base, and
post-branch identity checks described above. The checkpoint authorizes entry to
Ralph; it does not mark a task complete, waive Quality/Standards/Review, approve
a slice, or replace Core Analyze or Converge. The runtime checkpoint result can
transport this evidence, but only the native handoff authorizes its meaning.

## Canonical task and slice receipt identity

Receipt paths are derived from the explicit Delivery run, never from whichever
Feature directory happens to be discoverable:

- With `delivery_run=<safe-id>`, use exactly
  `.specify/delivery/<delivery_run>/task-verdicts.yml` and, for sliced runs,
  `.specify/delivery/<delivery_run>/slice-verdicts.yml`. Record the run identity
  in every receipt and nested task/review packet. A supplied Feature slug is
  metadata only; it must never change either path.
- Without `delivery_run`, the independently installed command has one narrow
  legacy fallback: only a non-sliced standalone Feature may supply an explicit
  `feature=<safe-id>` mapping, and the host/project must already have resolved
  that exact Feature unambiguously with its matching record. Use the matching
  `.specify/delivery/<feature>/task-verdicts.yml` path and record the legacy
  Feature identity. Do not infer it from a branch, directory scan, newest file,
  or one candidate. If the mapping is absent or ambiguous, stop with recovery
  instructions to rerun with an explicit `delivery_run` and canonical paths.
- A sliced invocation requires `delivery_run`; it never uses the legacy Feature
  fallback. When a run is supplied, reject conflicting Feature-derived receipt
  paths rather than falling back to them. There must be no
  `.specify/delivery/<feature>/...` leakage in a run-scoped task or slice
  receipt.

The receipt is evidence of the task/slice state, not a queue. Preserve prior
receipt history and finding/attempt identity on resume. Runtime bookkeeping stays
local as described above; it is not a substitute for a required task or slice
receipt.

## Completion boundary

In an SD Feature run, `<promise>ALL_TASKS_DONE</promise>` means that every task
from the current approved queue has its own verified Ralph commit and receipt,
and that Ralph has satisfied Core Converge's "implementation has run"
precondition. It does not mean that Converge, later Analyze, Simplify, final
Review, evidence, or handoff may be skipped. If Converge appends work, return to
the checkpoint sequence above. Core remains the owner of its append-only
Converge result and the SD coordinator remains the owner of routing that result
back to planning and Ralph.
