# Diff-Driven Evidence

Selects verification from the actual outgoing diff instead of imposing one universal local test suite. CI remains responsible for the exhaustive platform matrix.

`speckit.evidence.collect` is independently installable and owns the durable,
same-run evidence summary. Direct workflows pass `lane`, `delivery_run`, the
exact project-relative `.specify/delivery/<run>/evidence.md` path, and the
Feature/Bugfix exploration path when that packet exists. The command validates
those identities before writing; it never chooses a newest file or relocates a
record when a Feature or Bug identity becomes known.

Feature evidence may consume its approved exploration and Spec/Plan inputs.
Bugfix evidence consumes the explicit assessment and original fix/test reports;
Lightweight consumes its bounded request and does not require Feature artifacts
or exploration. Quality owns execution receipts, Standards/Review own their
verdicts, and `speckit.delivery.close` owns the actual PR outcome. See the
[Evidence command contract](commands/speckit.evidence.collect.md) for safe-id
validation, the explicit active-Feature-only legacy fallback, fingerprint
binding, and same-run append/update rules.
