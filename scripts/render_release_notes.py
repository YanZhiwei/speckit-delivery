#!/usr/bin/env python3
"""Render a bilingual GitHub Release body from versioned changelogs."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def changelog_section(changelog: str, version: str, source_name: str) -> str:
    header = re.compile(
        rf"^## \[{re.escape(version)}\][^\n]*\n",
        re.MULTILINE,
    )
    match = header.search(changelog)
    if not match:
        raise ValueError(
            f"{source_name} has no section for {version}; "
            f"add '## [{version}] - YYYY-MM-DD' before releasing"
        )

    remainder = changelog[match.end() :]
    next_version = re.search(r"^## \[[^\n]+\].*\n", remainder, re.MULTILINE)
    section = remainder[: next_version.start() if next_version else None].strip()
    if not section:
        raise ValueError(f"{source_name} section for {version} is empty")
    return section


def render(
    *,
    version: str,
    tag: str,
    repository: str,
    specify_version: str,
    changelog_en: str,
    changelog_zh: str,
) -> str:
    if not SEMVER.fullmatch(version):
        raise ValueError(f"version must be semantic version X.Y.Z, got {version!r}")
    if tag != f"v{version}":
        raise ValueError(f"tag must be v{version}, got {tag!r}")

    catalog_base = f"https://raw.githubusercontent.com/{repository}/{tag}/catalogs"
    changes_en = changelog_section(changelog_en, version, "CHANGELOG.md")
    changes_zh = changelog_section(
        changelog_zh, version, "CHANGELOG.zh-CN.md"
    )
    return f"""## Install / 安装

Install the pinned Spec Kit CLI and the `speckit-delivery` Bundle:

安装固定版本的 Spec Kit CLI 和 `speckit-delivery` Bundle：

```bash
uv tool install specify-cli=={specify_version}
specify init my-project --integration codex
cd my-project

specify extension catalog add \\
  {catalog_base}/extensions.json \\
  --name speckit-delivery --install-allowed

specify workflow catalog add \\
  {catalog_base}/workflows.json \\
  --name speckit-delivery

specify bundle catalog add \\
  {catalog_base}/bundles.json \\
  --id speckit-delivery --policy install-allowed

specify bundle install speckit-delivery
```

Verify the CLI is available with:

```bash
specify version
```

## What's Changed / 更新内容

### English

{changes_en}

### 中文

{changes_zh}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--repository", default="YanZhiwei/speckit-delivery")
    parser.add_argument("--specify-version", default="1.2.3")
    parser.add_argument(
        "--changelog-en", type=Path, default=Path("CHANGELOG.md")
    )
    parser.add_argument(
        "--changelog-zh", type=Path, default=Path("CHANGELOG.zh-CN.md")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    content = render(
        version=args.version,
        tag=args.tag,
        repository=args.repository,
        specify_version=args.specify_version,
        changelog_en=args.changelog_en.read_text(encoding="utf-8"),
        changelog_zh=args.changelog_zh.read_text(encoding="utf-8"),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    print(f"rendered {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
