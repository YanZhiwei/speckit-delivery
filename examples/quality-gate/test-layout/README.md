# Test layout checker example

Copy `check-test-layout.mjs` into the target repository's `scripts/` directory,
then adapt its root prefixes and permitted exceptions. It deliberately checks
only a narrow, explicit convention: TypeScript or JavaScript test files must
not be created below `src/`.

Wire it into a package script, CI, and the Quality Profile:

```json
{ "check:test-layout": "node scripts/check-test-layout.mjs" }
```

```yaml
standards:
  - id: test-layout
    owner: quality
    mechanism: "pnpm check:test-layout"
profiles:
  - id: frontend
    commands:
      test: "pnpm check:test-layout && pnpm test:frontend"
```

Keep exceptions in the repository's `testing-policy.md`; do not loosen the
regex globally because of one legacy module. Use a staged-file invocation for
fast feedback and a no-argument invocation in CI for the full tracked tree.
