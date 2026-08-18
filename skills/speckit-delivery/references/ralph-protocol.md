# Ralph protocol

Parse task identifiers, dependencies, `[P]` markers, user-story labels, file targets, and verification instructions. Dispatch only dependency-ready work. Treat file overlap and shared public contracts as blocking edges even when tasks carry `[P]`.

Give a worker one task or one cohesive red/green/refactor bundle. Include the exact acceptance condition and relevant Spec/Plan/ADR excerpts. Workers return changed paths, commands run, results, residual risk, and commit identity when commits are part of the provider contract.

The orchestrator checks the result and marks `[X]`. A worker never marks its own task complete. Failed tasks block downstream tasks until retried, revised, or explicitly waived by an authorized human.
