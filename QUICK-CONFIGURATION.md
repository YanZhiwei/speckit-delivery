# Quick SD Configuration

This guide connects an existing project to Spec Kit Delivery (SD). It supports
mixed-language and multi-module projects without assuming a repository layout
or package manager.

The rule is simple: every standard needs **pre-edit guidance, post-edit
verification, and task-closure blocking**. `.specify/` may be Git-ignored;
ADRs, native tool configuration, and CI remain tracked by the project.

## 0. Establish project facts

Do not make SD infer these facts:

| Project fact              | Example                                                          | Where it belongs                  |
| ------------------------- | ---------------------------------------------------------------- | --------------------------------- |
| Code families             | `frontend/**/*.ts(x)`, `backend/**/*.py`                         | Quality Profile `match`           |
| Native commands           | `pnpm lint:ci`, `pnpm typecheck`, `uv … ruff check`              | Quality Profile `commands`        |
| Architecture rules        | Routers do not contain business rules; dependencies point inward | Architecture docs / ADRs          |
| Complexity rule           | Python C901 ≤ 10                                                 | Ruff config, never Markdown alone |
| Comment rule              | Explain non-obvious intent, not implementation history           | Style docs + Standards Review     |
| Durable decision location | `docs/architecture/adr/`                                         | Delivery / Decision config        |

If a rule has no executable mechanism, record a gap; never configure it as a
pass. Ruff's `max-complexity = 10`, for example, is inert unless `C90` is also
enabled.

## 0.1 Recommended governance layout

SD does not impose a directory layout. Keep durable, human-and-agent-readable
rules in `docs/engineering/` and `docs/architecture/`; keep executable rules
in native language tools.

```text
AGENT_GUIDE.md                         # entry point, module map, daily quality commands
docs/
├── engineering/
│   ├── quality.md                      # quality commands and CI / Hook responsibilities
│   ├── code-style.md                   # cross-language: DRY, comments, responsibilities
│   ├── code-style-typescript.md        # TypeScript / React conventions
│   └── code-style-python.md            # Python / FastAPI conventions
└── architecture/
    ├── boundaries.md                   # ownership, layers, dependency direction
    ├── testing-policy.md               # test directories, naming, and exceptions
    └── adr/                            # accepted and Proposed decisions

eslint.config.* / tsconfig*.json        # executable TypeScript rules
pyproject.toml / ruff.toml              # executable Python rules
.husky/ or .pre-commit-config.yaml      # fast local feedback
.github/workflows/                      # reproducible CI gates
```

| Rule                                            | Put it in                                   | Why                                                       |
| ----------------------------------------------- | ------------------------------------------- | --------------------------------------------------------- |
| Format, lint, types, tests, complexity          | Native configuration and CI                 | Machines must run and fail it                             |
| Quality commands and Hook/CI ownership          | `docs/engineering/quality.md`               | Humans and SD need the evidence level                     |
| DRY, responsibilities, comment intent           | `docs/engineering/code-style.md`            | Cross-language semantic rules                             |
| Framework conventions                           | `docs/engineering/code-style-<language>.md` | Keeps language rules separate                             |
| Ownership, layers, dependency direction         | `docs/architecture/boundaries.md`           | System structure, not formatting                          |
| Test directories, naming, exceptions, migration | `docs/architecture/testing-policy.md`       | State the contract, then enforce it with a narrow checker |
| Trade-offs and historical context               | `docs/architecture/adr/`                    | Later Spec / ADR retrieval and citation                   |

Keep `AGENT_GUIDE.md` short and link it to these authoritative documents. Do
not leave mechanical rules only in Markdown: enable them in native tools too.

## 1. Install extensions and workflows

Run this in the target repository root. Replace `$delivery` with the local path
to this repository; use a catalog or zip installation after publishing.

