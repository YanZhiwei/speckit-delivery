# Reference repository review

The initial structure was informed by four public repositories:

- [GitHub Spec Kit](https://github.com/github/spec-kit): separates extensions, workflows, presets, bundles, catalogs, examples, and publishing guides. Its README leads with the SDD value proposition, then installation, commands, extension points, and philosophy.
- [Anthropic Skills](https://github.com/anthropics/skills): keeps every skill self-contained under `skills/<name>/SKILL.md`, adding scripts, references, and assets only when the capability needs them.
- [Superpowers](https://github.com/obra/superpowers): distributes a methodology as composable skills, documents installation per harness, names the basic workflow explicitly, and tests skill behavior separately from plugin infrastructure.
- [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness/tree/master/.agents/skills): keeps repository-specific engineering skills small and evidence-driven. Its review, pre-push, documentation, and simplification skills separate scope discovery from semantic judgment.

## Adopted patterns

- One root README with a direct value proposition and copyable installation path.
- One capability per extension, composed by a bundle.
- One memorable `$sd` router facade rather than requiring humans to remember every command; the canonical `speckit-delivery` router remains the single owner of routing policy.
- Progressive disclosure from command to references and project configuration.
- Version-pinned catalogs and release artifacts.
- Clean-project installation evidence before release claims.
- Bilingual top-level entry without duplicating detailed reference documents.

## Deliberately not adopted

- Repository-specific paths, package managers, protected seams, or test commands.
- A single monolithic workflow prompt containing every capability.
- Claims that all agent integrations provide equivalent parallelism.
- Direct editing of generated documentation projections.
- Automatic repository-wide simplification during an unrelated feature.
