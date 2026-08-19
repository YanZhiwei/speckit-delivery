# Contributing

## Development setup

1. Install Spec Kit CLI `>=0.16.4`.
2. Fork and clone the repository.
3. Create a focused branch.
4. Install changed extensions and workflows into a clean temporary Spec Kit project with their `--dev` options.
5. Run the validation commands documented in `DISTRIBUTION.md`.

## Change rules

- Keep each extension focused on one capability.
- Keep command instructions executable and end each phase with a checkable completion condition.
- Put shared definitions in `docs/` or an extension's `references/`; do not duplicate policy across commands.
- Update manifests, catalogs, changelog, and behavioral evals together when public behavior changes.
- Treat workflow state and ignored Spec artifacts as untrusted until their existence is verified.
- Never claim provider support without clean-project installation evidence.

## Pull requests

Use `.github/pull_request_template.md`. Explain the user-visible contract, compatibility impact, evidence, and any architecture decision changes.
