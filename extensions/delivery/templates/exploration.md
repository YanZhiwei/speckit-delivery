# Exploration and scope packet

Use this format for `speckit.delivery.explore`. Replace placeholders with read
evidence; remove example paths rather than presenting them as repository facts.

## Request and investigation

- Request and desired outcome: <summary>
- Delivery run / canonical packet path: <actual assigned identity and path>
- Feature location / Bug slug: <when known; not inferred from delivery run id>
- Investigation: existing capability | new capability | defect
- Provisional lane / recommended lane: <lane and reasons>
- Baseline HEAD / relevant working-tree changes: <SHA and paths>
- Governing instructions / ADRs: <sources and constraints>
- Tools / fallback / freshness limitations: <what was actually used>

## Findings

- Facts: <current behavior, satisfied needs, gaps; cite source/tests>
- Hypotheses: <unverified explanations and how to test them>
- Recommendations: <proposed choices, not user decisions>
- Unknowns: <missing evidence and its effect on scope>

## Current directory tree

```text
<repository>/
├── <existing directory>/
│   └── <verified key file>       # Responsibility; evidence reference
└── <existing test directory>/    # Existing verification surface
```

For an empty repository, show the actual available scaffold and explicitly state
that the capability has no implementation. Do not fabricate existing files.

## Current flow

<Entry → processing/configuration/storage → consumer/output; cite files/symbols.
For a defect, mark the suspected break as a hypothesis until assessment verifies it.>

## Project history and external references

| Source / repository | Issue / PR / commit / version | Read paths and evidence | Relevance / adopted idea | Rejected parts / constraints / scope impact |
| --- | --- | --- | --- | --- |
| <current project or reference> | <links and fixed SHA where applicable> | <actual diffs, code, tests, discussion> | <finding> | <fit and limitations> |

- Search coverage: <queries/areas and records read; relevant follow-up fixes/reverts>
- External research: performed | skipped with reason | unavailable | no suitable result
- Evidence gaps: <impact, next action, and explicit acceptance needed if applicable>

## Options and candidate change tree

Compare viable alternatives and recommend the smallest justified option. State
why reuse is insufficient before proposing a new module or directory.

```text
<repository>/
├── <existing path>               [modify] Candidate responsibility/change
├── <proposed path>               [new] Proposed, does not exist yet
├── <existing dependency>         [reuse] Existing capability to preserve
├── <existing consumer>           [no-change] Why it should remain untouched
├── <unresolved area>             [uncertain] What must be checked
└── <test path>                   [new/modify] Planned verification surface
```

Use tentative labels such as `预计修改`, `预计新增`, `复用`, `不改`, and `待确认`
when presenting in Chinese. Every existing path must be verified; proposed test
paths must be marked new. Trees cover only relevant areas, not every repository file.

## Scope, risks, and verification

- Included / excluded scope: <boundaries and reasons>
- Interfaces, compatibility, migrations, security: <known impact or unknown>
- Verification: <existing tests, proposed regression seam, commands if verified>
- Defect handoff: <user symptom, logs/configuration, existing repro evidence;
  what bug.assess must still establish, not a duplicate diagnosis>
- Decision blockers / questions: <only matters that affect scope or safety>

## Checkpoint record

- EXPLORATION_VERDICT: ready | blocked
- Evidence location: <actual path or preserved context>
- SCOPE_APPROVAL: pending

The router/workflow records the user's actual approval or rejection, approved
scope, and accepted non-critical limitations here (or in preserved context).
Do not infer approval from a ready verdict. If the baseline or material scope
changes, refresh the affected evidence and obtain renewed approval.

Direct workflows persist this packet before Explore exits, and pass its exact
path plus the actual gate choice into the next host process. The receiving
command records that choice, approved snapshot/scope, and accepted limitations;
the gate does not edit this file. No missing receipt is replaced with inferred
approval. Preserve the same run path across later Feature/bug identification.

## Plan checkpoint (later, not an exploration deliverable)

Keep exact design in `plan.md`; reference this packet instead of duplicating it.
At the existing plan gate, present the finalized change tree with file
responsibilities, interfaces/data flow, test paths and verification commands,
compatibility/migration/security risks, and differences from the approved scope.
Record plan approval against the shown design, not the earlier candidate tree.
Reopen scope approval for material expansion; ordinary in-scope test additions
do not require restarting the workflow.
