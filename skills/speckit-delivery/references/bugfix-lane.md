# Bugfix lane

1. Assess the report and reproduce the symptom.
2. Retrieve decisions and project rules governing the affected code.
3. Establish a failing regression test or equivalent red evidence.
4. Diagnose the root cause before editing the fix.
5. Apply the smallest coherent fix and establish green evidence.
6. Run diff-scoped simplification, review, decision consistency, and evidence selection.
7. Create or supersede an ADR only when the architectural decision changes.
8. Escalate to Feature when the fix changes public contracts, durable formats, ownership boundaries, security policy, or multiple modules.
