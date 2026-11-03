---
description: "Synchronize authoritative documentation sources, manifests, inbound links, and generated projections"
---

# Documentation Sync

Read documentation configuration. When disabled or absent, or when the caller
explicitly passes `with_docs_sync=false`, report `not configured` and make no
changes. When called inside an already reserved Review Fix attempt (`repair=1` plus its
`attempt=<n>`), restrict work to surfaces affected by that repair/attempt; never
use the repair to perform unrelated documentation sync. Record the run/lane/scope,
attempt, and actual checked inputs so a later repair can reuse only an exact-content
result. Identify documentation impact from the final diff and update the authoritative source. Never edit a generated projection as the source of truth.

When documents move or publication status changes, update the source, publication manifest, and inbound links atomically. Run the configured synchronization command, then the verification command. Distinguish authored changes from generator output in the report.

The command is complete when sources, manifest, links, and generated projection agree, or when it reports a concrete configuration/tool blocker. Report `DOCS_SYNC: synced | unchanged | not-configured | blocked` with `INPUT_IDENTITY`, the run/lane/scope, actual source and generated paths, commands/results, and any reused exact-content identity. Documentation publication or remote mutation needs separate authorization.
