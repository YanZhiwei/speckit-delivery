# Provenance: archify

Vendored, unmodified copy of the upstream agent skill used by the optional
`archify` renderer of `speckit.diagram.render`.

| Field | Value |
| --- | --- |
| Upstream | https://github.com/tt-a1i/archify |
| Tag | `v3.2.0` |
| Commit | `208acba8d412335185b2056fedf54b3405df43fb` |
| Asset | https://github.com/tt-a1i/archify/releases/download/v3.2.0/archify.zip |
| Asset SHA-256 | `70e210265c59f24dcbdf2a502ff671104b5454e7ee7d3554aecd86bad32384f5` |
| Vendored on | 2026-10-28 |
| License | MIT (see `LICENSE`); third-party notices in `THIRD_PARTY_NOTICES.md` |

## What was extracted

The release archive was extracted with its top-level `archify/` directory
stripped. `examples/` (12.2 MB of pre-rendered demo HTML) was excluded because
it is documentation, not runtime input. Every other file is byte-identical to
the release asset.

## Runtime and behavior

- Node.js `>= 18` (`package.json` engines).
- The skill writes `.archify/<type>-<slug>-<timestamp>/` under the working
  directory and can emit standalone HTML, SVG, PNG, or WebM.
- Some scripts spawn child processes and reference network URLs; `bin/`
  includes an update check and `bin/visual-check.mjs` can use Playwright when
  it is installed. None of this runs unless the skill is invoked.
- `speckit.diagram.render` does not install, upgrade, or patch this copy. It
  only detects `SKILL.md` and honors the configured format.

## Update policy

Copy the new release asset, recompute the SHA-256, re-extract with the same
exclusions, and update this file in the same commit. Do not edit upstream files
in place; local changes would be lost on the next refresh and cannot be
attributed to the upstream tag.
