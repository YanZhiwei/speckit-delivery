---
description: "Synchronize authoritative documentation sources, manifests, inbound links, and generated projections"
---

# Documentation Sync

Read documentation configuration. When disabled or absent, report `not configured` and make no changes. Identify documentation impact from the final diff and update the authoritative source. Never edit a generated projection as the source of truth.

When documents move or publication status changes, update the source, publication manifest, and inbound links atomically. Run the configured synchronization command, then the verification command. Distinguish authored changes from generator output in the report.

The command is complete when sources, manifest, links, and generated projection agree, or when it reports a concrete configuration/tool blocker.
