# Provenance: fireworks-tech-graph

Vendored, unmodified copy of the upstream agent skill used by the optional
`fireworks` renderer of `speckit.diagram.render`.

| Field | Value |
| --- | --- |
| Upstream | https://github.com/yizhiyanhua-ai/fireworks-tech-graph |
| Tag | `v1.2.0` |
| Commit | `ea534c2d2817d43e4c02fe0ea9f67dfced6dece3` |
| Asset | https://github.com/yizhiyanhua-ai/fireworks-tech-graph/releases/download/v1.2.0/fireworks-tech-graph-v1.2.0.zip |
| Asset SHA-256 | `01edddef492988b7144439540bc0f6cd1f8baaa8ed2493c1e0cd35fa35668ef0` |
| Vendored on | 2026-10-28 |
| License | MIT (see `LICENSE`) |

## What was extracted

The release archive was extracted in full with its top-level
`fireworks-tech-graph/` directory stripped. All 122 files are byte-identical to
the release asset.

## Runtime and behavior

- Python 3 with the packages listed in the upstream `scripts/` directory.
- Produces SVG and PNG, which is the format the PR body can render inline.
- It is invoked only through `speckit.diagram.render`; nothing runs at
  installation time.

## Update policy

Copy the new release asset, recompute the SHA-256, re-extract, and update this
file in the same commit. Do not edit upstream files in place; local changes
would be lost on the next refresh and cannot be attributed to the upstream tag.
