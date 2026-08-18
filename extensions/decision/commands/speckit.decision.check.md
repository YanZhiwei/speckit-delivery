---
description: "Validate architecture decision links, lifecycle, citations, and implementation consistency"
---

# Check Decision Memory

Read configured ADR roots and the final implementation. Report blocking failures for broken decision links, missing superseded targets, multiple accepted owners of the same incompatible decision, accepted records contradicted by current code, and citations to ephemeral Spec artifacts or review/session chronology.

Distinguish an implementation defect from stale documentation. Do not silently rewrite accepted history. Recommend a new superseding ADR when a later decision replaced an accepted one.

Return `pass` only when all active decision relationships resolve and the records describe repository HEAD. Otherwise return structured findings with severity, record, evidence, impact, and remediation.
