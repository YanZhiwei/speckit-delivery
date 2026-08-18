# Feature lane

1. Run decision context discovery before specification.
2. Run `speckit.specify`, then `speckit.clarify` for meaningful changes.
3. Resolve governing ADRs before `speckit.plan`.
4. Create or update Proposed ADRs after the plan establishes the implementation baseline.
5. Run `speckit.tasks` and `speckit.analyze`; resolve blocking artifact findings.
6. Run Ralph against dependency-ready tasks.
7. Run `speckit.converge`; when it appends tasks, rerun analyze and Ralph. Bound the loop using project configuration.
8. Run diff-scoped simplification. Route accepted local candidates through tasks; return behavior or architecture changes to clarify/plan/ADR.
9. Synchronize documentation when configured, then review Standards, Spec, architecture, correctness, security, tests, and simplicity.
10. Convert blocking findings into tasks and repeat analyze → Ralph → converge → review.
11. Finalize ADRs against repository HEAD, collect evidence, and render the PR handoff.
