# Design analysis profile

Owner: Core Plan and Delivery's existing Plan checkpoint. Use the shared method
adapter contract; this profile does not write or approve the plan or an ADR.

Read the clarified requirements, approved exploration, active decisions, relevant
code and tests, and the supplied architecture constraints. Reuse established facts;
research only a named gap through the owner's normal exploration permissions.

1. Separate binding project rules, accepted requirements, recommendations, and
   unknowns. Do not import a skill example's stack, numeric SLO, vocabulary, or
   Accepted ADR status as project policy.
2. Compare viable interfaces and state/dependency ownership, including reuse or
   extension of current code. A small understood change needs only a short
   comparison; one viable approach is acceptable with an evidenced reason.
3. Consider applicable compatibility, failure/degradation, operational cost, and
   non-functional requirements. Avoid infrastructure or abstractions for
   hypothetical scale. State which claims still need evidence.
4. Return candidate design responses by constraint ID, precise affected paths,
   interface responsibilities, verification owner/mechanism, and open decisions.
   Planned tests are not executed evidence; unsupported automation stays explicit.

Return the comparison, recommendation, alternatives rejected with reasons,
constraint-response/verification mapping, and decision-critical gaps. Core Plan
incorporates the result in its actual `plan.md`, retains the existing design gate,
and passes durable choices through Proposed ADRs. No parallel plan or task queue.

Method provenance: the profile's requirements/trade-off/failure review and
interface-alternative comparison were informed by the architecture-design source
pinned in `REFERENCE-REVIEW.md`; unaffected sources are not implicitly adopted.
External resources apply only when explicitly selected and verified under the
shared contract.
