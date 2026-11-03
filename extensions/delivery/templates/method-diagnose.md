# Diagnosis and test-design profile

Owner: official Bug Assess/Fix/Test (or the explicitly supplied task worker).
Use the shared method adapter contract. This profile returns investigation and
regression guidance; it does not write official reports, repair code, or run a
second Bug workflow.

Ownership note: this adapter may support the diagnosis/time-boxed reproduction
that informs an official Bug assessment without writing it. It must not be used
as the Bugfix-Feature workflow's required assessment path; official
`speckit.bug.assess` remains mandatory there.

1. State the observed symptom, expected behavior, environment/configuration,
   available reproduction, and missing evidence. A plausible explanation without
   reproduction or trace evidence remains a hypothesis.
2. Trace the relevant request/data path across component boundaries. Compare a
   working path or prior revision; inspect implicated changes, callers, and tests.
   Reuse exploration evidence instead of mapping the whole repository again.
3. Form one falsifiable hypothesis at a time and propose the narrowest experiment
   that distinguishes it from alternatives. Have the owner perform any permitted
   reproduction/test execution and supply actual outputs; do not fabricate them.
4. Explain the smallest cause-level correction inside approved scope. New durable
   contracts or material architecture changes return to lane/scope/ADR decisions.
5. Propose a behavioral regression at a meaningful interface: fixture/input,
   independently derived expected result, the real defect it catches, and the
   expected RED-to-GREEN observation. Avoid source-text assertions and tests that
   merely repeat the implementation. Test-first scope and commands follow project
   policy, not a provider's universal ritual or full-suite requirement.

Return evidence versus hypotheses, causal path, proposed experiments, bounded
repair options, regression design, and unresolved blockers. Before assessment,
the official Bug assessor alone confirms diagnosis/red evidence; for an approved
task the worker/owner executes the proposed tests and records results.
Never present an adapter proposal as executed proof. Missing evidence does not
authorize a fix, another approval, commit, or budget.

Method provenance: Superpowers systematic-debugging/writing-good-tests and Matt
Pocock tdd informed this profile. Use pinned external resources only through the
shared selection contract; do not inherit their separate execution/commit loops.
