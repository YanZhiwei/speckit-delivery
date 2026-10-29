---
description: "Route and orchestrate a complete Spec Kit delivery across feature, bugfix, and lightweight lanes"
---

# Spec Kit Delivery Route

## Input

```text
$ARGUMENTS
```

Read project governance and `.specify/extensions/delivery/delivery-config.yml`
when present. Identify the requested change and repository state. Select one
provisional, proportional lane; confirm or change it after investigation:

- **Feature** for new behavior, cross-module work, durable data, public API,
  security, or architectural change.
- **Bugfix** for a reported defect expected to have bounded scope; assessment
  must establish reproduction/red evidence before the correction. Multiple
  affected files alone do not require Feature.
- **Lightweight** for a mechanical, documentation-only, or
  behavior-preserving change.

Before mutation, announce the lane, durable records, Spec artifact policy,
integration capability, and verification entry points.

When invoking direct YAML workflows, obtain an explicit safe `delivery_run` id
and pass it unchanged (including resume and lane changes). Their command steps
are separate host processes: Explore must persist the canonical run packet before
returning, and consumers receive its exact path plus the actual gate choice. Use
the command/template's transport contract; context alone does not cross processes.
In shared-session orchestration, explicitly preserved context remains allowed
until a real run location is assigned. Never move an assigned canonical packet
when the Feature/bug identity later becomes known.

## Investigation and approval

For Feature and Bugfix, invoke `speckit.delivery.explore` after Doctor and
`speckit.decision.context mode=discover`. That command owns code/history/reference
research and the scope packet format; do not duplicate its investigation or
make GitHub/CodeGraph availability an unconditional installation requirement.

Before Feature specification, show the exploration packet's current directory
tree and candidate change tree in the conversation, with evidence, alternatives,
excluded scope, risks, and open questions. Obtain explicit user scope approval;
`EXPLORATION_VERDICT: ready` is not approval. Stop on decision-critical evidence
gaps or rejection. Record the approved scope, actual user decision, and explicitly
accepted non-critical research limitations in the packet or preserved context.
If the capability already exists, narrow the request instead of rebuilding it.

For Bugfix, pass exploration to `speckit.bug.assess`, which retains ownership of
reproduction and root-cause diagnosis. At its assessment gate, show both trees,
the fault path, red evidence, proposed repair, and excluded scope before asking
for scope approval. Missing reproduction is not a confirmed diagnosis or
permission to fix. Escalate to Feature only for new capability, material
architecture, or durable-contract decisions; carry evidence forward rather than
repeating the investigation. If a direct workflow must change lanes, stop it and
resume the appropriate workflow after explaining the reason.
Do not add a separate pre-assessment scope-approval round for Bugfix; the existing
assessment gate is its scope checkpoint. A blocked packet can still feed
authorized read-only assessment to collect missing evidence, but cannot authorize
specification or repair.

Pass the latest exploration packet to assessment; pass the scope-approved packet
(or explicitly preserved evidence when no feature path exists yet) to specify,
clarify, plan, and task generation.
Persist the packet once the real feature/run location is known, honoring
`artifact_policy`; do not invent a feature path before specify creates one.
At the existing plan gate, use the plan-checkpoint section of the installed
`delivery/templates/exploration.md`: present the finalized tree, file
responsibilities, interfaces, test paths/commands, risks, and scope differences.
Scope approval does not approve this detailed design. Reuse an explicit prior
approval only when it covers the unchanged evidence and design; do not ask the
same question after every command. Material expansion during planning or execution
reopens scope/design approval; ordinary in-scope test additions do not.

## Feature

Run the installed Spec Kit commands in this sequence, honoring the scope,
clarification, plan, and analysis gates just as the Feature YAML workflow does:

`speckit.delivery.doctor → speckit.decision.context (discover) → speckit.delivery.explore → scope approval → speckit.specify → speckit.clarify → clarification approval → speckit.decision.context (resolve) → speckit.plan → speckit.decision.propose → plan approval → speckit.tasks → speckit.analyze → analysis approval → speckit.quality.brief → speckit.ralph.run → speckit.quality.check → speckit.review.standards → speckit.converge → speckit.simplify.scan → speckit.docs-sync.run (when configured) → bounded review/fix loop → final review gate → speckit.decision.finalize → speckit.decision.check → speckit.simplify.verify → review freshness check → speckit.evidence.collect → speckit.delivery.handoff`.

Treat `tasks.md` as the only execution queue. When a standards, review, or convergence
finding remains, add or reopen a task and repeat `analyze → ralph → quality → standards → review`. A quality blocker, missing profile, unavailable configured check, or blocked standards verdict is a delivery blocker, not a passing warning.
Keep an ADR Proposed until the reviewed repository HEAD matches it; Accepted
ADRs must be self-contained and cannot depend on ignored Spec artifacts.

## Review and repair orchestration

Ralph requires task-scoped `speckit.review.run` before its checkbox/commit gate,
in addition to Quality and Standards. Final review uses `scope=outgoing-diff`
and the installed Review template's six dimensions; task approvals do not prove
integration correctness. The reviewer is read-only and independent where possible;
unavailable independence must be declared, not silently simulated.

Match each lane's YAML: up to three safe review/repair slots, each invoking
`speckit.review.run → speckit.delivery.review-fix`, followed by a final
`review.run` and review gate. The repair command owns lane routing, budget
accounting, and evidence refresh; do not duplicate its repair policy. Honor the
lower configured `max_review_fix_rounds` bound, never reset attempts after a
resume/new HEAD, and make slots after a complete current pass no-ops. A review
run without a repair does not consume the repair budget. At cap exhaustion,
unresolved blockers or incomplete coverage stop delivery instead of being waived.

Persist the reviewer report and stable finding states as coordinator-owned local
records. The report template owns snapshot/coverage/aggregation rules. Before
accepting a task or final pass, verify all dimensions, actual independence or
accepted degradation, the current content/requirements fingerprints, coverage,
and every earlier finding's explicit disposition. No report prose or exit code
replaces this gate. Reviewer fixes cannot be self-approved.

After ADR finalization, decision checks, or other post-review mutations, invoke
`review.run` again if needed to refresh the final snapshot; reuse an unchanged
complete pass instead of repeating the same review. Do not hide ADR/spec/source
changes as bookkeeping or reset the repair budget. Evidence/handoff cannot
proceed on stale, blocked, or incomplete review.

## Bugfix

Run `doctor → decision.context (discover) → explore → bug.assess → assessment/scope
approval → decision.context (resolve) → quality.brief → bug.fix → bug.test`, then
the Bugfix workflow's quality, standards, simplification, bounded review/fix loop,
review gate, decision check, review freshness check,
evidence, and handoff steps. Reuse the assessment as the bounded repair contract;
do not require a full Feature spec or a second root-cause report.

## Lightweight and completion

For Lightweight, follow its existing YAML sequence:
`doctor → quality.brief → delivery.lightweight → quality.check → review.standards
→ bounded review/fix loop → final review gate → evidence.collect → delivery.handoff`.
State the relevant paths and intended small scope;
do not require full exploration, external research, or two approval rounds for a
mechanical change. The command is complete only when its selected
lane has no blocking finding, all durable records match repository HEAD, and
the outgoing diff is supported by credible evidence.
