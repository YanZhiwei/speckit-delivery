# Feature lane

1. Run decision context discovery before specification.
2. Run `speckit.specify`, then `speckit.clarify` for meaningful changes.
3. Resolve governing ADRs before `speckit.plan`. Follow Delivery's shared Plan checkpoint: keep sourced architecture constraints, design responses, verification owners/mechanisms, and gaps in the actual plan; optional skill methods remain recommendations under project governance. `method_adapters.design` defaults to builtin; an explicit external method needs verified local resources and returns analysis only to the existing plan/gate.
4. Create or update Proposed ADRs after the plan establishes the implementation baseline. Review constraints with the design at the existing plan gate.
5. Run `speckit.tasks`, retaining applicable constraint IDs and verification work for Analyze, Brief, and Review.
6. Run `speckit.delivery.slice`, then `speckit.analyze`; resolve blocking artifact and slice-coverage findings. Only then approve the slice table, trunk-safety evidence, resolved execution/publication modes, publication-group map, and merge policy at `slice-gate`, and record the actual choice/snapshot through Delivery's `action=record-approval` writer. `tasks.md` remains the only queue; slice approval does not authorize remote publication.
7. Run Ralph against dependency-ready tasks, stopping at approved internal slice boundaries for Quality, Standards, task Review, declared prefix/flag/checkpoint verification, and applicable risk probes. Render each boundary or approved publication layer with `speckit.delivery.handoff slice=<id>`; `Publication mode: single` still produces one final PR body, and PR creation remains separately authorized.
8. Run `speckit.converge`; when it appends tasks, assign them to the current approved slice fingerprint or reopen slice approval, then rerun analyze and Ralph. Bound the loop using project configuration.
9. Run diff-scoped simplification. Route accepted local candidates through tasks; return behavior or architecture changes to clarify/plan/ADR.
10. Synchronize documentation when configured and judge package README drift before final Quality/Standards. Then review Standards, Spec, architecture, correctness, security, tests, and simplicity. Final Review owns cross-slice integration.
11. Convert blocking findings into tasks and repeat analyze → Ralph → converge → review.
12. Finalize ADRs against repository HEAD, collect evidence, and render the slice or rollup PR handoff.
13. After the authorized PR outcome, run `speckit.delivery.close` so the durable record says `delivered`, `abandoned`, or `superseded`.