```powershell
$delivery = 'D:\Repos\Github\speckit-delivery'

specify extension add --dev "$delivery\extensions\decision"
specify extension add --dev "$delivery\extensions\ralph"
specify extension add --dev "$delivery\extensions\review"
specify extension add --dev "$delivery\extensions\simplify"
specify extension add --dev "$delivery\extensions\evidence"
specify extension add --dev "$delivery\extensions\quality"
specify extension add --dev "$delivery\extensions\docs-sync"
specify extension add --dev "$delivery\extensions\delivery"

specify workflow add --dev "$delivery\workflows\feature-delivery\workflow.yml"
specify workflow add --dev "$delivery\workflows\bugfix-delivery\workflow.yml"
specify workflow add --dev "$delivery\workflows\lightweight-delivery\workflow.yml"
```

When upgrading, add `--force` for changed extensions. Verify with `specify
extension list` and `specify workflow list`; at minimum, see `quality` (2
commands), `delivery` (5), and `review` (2).

## 2. Initialize project governance

Run `speckit.delivery.init`, then review manually:

- The ADR path is actually tracked in the project.
- `docs-sync` is `enabled: true` and uses only authoritative sources.
- Decide whether `.specify/` is local ephemeral state or tracked. Either is
  valid, but an ADR must never depend on an ignored Spec.
- The root governance document names branches, module boundaries, code style,
  and quality commands.

A common model ignores `.specify/` but tracks `docs/architecture/adr/`:
Spec/Plan/Tasks remain personal working state; Accepted ADRs remain durable
decisions retrievable by later SD work.

## 3. Configure Quality Profiles

Create `.specify/extensions/quality/quality-config.yml`:

```yaml
schema_version: "1.0"
policy_sources:
  architecture:
    [
      AGENT_GUIDE.md,
      docs/architecture/boundaries.md,
      docs/architecture/testing-policy.md,
      docs/architecture/adr,
    ]
  style:
    - docs/engineering/code-style.md
    - docs/engineering/code-style-typescript.md
    - docs/engineering/code-style-python.md

standards:
  - id: typescript-native-checks
    owner: quality
    mechanism: "pnpm lint:ci, pnpm typecheck, pnpm test:frontend"
  - id: dry-and-module-ownership
    owner: review
    mechanism: "speckit.review.standards against architecture policy"
  - id: test-layout
    owner: quality
    mechanism: "pnpm check:test-layout"
  - id: simplification
    owner: simplify
    mechanism: "speckit.simplify.scan before final review"
  - id: architecture-decisions
    owner: adr
    mechanism: "speckit.decision.propose and speckit.decision.finalize"

profiles:
  - id: frontend-typescript
    match: ["frontend/**/*.{ts,tsx,js,jsx}", "gateway/**/*.{ts,tsx}"]
    discovery_files: [package.json, pnpm-workspace.yaml]
    commands:
      format: "pnpm format:check"
      lint: "pnpm lint:ci"
      typecheck: "pnpm typecheck"
      test: "pnpm check:test-layout && pnpm test:frontend"
    rules:
      complexity_max: 10
      comment_policy: "Explain non-obvious intent; do not use history comments as a design record."
  - id: project-automation
    match: ["scripts/**/*.{ts,js,mjs,cjs}", ".github/workflows/**/*.{yml,yaml}"]
    discovery_files: [package.json]
    commands:
      format: "pnpm format:check"
      test: "pnpm test:scripts"

unprofiled_changed_paths: block
# Throwaway prototypes are outside product SD gates; reported, never passed.
excluded_paths: ["poc/**"]
reuse_passing_hooks: true
```

`policy_sources` are read by Quality Brief and Standards Review;
`profiles.match` maps files to real commands; `standards` maps DRY, boundaries,
comments, and ADRs to Review, Simplify, or the ADR lifecycle. Also keep the
following project-local files consistent:

```yaml
# .specify/extensions/decision/decision-config.yml
adr_directories: [docs/architecture/adr]
context_files: [AGENT_GUIDE.md, docs/architecture/boundaries.md]

# .specify/extensions/delivery/delivery-config.yml
context_files: [AGENT_GUIDE.md, docs/engineering/quality.md]
adr_directories: [docs/architecture/adr]
docs_sync: auto
```

