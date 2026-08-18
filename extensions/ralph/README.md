# Ralph

Ralph consumes Spec Kit `tasks.md`, not an independent ticket format. It uses native agent delegation when available and dependency-ordered sequential execution otherwise.

Workers never mark their own tasks complete. The orchestrator verifies changed paths, acceptance evidence, commands, results, and dependency impact before changing `[ ]` to `[X]`.
