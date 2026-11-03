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
Include the architecture checkpoint below in the same plan and approval. Plan
records its actual path in the canonical exploration packet. After Decision
Propose establishes the Proposed ADR baseline, the pre-gate coordinator records
the final presented content fingerprint there: hash method, input manifest, and
digest covering the plan, clarified requirements, cited governing policy/ADRs,
and Proposed ADR baseline. Present that final design/ADR/constraint snapshot for
the existing gate. Do not freeze the approval baseline before Propose can change
its inputs. A shared-session router may preserve the same exact reference and
identity in context. The receiving Tasks consumer recomputes that identity before
recording the actual plan-gate choice against it. Missing baseline, changed inputs, or missing choice
stops progression for refreshed presentation/approval; never rewrite the presented
fingerprint to make an old choice fit. Later consumers preserve the approved
snapshot and apply current content/requirements freshness checks. Substantive
constraint/design changes reopen approval. Expected later ADR status finalization
uses Decision reconciliation and fresh Review: preserve the original approval
identity and record the comparison instead of relabeling it. Record approval
against the shown design, including constraints and verification gaps, not the
earlier candidate tree. Reopen scope approval for material expansion; ordinary
in-scope test additions do not restart the workflow.

### Architecture constraints

Before choosing the implementation design, read applicable root/scoped agent
instructions, Constitution, active ADRs, configured architecture policy sources,
and owning-module documentation. Follow their relevant links; do not infer rules
from a filename or silently adopt another project's architecture. Reuse Explore's
code/history/reference evidence and distinguish binding project rules from new
recommendations. In `plan.md`, include an `Architecture constraints` section:

| ID | Source and authority | Constraint and affected paths | Design response | Owner and verification | Evidence state / gap |
| --- | --- | --- | --- | --- | --- |
| AC-01 | <path/section; binding rule or proposed choice> | <ownership, dependency, interface, state, or failure constraint> | <how this design satisfies it> | <project command/test path or named semantic review> | <existing, planned, semantic-only, unsupported; evidence or next action> |

Cover relevant component/data ownership, dependency direction, public interfaces,
compatibility, failure/degradation behavior, and non-functional requirements.
Explain why a concern does not apply; do not invent performance targets or force
layers, interfaces, or infrastructure with no evidenced need. Compare viable
approaches on these constraints, including extending/reusing the current design.
For a small understood extension, a short comparison is enough; record why no
additional architecture decision or research is needed.

Every applicable binding rule needs a design response, a verification owner, and
a credible mechanism. Distinguish a planned test/check from one that already ran,
and semantic review from automated enforcement. Record unsupported checks and
open decisions with their impact and resolution owner. Decision-critical gaps
block design approval. Accepting a limitation does not waive a binding rule or
its mandated enforcement; an exception follows that rule's governance process.
Keep durable choices in Proposed ADRs through the existing Decision lifecycle.

### Optional skill methods

`method_adapters.design` in Delivery configuration defaults to `builtin`: use this
checkpoint directly without another helper/model round. When an external method
is configured, use the installed `speckit.delivery.method phase=design` with this
run's exact exploration, clarified requirements, constraints, and plan references.
Its shared `templates/method-adapter.md` owns verified local resource selection,
identity, fallback/block behavior, and the result contract. The design profile
returns analysis to Core Plan; it does not write another plan or approve an ADR.

Record the receipt, adopted/rejected guidance, and any fallback reason in the
plan's sources. Include selected configuration/resource identity in the presented
input manifest and subsequent freshness checks. A blocked required method or
owner evidence gap stops the checkpoint. Missing optional configuration keeps
the builtin path available. External guidance remains a recommendation under
project governance; do not install skills or run their whole workflow/scripts.
