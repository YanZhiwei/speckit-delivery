# Feature Delivery Workflow

The full lane for new behavior and architectural change. Doctor and ADR discovery
precede `speckit.delivery.explore`; a scope gate reviews code/history/open-source
evidence and the current/candidate directory trees before `specify`. The original
request and approved packet flow into specification, clarification, and planning.

Supply required `delivery_run=<safe-id>` when starting, and reuse it on resume.
Explore persists its canonical run packet before returning; Specify receives its
exact path and the real scope-gate choice, not another process's lost context.
The packet stays at that run path after Feature creation. Gates display the file;
receiving commands record actual approval and reject missing/stale inputs.

The existing plan gate reviews finalized paths, file responsibilities, interfaces,
test locations/commands, risks, and scope differences before tasks. See the
[Delivery contract](../../extensions/delivery/README.md) for research, output,
approval, and artifact policy. A material scope change reopens approval; if the
lane is wrong, stop this workflow and carry evidence to the correct lane.

Version `0.1.x` uses explicit human gates and three safe no-op convergence
iterations because command-step prose is not a machine-readable semantic result.
Later versions will use a state protocol and custom result gate.

Ralph requires task-scoped Review as well as Quality/Standards. Final integrated
Review uses up to three `review.run → delivery.review-fix` slots (or the lower
configured repair budget), then final review and an aborting gate. A complete
current pass makes remaining slots no-ops; blocked/incomplete cannot be waived.
Repair attempts and finding IDs survive resume/new HEAD. Feature repairs remain
in `tasks.md`; no recursive Ralph for an open task and no dirty-entry bypass.
ADR finalization/checks are followed by freshness review before evidence/handoff.
See the [Reviewer contract](../../extensions/review/templates/reviewer.md).
