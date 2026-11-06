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

## Concepts, boundaries, and research questions

Keep this proportional to the request; a small understood change can use a few
lines. Establish provisional meanings and boundaries before broad research,
then revise them from evidence. Do not present a proposed glossary as project policy.

| Term | Meaning in this request / authoritative source | Ambiguity or excluded meaning |
| --- | --- | --- |
| <core concept> | <project definition, or explicitly provisional meaning> | <conflict and scope impact, or none> |

- Domain boundary: <included responsibility, adjacent owners, and non-goals>

| Question / decision affected | Evidence and source identity | Conclusion / conflicting evidence | Remaining gap, impact, and next owner |
| --- | --- | --- | --- |
| <bounded question> | <read paths, version/commit, tests or observations> | <supported, rejected with reason, or unresolved> | <decision-critical or non-critical; next action> |

Preserve rejected hypotheses and their verification/rejection reasons so a later
context does not repeat them as new proposals. Multiple agents citing the same
upstream source are one evidence origin, not independent corroboration. Reconcile
conflicts against source versions, applicability, and observed behavior; do not
settle them by vote. For defects these remain assessment inputs, not a confirmed
root cause.

Research stops when decision-relevant concepts and boundaries are clear, viable
options have enough evidence for scope discussion, and material conflicts are
resolved or explicitly blocking. Report residual gaps and their impact. A time or
resource limit may stop research but cannot turn a critical gap into readiness;
non-critical limitations require the existing gate's explicit acceptance. Neither
a fixed agent count nor a claim to have collected all facts is a stopping rule.

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

## Phase handoff

Delivery's coordinator prepares a reusable reading map in this canonical packet
before the relevant approval snapshot is frozen, referencing Decision Context,
Code Context, and Quality Brief
outputs when relevant and current. Do not rerun those owners or copy their full
reports merely to fill a handoff. Use the receiving role's contract: Ralph owns
the implementation task packet; Review owns its reviewer input and report.

For each actual phase handoff, identify:

- Receiving owner, question/outcome, acceptance evidence, allowed operations and
  paths, and conditions that require returning to the coordinator.
- Exact approved scope/design references and actual decisions, or pending status;
  known conflicts, rejected approaches, and remaining evidence gaps.
- Required reading: path plus section/symbol, why it matters to this decision,
  and its authority (binding rule, approved design, observation, or recommendation).
  Separate conditional reading with an explicit trigger from the required minimum.
- Input identity: run, baseline and relevant working-tree state, and existing
  approval/snapshot references. Bind relied-on sources through the owner's existing
  requirements/design identity contract; never invent another receipt format or
  add unrelated paths to the planning-commit manifest.
- Expected return: conclusion with source citations, verification performed and
  results, unresolved questions, and any proposed scope/design deviation.

Pass exact resolvable paths to another process; a prior chat or a filename alone
is not the handoff. The receiver checks required sources and identity before
acting. Missing, stale, or conflicting decision-critical inputs return a named
gap and recovery action to their owner; authorized read-only investigation can
continue to resolve that gap. Optional missing sources remain explicit limitations.
File existence and hashes establish identity, not understanding: the receiver's
design response or result must connect the relevant sources to its decisions.
Keep the handoff in the existing packet/owner output, honoring artifact policy;
do not create a second knowledge store, execution queue, or approval round.
After approval, reference the unchanged map and snapshot in the receiving owner's
existing input/output. Do not rewrite the approved packet to log routine dispatch
or repeat an earlier decision. A change to relied-on evidence, scope, or design
requires the affected owner's normal freshness and approval handling.

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

For each proposed new responsibility, state owner, interface, dependency, or
lifecycle mechanism, explain the requirement/invariant it serves and why the
existing owner or mechanism cannot satisfy it. Keep local implementation details
proportional; naming a familiar architecture pattern is not evidence of need.

Every applicable binding rule needs a design response, a verification owner, and
a credible mechanism. Distinguish a planned test/check from one that already ran,
and semantic review from automated enforcement. Record unsupported checks and
open decisions with their impact and resolution owner. Decision-critical gaps
block design approval. Accepting a limitation does not waive a binding rule or
its mandated enforcement; an exception follows that rule's governance process.
Keep durable choices in Proposed ADRs through the existing Decision lifecycle.

### Cooperation and context plan

In the same `plan.md`, describe who coordinates and integrates, who researches,
implements, and reviews, and how each role gets the phase handoff above. Name
roles rather than inventing agents the host cannot provide. For simple work a
short statement of sequential implementation and available review is enough.

For delegated work, identify independent questions/outcomes, required reading and
return evidence per role, dependency order, shared paths/contracts, integration
owner, and verification at integration. Distinguish read-only research concurrency
from implementation concurrency. Bound research by separable questions, project
permissions, host capability, and available resource/time limits; record those
limits or the sequential fallback. An agent count is not a coverage guarantee.
Implementation concurrency must satisfy Ralph's existing isolation/provider
contract and project configuration; a `[P]` marker or parallel research does not
authorize concurrent writes. Disclose reviewer independence or its actual gap.

Present this cooperation plan with the existing design gate and include it in
that plan's snapshot. Tasks/Analyze carry its dependencies and verification work
through the existing queue. Routine assignments within the approved boundaries
need no new gate; changing allowed writes, shared ownership, integration method,
or review independence requires the affected owner/approval to be revisited.

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
