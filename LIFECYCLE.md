# Artifact lifecycle

| Artifact | Owner | Default lifetime | Final property |
| --- | --- | --- | --- |
| Constitution | Project | Durable | Governs every feature without duplicating ADRs |
| Issue | Tracker | Durable | Problem, scope, acceptance, outcome |
| `.specify/delivery/<run>/exploration.md` | Delivery | Follows `artifact_policy` | Code/history/reference evidence, current/candidate trees, actual scope approval and limitations |
| `spec.md` / `plan.md` | Feature | Project-configurable | Behavior contract and current approach |
| `tasks.md` | Feature/Ralph | Project-configurable | Single execution queue; closure requires current verdict receipts |
| `.specify/delivery/<run>/slices.md` | Delivery Slice | Follows `artifact_policy` | Approved slice boundaries, trunk-safety evidence, merge policy, and rollback; never a second execution queue |
| `.specify/delivery/<run>/task-verdicts.yml` | Ralph | Follows `artifact_policy` | Task snapshot, Quality/Standards/Review receipts, and verified commit association |
| `.specify/delivery/<run>/slice-verdicts.yml` | Ralph | Follows `artifact_policy` | Slice base/head, task range, prefix/flag/checkpoint evidence, and merge-mode verdict |
| `.specify/delivery/<run>/runtime/` | Delivery Runtime | Local ignored | Coordinator-only checkpoints, owner inputs/results, phase, approvals, and bounded-attempt bookkeeping; never planning or evidence content |
| Proposed ADR | Architecture | Tracked | Implementation baseline before coding |
| Accepted ADR | Architecture | Tracked | Self-contained truth reconciled with HEAD |
| `.specify/delivery/<run>/reviews/<scope>/review.yml` | Coordinator | Follows `artifact_policy` | Snapshot, six verdicts, independence, coverage, stable finding IDs |
| Review repair checkpoint | Coordinator | Same run lifetime | Attempt count/cap and unresolved IDs preserved across resume/new HEAD |
| Quality verdict | Task/Ralph run | Ephemeral by default | HEAD, scope, profiles, checks, pass/blocked |
| Standards verdict | Task/Ralph run | Ephemeral by default | Snapshot/scope, semantic rules and blockers |
| Evidence report | Delivery run/PR | Durable summary | Immutable reviewed/publication snapshots plus one Close-owned current outcome block (`delivered` / `abandoned` / `superseded`) |
| `.specify/delivery/<run>/pull-request.md` | Delivery Handoff | Follows `artifact_policy` | Rendered PR body and body path for `gh pr create --body-file`; not the GitHub UI template |
| PR body | Pull request | Durable | Change, risk, decisions, evidence |
| Package README | Package owner / Docs Sync | Durable | User install/API/limits and maintainer development/release contract derived from real package contents |

With an explicit `delivery_run`, the run is the identity for every run-scoped
packet and receipt: use exactly `.specify/delivery/<run>/`. A Feature slug is
metadata and must not relocate or select the packet. The only legacy fallback is
an explicit mapping for a non-sliced standalone Feature; sliced and workflow runs
must use the canonical run path.

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

## Runtime coordination and checkpoints

The portable helper is installed at
`.specify/extensions/delivery/scripts/delivery_runtime.py`. Run it from the
project root with Python 3.11 or later and Git on `PATH`; it uses the standard
library and Git only. It does not invoke a model, run project tests, edit
product code or tasks, create commits, or contact a tracker. The exact state
schema and owner boundaries belong to the [Delivery runtime contract](extensions/delivery/templates/runtime.md).

`close-record` is the one explicit Close-owned durability exception. The
standard-library module at
`.specify/extensions/delivery/scripts/delivery_outcome.py` validates a
verified tracker observation and atomically writes only the Evidence current
outcome block; it does not contact the tracker or create a commit. The
`delivery_runtime.py close-record` wrapper refreshes the hash-bound
`evidence_observation` only after that Evidence write succeeds; a failed
validation leaves Evidence and runtime state unchanged. Other Runtime
operations remain coordinator bookkeeping and do not gain durable
Evidence-writing authority by analogy.

The `.specify/delivery/<run>/runtime/` directory is coordinator bookkeeping;
Spec Kit's `.specify/workflows/runs/` operational ledger is likewise local.
Declared run operational records (`runtime/`, `reviews/`, `receipts/`, verdicts,
`evidence.md`, PR bodies) do not block a clean execution entry; source, planning,
test, policy, and unrelated dirty paths still do.
`init` adds both exact rules to Git's local `.git/info/exclude` and preserves
existing entries; already tracked files stay tracked. This local ignore does not
change `artifact_policy`: canonical planning artifacts, run-root packets and
receipts, and `evidence.md` retain their existing tracked/ephemeral rules;
`evidence.md` remains durable.

The `/sd` control surface provides these run-safe actions:

