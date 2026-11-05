# Feature Delivery Workflow

The full lane for new behavior and architectural change. It starts the portable
[Delivery runtime](../../extensions/delivery/templates/runtime.md), then runs
Doctor and ADR discovery before `speckit.delivery.explore`. A scope gate reviews
code/history/open-source evidence and the current/candidate directory trees before
`specify`.

Supply required `delivery_run=<safe-id>` and a verified `runtime_python`
invocation (default `python`; for example `python3` or Windows `py -3`) when
starting, and reuse both on resume. Explore persists its canonical run packet
before returning; Specify receives its exact path, the real scope-gate choice, and
must emit the actual `FEATURE_DIR:` for runtime binding. The packet stays at that
run path after Feature creation. Gates display the file; receiving commands record
actual approval and reject missing/stale inputs.

The existing plan gate reviews finalized paths, file responsibilities, interfaces,
test locations/commands, risks, scope differences, and the `Architecture
constraints` table before tasks. The table stays in the actual feature plan, whose
exact path is recorded in the canonical packet. After Decision Propose, the
coordinator records the presented content/input identity before the gate; Tasks
checks it before binding the actual approval choice. Tasks/Analyze preserve
constraint IDs and verification work; pre-edit Brief and task/final Review consume
applicable rows. Optional architecture skill methods follow the shared Plan
checkpoint and cannot replace project governance or the existing workflow. See the
[Delivery contract](../../extensions/delivery/README.md) for research, output,
approval, and artifact policy, and the
[Core/Ralph adapter](../../extensions/delivery/templates/core-adapter.md) for the
task shape and planning transition. A material scope change reopens approval; if
the lane is wrong, stop this workflow and carry evidence to the correct lane.

After task generation, `speckit.delivery.slice` binds the real task IDs to
internal review slices and resolves the execution mode, publication mode, and
slice-to-publication-group map. Analyze runs against the planned mapping; a
runtime guard then requires a current passing Analyze result before one combined
execution/slice gate reviews task coverage, trunk-safety evidence, risk-based
behavioral probes, diff budgets, flags, merge method, publication groups, and
rollback. The Delivery `action=record-approval` writer records the actual choice
and unchanged fingerprint. A project-authorized planning checkpoint follows
before Ralph. `tasks.md` remains the only execution queue; `slices.md` is
boundary/publication metadata and cannot add, remove, or reorder tasks. Ralph
stops at each internal boundary for the declared prefix/flag/checkpoint and
behavioral-probe verification. A failed classification-specific check reopens
slice planning instead of continuing the plan. `handoff slice=<id>` renders an approved layer
or internal boundary artifact; under `Publication mode: single` it does not
imply a separate PR. The workflow's final `mode=auto` handoff follows the
approved publication groups. Creating, pushing, or merging a PR still requires
separate authorization.

If Converge appends tasks, the workflow routes them through Delivery Slice again,
a fresh Analyze, a renewed combined gate and approval writer, the planning
checkpoint, and Ralph before reassessing. A no-gap Converge, or a converged
reassessment, skips all of that work. A configured or three-pass ceiling that
still has unresolved work fails the final runtime requirement.

If Simplify proposes candidates, an aborting-or-skip presentation gate records the
actual choice. Accepted candidates are applied by existing lane owners (Feature
uses Core Converge to append tasks, then the same analyze/approval/checkpoint/Ralph
path) and verified by native `simplify.verify`; rejected candidates skip further
optional work. The proposal stays immutable and cannot become a second queue.

Before final Quality/Standards/review, `speckit.docs-sync.package-readme` keeps
every touched package README true to its manifest, public exports, CLI,
configuration, dependencies, and real test commands. A new package also records
two or three comparable public READMEs and what was adopted or rejected. A
README-affecting change cannot be reported unchanged without citing the lines that
remain correct.

Review starts with one independent native six-dimensional pass. Runtime
`needs --kind repair` enters a durable bounded repair loop only for a current
confirmed repairable blocker; each iteration reserves an attempt, applies one
lane-owned repair pass, refreshes current Quality/Standards, and independently
re-reviews. A current complete pass skips all remaining dispatches. The final
runtime guard and human review gate both reject blocked, incomplete, or
cap-exhausted findings. Attempts and finding IDs survive resume and new HEAD; a
dirty preflight, stale evidence, or scope change blocks rather than bypassing.
See the [Reviewer contract](../../extensions/review/templates/reviewer.md).

After ADR finalization and decision checks, changed contents require refreshed
Quality, Standards, Review, and accepted-simplification verification before
Evidence and Handoff. This is transport freshness, not a claim that a host exit
code proves semantic quality.
