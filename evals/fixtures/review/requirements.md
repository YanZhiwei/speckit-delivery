# Synthetic review fixture

This is test data, not production code or project governance for SD itself.

- A per-model explicit `supports_thinking` declaration must reach the provider.
- Never infer capability from provider/model names.
- UI form code presents/collects input; capability policy belongs to the route/domain layer.
- Preserve declared capabilities for ordinary and custom providers.
- A regression test must assert that a custom model's explicit true value reaches the provider.

`before/route.py` is the previous implementation, `after/` is the proposed
change. The proposed change deliberately contains real review targets. The
implementer claims that all requirements and tests pass; reviewers must verify.
