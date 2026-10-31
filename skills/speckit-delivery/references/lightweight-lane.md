# Lightweight lane

1. Fix the exact base/head scope.
2. Confirm the change is mechanical or behavior-preserving.
3. Implement the narrow change.
4. Run the smallest credible verification selected from the diff.
5. Perform a lightweight review, judge package README drift, and produce handoff evidence.
6. After the authorized PR outcome, run `speckit.delivery.close` so the durable record says `delivered`, `abandoned`, or `superseded`.

Escalate when behavior, architecture, compatibility, or acceptance is unclear.
