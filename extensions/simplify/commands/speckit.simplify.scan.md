---
description: "Find evidence-backed simplification candidates and route them without expanding scope silently"
---

# Simplification Scan

## Input and run/output binding

```text
$ARGUMENTS
```

A direct Delivery invocation must supply explicit
`lane=feature|bugfix|lightweight` and `delivery_run=<id>`. For Bugfix, also use
the coordinator's explicit `bug_slug` and approved assessment reference when
provided; the run id is never a Bug slug. Validate the run as one safe path
segment and use only `.specify/delivery/<delivery_run>/`.

The candidate report is canonical at
`.specify/delivery/<delivery_run>/simplifications.md`. Exploration,
decision-context, code-context, slices, and evidence remain separate files at
that same run root. Per-run operational state/results belong under
`.specify/delivery/<delivery_run>/runtime/`; follow the central owner at
`.specify/extensions/delivery/templates/runtime.md`. When either `runtime_stage` or `runtime_result` is supplied, require the
canonical `delivery_run`, read `.specify/extensions/delivery/templates/runtime.md`
in full, and follow that runtime contract; do not invent helper flags, paths, or
result schemas. Use the runtime `owner-result` helper with the native candidate
report and a stage data JSON, or write the exact machine `native_receipt` and
normalized envelope the contract defines, with the real
candidate ID list and report bytes. With neither argument, do not create runtime
state here.

A standalone invocation without `delivery_run` may inspect the current outgoing
diff, but returns candidates inline and reports
`SIMPLIFICATIONS_PATH: inline`; it must not infer another active Feature, create
a directory, or write to a guessed Feature path. Scan the repository broadly only
when the user explicitly requests a broad audit; otherwise use the current
outgoing diff.

## Read-only boundary

Read project governance, decisions, architecture, dependency policy, and the
lane's approved requirement source before judging an intentional seam. Inspect
production consumers, dynamic registration, configuration, serialization,
plugins, scripts, examples, migrations, external contracts, tests, and docs
before claiming absence.

Until an explicit simplification gate approves the candidates, this command is
read-only with respect to source, tests, docs, configuration, Bug assessment,
and every execution queue. It must never edit `tasks.md`, add `forcedTasks`,
change a Bug report/assessment, or apply a source deletion. It may write or
update only the supplied run's canonical `simplifications.md` report (or return
it inline without a run). After approval, the owning lane may apply an accepted
route; this scan still does not impersonate that approval or perform the edit.

## Procedure

1. Establish the exact lane, run, reviewed HEAD, outgoing diff, changed paths,
   and requirement/policy inputs. A missing or mismatched supplied run is a
   blocker; do not select the newest run or active Feature.
2. Look for unused public methods/config/events, tests-or-docs-only behavior,
   duplicate representations, unused seams, speculative generality, redundant
   lifecycle state, obsolete compatibility machinery, and hand-rolled behavior
   covered by a healthy builtin or dependency.
3. For each candidate, classify consumers as production, non-production, or
   ambiguous. Record the concrete evidence inspected, capability trade-off,
   likely risk, and net deletion estimate (removed implementation/tests/docs
   minus remaining glue and compatibility cost). A wrapper that relocates the
   same complexity is not a simplification.
4. Assign a lane-aware route without applying it:
   - **Feature:** after approval, a behavior-preserving local candidate may enter
     the existing `tasks.md` queue through the owning workflow; a public or
     requirements change routes to clarify/plan; an architecture change routes
     to a Proposed ADR; out-of-scope work routes to an issue/proposal without
     creating a tracker resource here.
   - **Bugfix:** route through the approved Bugfix assessment/continuation and
     its official repair scope. Do not create Feature tasks or force a Feature
     spec; escalate to Feature only when the evidence shows new capability,
     material architecture, or a durable-contract change.
   - **Lightweight:** keep a behavior-preserving/mechanical candidate within the
     bounded request and its checks. Do not create Feature artifacts or use
     `forcedTasks`; if the candidate expands behavior, compatibility, data,
     security, or architecture, recommend the appropriate lane change and stop.
5. Write the complete candidate report to exactly
   `.specify/delivery/<delivery_run>/simplifications.md` when a run exists. Do
   not write source, queues, assessments, or another run's report. With no run,
   return the report inline.
6. If no evidence-backed candidate exists, record a successful no-op rather than
   inventing work or treating the absence as a blocker.

## Output

```text
SIMPLIFY_SCAN: candidates | none | blocked
LANE: <feature|bugfix|lightweight|standalone>
DELIVERY_RUN: <id or none>
SIMPLIFICATIONS_PATH: <.specify/delivery/<id>/simplifications.md or inline>
CANDIDATES:
- <id>: <candidate, consumer classification, evidence, trade-off, net deletion>
ROUTES:
- <id or none>: <lane owner and approval-dependent next route>
APPROVAL: pending
BLOCKERS:
- <id or none>: <concrete recovery>
```

The scan leaves `APPROVAL: pending`; the owning lane gate/coordinator records the
actual accepted or rejected candidate IDs against the unchanged report or its
same-run runtime gate receipt. `none` (no candidates) is a valid no-op with
`BLOCKERS: none`; it does not
append a queue item and does not require Simplification Verify to manufacture an
accepted candidate. `blocked` must name the missing identity, evidence, or policy
input.
The command is complete when every proposed candidate has consumer evidence,
capability trade-offs, a lane-correct approval-dependent route, and the
canonical report or inline result is clearly identified.
