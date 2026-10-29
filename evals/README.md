# Behavioral evaluations

`evals.json` contains delivery scenarios and expected behavior, not a test runner
or a claim that every scenario has been executed end to end. Cases 21–23 probe
Review's defect analysis, finding reconciliation, and stale task closure. Cases
24–27 probe slice planning, stacked versus integration selection, failed prefix
checks, and linear-history merge-policy conflicts.

## Review fixtures

`fixtures/review/` is deliberately broken synthetic input. The proposed `after/`
change drops a custom-provider capability, adds forbidden UI name inference, and
contains an ineffective `assert True` test. These are review targets, not product
code or examples to adopt. Its requirements apply only to the fixture.

Compare baseline and updated prompts in separate fresh contexts against the same
input. Save actual outputs, grade every assertion with quoted evidence, and keep
missing runtime/Git facts explicit. Do not change the fixture to make a review pass.
An assistant's next-response decision does not prove that a complete workflow,
repair/resume cycle, provider integration, or Git closure was executed correctly.

## Current comparison and limits

The October 2026 Review update used three cases, one baseline and one updated run
per case. Both configurations satisfied 14/14 assertions and identified all three
planted defects. The updated output made the six dimensions and snapshot/finding
contract explicit; **no defect-detection uplift is demonstrated** by these samples.

Prompts expose the risk conditions, and agents read metadata with assertions
while instructed not to tailor responses. Grading was evidence-based but inline,
not blinded. Timing/token telemetry was unavailable and was not inferred from
output length. Raw outputs, grading, and the generated comparison page are local
evaluation artifacts, not shipped extensions or release readiness evidence.

Stronger follow-up evaluation should use less-leading cases and isolated real
repositories: execute repair → re-review → resume, preserve unresolved IDs and
attempt counts, introduce late ADR/worktree mutations, and verify actual task
state/commit ownership. Structural regression tests and clean OpenCode/Codex
Bundle installations complement these probes; they do not establish semantic
correctness across all hosts.
