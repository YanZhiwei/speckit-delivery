# Quality Gate examples

Each subdirectory is a **configuration fragment**, not a runnable starter
application. It demonstrates the association between:

1. a language's native style/static-analysis configuration;
2. a `quality-profile.yml` fragment for
   `.specify/extensions/quality/quality-config.yml`; and
3. the changed-path scope that causes the profile to run.

| Example | Native configuration to merge into the target project | Profile source scope |
| --- | --- | --- |
| [Python](python/) | `pyproject.toml` | `src/**/*.py`, `tests/**/*.py` |
| [TypeScript](typescript/) | `eslint.config.mjs`, `tsconfig.json` | `apps/web/**/*.{ts,tsx}` |
| [Go](go/) | `.golangci.yml` and a repository format-check script | `services/api/**/*.go` |
| [Java](java/) | Maven plugin configuration in `pom.xml` | `services/orders/**/*.java` |
| [.NET](dotnet/) | `.editorconfig`, `Directory.Build.props` | `src/**/*.cs`, `tests/**/*.cs` |

## Apply one example

Assume the target repository has Python code under `backend/` and uses `uv`.

1. Merge [python/pyproject.toml](python/pyproject.toml) into the repository's
   real `pyproject.toml`. Do not overwrite existing dependencies, tool
   versions, excludes, or per-file exceptions.
2. Copy the profile from [python/quality-profile.yml](python/quality-profile.yml)
   into `profiles:` in
   `.specify/extensions/quality/quality-config.yml`.
3. Change `match`, runner (`uv run`), source directory, and test selection to
   the repository's actual layout. The profile must select the exact native
   configuration file from step 1 through its `discovery_files`.
4. Add the real style and architecture documents under `policy_sources`; these
   are read as policy, not copied into the profile.
5. Run each profile command from repository root once. Only then is it a gate:

   ```text
   speckit.quality.check scope=outgoing-diff
   ```

The relationship is deliberately one-directional: **native config defines the
rule; Quality Profile decides when and how that native config is executed.**
Do not duplicate `complexity_max` in the profile without enabling its native
tool rule. `rules` is audit metadata, not an enforcement engine.

## Compose a monorepo

Keep one `quality-config.yml`, but add a separate profile for each independent
build root or runtime. A change can match multiple profiles; every matched
profile must pass.

```yaml
policy_sources:
  architecture: [Docs/architecture/repo-structure.md]
  style: [Docs/architecture/code-style.md]

profiles:
  # Paste and adapt one or more quality-profile.yml fragments here.

unprofiled_changed_paths: block
reuse_passing_hooks: true
```

Never point a profile at an example file in this distribution repository. All
`discovery_files` and commands must refer to files in the target project.
