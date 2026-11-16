# Focused history and delivery audits

Load this guidance only for an explicitly requested history/architecture,
newcomer-comprehension, PR-performance, or recurring-defect audit. Delivery Explore
owns read-only research and returns its existing scope packet; this is optional
method guidance, not an automatic analytics service, new workflow, or repair queue.
Apply only the relevant sections below.

## 1. Bound the question and evidence set

Establish the repository/branches, affected area, question, and requested coverage.
For a time-window audit, resolve actual start/end timestamps, timezone, and whether
the cohort uses creation, update, merge, or incident occurrence. Reuse established
preferences; an unresolved `XX days` placeholder is not a usable window. Ask for
material missing choices while continuing independent source/governance reading.
Do not reinterpret a quoted example audit prompt as authorization to run it.

Use available read-only Git and tracker/CI tools. Record queries/filters, data
source and observation time, included record IDs, exclusions, and missing fields.
For an "all PRs/incidents" request, exhaust pagination and reconcile the complete
matching set before claiming full coverage. If access, retention, or resource
limits prevent that, label the result partial or sampled and state the unexamined
set/unknown coverage and its effect. Do not silently substitute the latest page,
merged-only results, or local Git history for the requested tracker population.
A missing decision-critical dataset blocks the affected conclusion; an explicit
limitation does not make an incomplete audit exhaustive.

Follow the relevant actual diffs, tests, discussions, deployment/incident evidence,
and subsequent fixes/reverts. Deduplicate records of the same event and preserve
source identity. Correlation, elapsed time, and repeated wording alone do not
establish a shared cause. Reuse existing evidence instead of rescanning unrelated
history, and report a bounded conclusion rather than promising an optimal design.

## 2. History and current design intent

Trace the relevant responsibility, interface, or compatibility mechanism from its
introduction through important revisions, follow-up repairs, and reversals.
Distinguish documented intent from inferred rationale. For each candidate, record:

- Original requirement/condition and the specific commit/PR/ADR evidence.
- Current consumers, supported versions/configurations, and applicable invariants.
- Whether the rationale still holds, its original condition is demonstrably obsolete,
  or the evidence is unresolved. Intentional code can later become obsolete.
- A behavior-preserving simplification, retained compatibility needs, and the
  production-path evidence required to justify removal, or a reason to retain it.

Age and absence of a local caller do not establish redundancy. Dynamic/external
consumers and support policy matter. Return supported simplification candidates to
Simplify's existing scan/accept/application/verify route; Explore does not delete
code or turn a historical inference into an approved design decision.

## 3. Newcomer comprehension

Use a concrete maintenance/change scenario to trace entry point → behavior owner
→ state/configuration → consumer → verification. List the concepts, files, hidden
invariants, ordering requirements, and missing/conflicting documentation a capable
newcomer must recover. Cite misleading names, responsibility splits, or indirection
that obscure that path. Distinguish essential domain complexity from accidental
context burden; do not invent onboarding hours from file counts or personal taste.

Propose the smallest clearer naming/ownership/interface model, showing which
concepts or navigation steps it removes and which guarantees must remain. A new
wrapper or document that preserves the same hidden coupling is not proof of lower
cognitive cost. Route accepted changes through their owning delivery lane; a broad
onboarding audit does not authorize unrelated refactors.

## 4. PR performance

First resolve what "slow" means: delivery latency (review/queue/CI/merge) or a
runtime regression introduced by code. If the intended target cannot be inferred,
ask the material question; report both only when both are requested and supported.

For delivery latency, define the exact metric and cohort before ranking. Use actual
events to distinguish draft time, time to first substantive review, revision cycles,
CI queue/run time, and merge waiting where data permits. Separate open PR age at
the observation time from completed cycle time; open records have no completion
duration. Account for overlapping checks, drafts, size, dependencies and external
waiting rather than summing overlapping durations or equating long-open with slow
code. Show sample size, missing timing fields, comparable baselines, and evidence
for each claimed bottleneck. Do not invent stage timings from creation/merge dates.

For runtime performance, name the scenario, environment, input/load, metric, and
budget/baseline when one actually exists. Inspect the implicated execution path and
use available profiles, traces, benchmarks, or a focused comparison at identified
revisions. Include uncertainty and correctness/resource trade-offs. A suspicious
loop or large diff is a hypothesis; PR duration is not execution-performance
proof. If telemetry or reproduction is missing, return a named measurement plan
and its owner instead of a confirmed regression or numerical improvement claim.
Mutation-heavy experiments belong to an authorized execution owner/environment.

## 5. Recurring bugs, rework, and rollbacks

Build an event set from explicit Issue/PR/commit, incident, review-finding, and
same-run repair associations. Do not infer continuity across runs from a matching
slug or title. Distinguish one unresolved defect and its repair attempts from a
verified recurrence after resolution, a repair-induced new defect, and intentional
scope/requirements changes. Reserved or replayed passes are not successful fixes.

Group by evidenced causal mechanism and escape point, retaining contrary examples
and contributing conditions. Explain the chain from trigger to invariant failure
to user/system impact, and why existing checks/review missed it. Multiple similar
symptoms may have different causes; missing original records remain limitations.

For each supported preventable pattern, propose the smallest effective control:

| Evidence and causal mechanism | Prevention/detection point | Proposed control and owner | Verification and cost | Adoption status |
| --- | --- | --- | --- | --- |
| <linked events, counterevidence, remaining uncertainty> | <earliest practical intervention> | <existing rule, project check, regression, or reusable skill update> | <failure it catches, false positives, maintenance cost, future outcome to observe> | <recommendation or actual governed acceptance> |

Prefer a project-owned automated check for deterministic invariants and a concise
rule or reusable skill for judgment that cannot be reliably automated. Check for
an existing owner/control before adding another; update it rather than duplicating
policy. Human error alone is not a causal explanation. Separate prevention,
detection, and mitigation, and do not claim a proposed rule prevents recurrence
until its effect has been observed.

## 6. Return through the existing owner

Use the exploration packet's history/source table, findings, options, risks,
verification, and next-owner handoff. Include audit scope/coverage and limitations,
ranked supported findings, alternatives/counterevidence, and proposed controls with
owners and acceptance evidence. No supported finding is a valid result.

Recommendations are not adopted policy. Project rules/automation/skills, product
edits, and tracker publication follow their existing governance and authorized
implementation paths. Do not rewrite historical receipts, create a second defect
ledger, allocate repair attempts, or add a new approval round. Keep durable adopted
policy in its existing owner; reference it from run evidence rather than copying it.