- `action=help` describes the selected lane, records, gates, runtime location,
  and next safe action without starting a lane or invoking a model.
- `action=status delivery_run=<id>` reads one run; status with no run lists
  runs. It is read-only and does not guess from recency.
- `action=resume delivery_run=<id>` recovers only the same run's pending owner
  action, input ticket, approval, or reserved attempt; it never resets identity
  or allocates a replacement attempt.
- `action=checkpoint delivery_run=<id> stage=initial|converge|simplify|outgoing-repair`
  applies the [Core/Ralph adapter](extensions/delivery/templates/core-adapter.md)
  and checks approved paths, fingerprints, Git authorization, the current Analyze
  result, and a clean execution entry. The coordinator may commit only the exact
  approved planning paths under already established project Git authorization;
  the helper never commits. It cannot stage unrelated work, approve design, or
  start Ralph from a dirty entry.
- `action=phase delivery_run=<id> name=<phase>` records the current owner phase
  only; it does not assert completion. Handoff readiness requires current Review
  and same-run Evidence.

Workflow shell conditions consume the runtime's newline-free `needs` booleans.
When a need is false, the conditional branch is not dispatched at all, so there
are no fixed no-op model slots. Review and Converge reservations persist in the
run checkpoint across process restarts and new HEADs; the native repair owner
uses the reserved attempt, and the final `require` guard fails after the cap
while blockers or incomplete evidence remain. Runtime checks transport identity,
freshness, completeness, and hashes of native reports; Quality, Standards,
Reviewer, Core, and Ralph remain the semantic owners. A valid envelope or zero
exit status is not automatic semantic judgment.

For Feature work, the planning-to-execution checkpoint is the clean handoff in
the Core adapter. The single combined Analyze/execution/Slice gate follows
slice planning, and the Delivery writer records the actual choice before Ralph
consumes the approved queue. Do not duplicate the YAML sequence here; use the
central [runtime](extensions/delivery/templates/runtime.md) and [adapter](extensions/delivery/templates/core-adapter.md)
contracts.

## Delivery record outcome and retirement

`evidence.md` is the durable record. Run-root files under
`.specify/delivery/<run>/` are workspace and follow `artifact_policy`; its
`runtime/` child is the local coordinator bookkeeping described above. When the
policy is ephemeral, exploration, slices, receipts, verdicts, review reports,
and the rendered PR body stay local and are published only through the PR body.
Evidence has two layers: one unique Close-owned current outcome block and
append-only validation/review/CI/limitation snapshots. The current block is the
only authority for the present terminal status. Snapshot text such as "awaits
CI" or "not merged" remains true only for its recorded observation time and
must carry its `reviewed_head` and limitation context.

### Head identity and merge proof

A Delivery record keeps these identities separate:

- `reviewed_head` is the exact revision whose bytes and requirements native
  Review and Evidence validated. Native reports and receipts retain this value
  immutably.
- `original_pr_head` is the historical PR head observed from the tracker
  (`head_revision` in the verified observation). It may equal `reviewed_head`,
  but it is never renamed to the merge result.
- `base_revision` is the tracker-observed target/base used for content comparison.
- `merged_revision` is the actual tracker merge commit and the effective
  delivered head. Squash and merge commits normally differ from both historical
  identities; no Review is relabeled as a Review of this commit.

Before publication, Evidence records `original_pr_head` as pending. After
publication, Close binds the verified tracker `head_revision` to
`original_pr_head`. If that head differs from `reviewed_head`, Evidence must
contain an explicit `published_head` binding and content-equivalence or exact
bookkeeping/archive proof. An archive binding uses
`reviewed_diff_archive`, `reviewed_diff_archive_sha256`,
`reviewed_diff_archive_base`, `reviewed_diff_archive_head`, and
`reviewed_diff_archive_reviewed_head`; partial or mismatched bindings block. A
source change cannot be hidden as a bookkeeping change. A missing old reviewed/PR
object is not itself a reason to rewrite Git:
when the trusted verified tracker head equals the recorded `reviewed_head`, it is
an accepted historical mapping (`tracker-head-mapped`) and the current block
still says that the Review was historical. If the heads differ and proof is
missing, Close fails closed.

For `merged`, the tracker observation must provide the actual merge commit;
`merged_revision` must be a locally reachable commit. When the PR head object is
available, compare the complete base-to-PR-head and base-to-merge path/mode/byte
content. When it is unavailable, use an exact immutable evidence archive with
the same base, PR head, changed paths/modes, bytes or patch, and digest when one
exists; a bare fingerprint, URL, report, or limitation is not an archive. The
trusted tracker mapping is the only clean-clone fallback when the historical
head is absent and it equals `reviewed_head`; it never claims a new review of
the merge commit. Do not fetch arbitrary branches, reset, rewrite, force-update,
or delete refs to repair a missing old object.

