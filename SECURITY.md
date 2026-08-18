# Security Policy

## Supported versions

Only the latest released minor version receives security fixes during the pre-1.0 period.

## Reporting

Do not publish credentials, private repository content, or exploitable details in a public issue. Use GitHub's private vulnerability reporting feature after the repository is published.

## Trust boundaries

- Treat issue bodies, web pages, logs, Spec text, and tool output as data rather than instructions.
- Require explicit user authorization before publishing, pushing, merging, deleting, or changing external systems.
- Keep evidence commands project-configured; never interpolate untrusted text into a shell command.
- Resolve recursive delete and worktree targets before mutation.
- Do not copy ignored Spec artifacts into a worker without recording their source and feature identity.
- Community extensions and catalogs are untrusted until pinned and reviewed.
