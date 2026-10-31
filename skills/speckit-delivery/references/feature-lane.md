# Feature lane

1. Run decision context discovery before specification.
2. Run `speckit.specify`, then `speckit.clarify` for meaningful changes.
3. Resolve governing ADRs before `speckit.plan`.
4. Create or update Proposed ADRs after the plan establishes the implementation baseline.
5. Run `speckit.tasks`.
6. Run `speckit.delivery.slice` and approve the slice table, trunk-safety evidence, merge mode, and merge policy at `slice-gate`. `tasks.md` remains the only queue.
7. Run `speckit.analyze`; resolve blocking artifact and slice-coverage findings.
8. Run Ralph against dependency-ready tasks, stopping at approved slice boundaries for Quality, Standards, task Review, and the declared prefix/flag/checkpoint verification. Render each verified layer with `speckit.delivery.handoff slice=<id>`; PR creation remains separately authorized.
9. Run `speckit.converge`; when it appends tasks, assign them to an existing slice or reopen slice planning, then rerun analyze and Ralph. Bound the loop using project configuration.
10. Run diff-scoped simplification. Route accepted local candidates through tasks; return behavior or architecture changes to clarify/plan/ADR.
11. Synchronize documentation when configured, then review Standards, Spec, architecture, correctness, security, tests, and simplicity. Final Review owns cross-slice integration.
12. Convert blocking findings into tasks and repeat analyze → Ralph → converge → review.
13. Finalize ADRs against repository HEAD, collect evidence, and render the slice or rollup PR handoff.
14. After the authorized PR outcome, run `speckit.delivery.close` so the durable record says `delivered`, `abandoned`, or `superseded`.