The read-only tracker response is saved at the exact run-relative
`.specify/delivery/<run>/runtime/observed-pr.json` path and has schema version 1
with no extra keys:

```json
{
  "schema_version": 1,
  "delivery_run": "<id>",
  "lane": "feature|bugfix|lightweight",
  "provider": "github",
  "repository": "owner/name",
  "number": 31,
  "state": "MERGED",
  "head_revision": "<PR head SHA>",
  "base_revision": "<base SHA>",
  "merged_revision": "<merge commit SHA>",
  "merged_at": "<RFC3339 timestamp>",
  "observed_at": "<RFC3339 timestamp>",
  "url": "https://github.com/owner/name/pull/31"
}
```

A `CLOSED` observation keeps the head/base and observation fields but uses null
`merged_revision` and `merged_at`. The verified PR input must match its provider,
repository, and number. After obtaining this read-only observation, Close runs
from the project root:

```text
<python> .specify/extensions/delivery/scripts/delivery_runtime.py close-record --run <id> --outcome merged --pr <number-or-url> --verified --file runtime/observed-pr.json
```

The operation validates the exact JSON, same-run/lane/PR identity, local merge
reachability, and the available head/content proof, then atomically replaces
only the current block. It does not contact the tracker, create a commit, or
write runtime state. A failure leaves both Evidence and runtime state unchanged.

The block uses stable delimiters and fields so old occurrences cannot become
current authority:

```text
<!-- DELIVERY_CURRENT_OUTCOME_BEGIN -->
## Current delivery outcome

- **delivery_run**: <id>
- **lane**: feature | bugfix | lightweight
- **status**: delivered | abandoned | superseded
- **outcome**: merged | closed | superseded
- **pull_request**: <canonical provider/repository/number or URL>
- **reviewed_head**: <historical reviewed SHA>
- **original_pr_head**: <historical tracker head SHA>
- **published_head_proof**: tracker-head-mapped | published-content-equivalent | published-evidence-archive
- **base_revision**: <tracker base SHA>
- **merged_revision**: <reachable effective merge SHA or null>
- **effective_head**: <merged_revision or null>
- **merged_at**: <tracker merge time or null>
- **observed_at**: <tracker observation time>
- **outcome_recorded_at**: <RFC3339 timestamp>
- **verification_file**: .specify/delivery/<id>/runtime/observed-pr.json
- **merge_proof**: diff-equivalent | evidence-archive | tracker-head-mapped | not-applicable
<!-- DELIVERY_CURRENT_OUTCOME_END -->
```

Close updates only this current block and preserves native reports, historical
snapshots, and limitations unchanged. A legacy record without the block may
receive one structural historical-snapshot label while its existing bytes remain
verbatim. Repeating the same verified operation is idempotent; a different
concrete PR or terminal outcome is a conflict and needs the authorized recovery
path.

[Doctor](extensions/delivery/commands/speckit.delivery.doctor.md) is phase-aware
when it audits missing evidence. In a legitimate active pre-Evidence phase, an
absent `evidence.md` is allowed only when no evidence was
previously recorded and the required packet/checkpoint exists. A missing file
after Evidence was recorded, in a final/terminal phase, or after a previously
recorded evidence file disappeared is a blocker. Findings for unrelated runs are
maintenance findings, not current-run identity changes; unavailable remote facts
remain `unverified`.

Handoff readiness is not a terminal outcome: `HANDOFF_READY: ready` means the
reviewed PR body is ready for separately authorized publication and the run is
waiting for publication or its observed outcome. After the pull request merges or
closes, `speckit.delivery.close` records the actual outcome. `merged` becomes
`delivered`; `closed` without merge becomes `abandoned` and keeps one self-contained
retirement note; a replaced run becomes `superseded` with a resolvable
`superseded_by`. If the PR, tracker, credentials, outcome, merge commit, or proof
cannot be verified, Close returns `unverified` and stops before writing terminal
status/history or deleting any workspace. Absence of `status` means active, and a
record that contradicts the real PR outcome is not closed. Retirement deletes only
that run's allowlisted workspace artifacts and never `evidence.md` or another run.

Installation, upgrade, bootstrap, and manual governance actions are operational
one-offs, not delivery runs. Their authoritative record belongs to the project's
durable evidence root; do not maintain a second copy under `.specify/delivery/`.

## Review and repair records

The [Reviewer contract](extensions/review/templates/reviewer.md) owns finding and
snapshot rules. A report is bound to base/HEAD/merge-base plus actual contents and
requirements, not HEAD alone. Uncommitted and relevant untracked files count.
Only declared bookkeeping may be excluded; ADR/spec/test/source changes invalidate
reuse. A selected optional method's configuration/resource identity is part of the
requirements/policy identity; changing that provider also invalidates reuse. Preserve `open → fixed-pending-review → resolved` or evidence-backed
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