Each Profile covers one code family with commands that genuinely run. Add
separate Profiles for Python, Go, Java, and so on. Leave an unready family
unprofiled: `unprofiled_changed_paths: block` prevents incorrect closure.

## 4. Make rules executable

SD runs project-owned tools by changed scope; it does not implement language
tools itself.

| Rule                         | Native mechanism                                                      | SD responsibility                              |
| ---------------------------- | --------------------------------------------------------------------- | ---------------------------------------------- |
| Format, lint, types, tests   | Prettier / ESLint / TypeScript / Pytest                               | Run after editing; block failures              |
| Python complexity ≤ 10       | Ruff `select` includes `C90` + `max-complexity = 10`                  | Run Ruff and report the real result            |
| Comment intent               | Project policy; optional custom checker                               | Brief before editing; Standards Review decides |
| DRY and directory boundaries | Architecture policy; dependency checker if available                  | Simplify / Standards Review block              |
| Test-directory layout        | A project-owned `check:test-layout` command limited to explicit paths | Brief before editing; failure blocks the task  |
| Architecture decisions       | ADR                                                                   | Proposed → reviewed HEAD → Accepted            |

Do not use a comment checker to decide DRY or object-oriented design. Those
need semantic review of the diff, callers, and architectural constraints.
Conversely, do not rely only on review to find type errors or complexity issues.

## 5. Configure Hooks: fast feedback, not closure gates

Hooks provide early feedback. Ralph's Quality + Standards verdicts remain the
task-closure condition.

### Node / Husky example

```json
{
  "scripts": {
    "precommit:quality": "lint-staged",
    "prepush:quality": "pnpm lint:ci && pnpm typecheck && pnpm test"
  },
  "lint-staged": {
    "*.{ts,tsx,js,jsx}": ["eslint --fix", "prettier --write"]
  }
}
```

Keep `pre-commit` fast and changed-scope only. `pre-push` may run repository
type checks and tests. Commands must match or be stricter than their Quality
Profile. If a Hook is bypassed, Quality Check still runs or verifies a receipt
for the exact current HEAD.

### Python / pre-commit example

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.12.0 # pin a project-approved version
    hooks:
      - id: ruff-check
        args: [--select, "E,F,I,C90"]
      - id: ruff-format
```

```toml
# pyproject.toml
[tool.ruff.lint]
select = ["E", "F", "I", "C90"]

[tool.ruff.lint.mccabe]
max-complexity = 10
```

Another Hook manager is fine. Hooks must not be the only gate or contradict CI
and Quality Profile commands.

## 6. First acceptance and daily usage

Validate one real small change in this order:

```text
1. specify extension list / specify workflow list
2. speckit.delivery.doctor
3. speckit.quality.brief for a small real change
4. Run every command in its Profile
5. speckit.quality.check + speckit.review.standards
6. Confirm Ralph closes a Task only after both verdicts pass
```

Start daily work with `$sd <request>` or `/sd <request>`. Feature work passes
through Doctor, Spec, ADR, Tasks, and Ralph; Bugfix and Lightweight work take a
proportional lane. Run Ralph directly only after `speckit.analyze` has passed
the active `tasks.md`.

## 7. New-project checklist

- [ ] Every code language has a Profile or is explicitly blocked.
- [ ] Every Profile command runs from the repository root.
- [ ] Complexity rules are enabled in native tooling.
- [ ] DRY, boundaries, comments, and ADRs declare an owner and mechanism in
      `standards`.
- [ ] Hooks provide fast feedback; CI and Quality Check provide reproducible
      closure evidence.
- [ ] Docs Sync is enabled and its authoritative sources are explicit.
- [ ] The ignored/tracked `.specify/` policy is decided; ADRs do not rely on
      ignored files.
- [ ] `speckit.delivery.doctor` returns `pass` before the first Feature.

See also: [中文](快速配置.md), [Quality Gate](QUALITY-GATE.md),
[Architecture](ARCHITECTURE.md), [Lifecycle](LIFECYCLE.md), and
[Distribution](DISTRIBUTION.md).
