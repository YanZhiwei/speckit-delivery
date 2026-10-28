# 分发说明

## 发布单元

每个 Extension 打包为根目录包含 `extension.yml` 的压缩包；Workflow 是固定版本的
YAML；Bundle 在 Catalog 引用全部解析后构建。

```text
decision  ralph  review  simplify  evidence  quality  docs-sync  delivery
                         + feature / bugfix / lightweight Workflow
                         + speckit-delivery Bundle
```

Catalog URL 必须指向与发布版本相同的 Tag，发布不能依赖可变的 `main` 内容。

## 发布准备 PR

一次发布分为两个独立 Pipeline：

1. 在中英文 Changelog 中增加非空的 `## [<version>]` 段落。
2. 从 Actions 页面手动运行 **Prepare release PR**，填写目标版本和基线分支。
3. 该 Workflow 运行 `scripts/stamp_release.py`，统一更新 Extension、Workflow、Bundle
   和 Catalog 的版本、Tag 与下载 URL；随后执行分发契约测试、本地 Catalog Bundle
   安装和组件打包，推送 `release/v<version>` 并创建 PR。
4. 审查并合并 PR。准备 Workflow 不会打 Tag，也不会发布。
5. 对合并后的提交手动运行 **Release distribution**，使用同一版本。发布 Workflow
   还会执行 `stamp_release.py --version <version> --check`，未 stamp 的源码不能发布。

不要在发布后回写 `bundles.json`：已经创建的 Tag 不能安全改写，而安装器读取的是该
Tag 下的 Catalog。版本准备必须在创建 Tag 之前完成。

## 手动发布 Workflow

GitHub Actions 中的 `Release distribution` Workflow 通过 Actions 页面手动
启动。运行时填写语义化版本号和要发布的分支或 Commit。Workflow 会先构建并
校验分发产物，只有校验通过后才创建 `v<version>` Tag 并发布 GitHub Release
资产。不需要再创建第二个发布 Workflow，也不要手动上传压缩包。

选中的来源必须已经包含匹配的 Manifest、Catalog、README 命令以及中英文
Changelog。只有当已有 Tag 指向同一个来源 Commit 时才允许复用；如果 Tag 指向
其他 Commit，Workflow 会拒绝发布。

发布的 Release 正文会从 `CHANGELOG.md` 和 `CHANGELOG.zh-CN.md` 中对应版本的
段落生成，包含双语的 Install / 安装和 What's Changed / 更新内容，以及固定版本
的 CLI、Catalog、Bundle 安装命令和版本检查命令。如果任一语言缺少对应版本的
Changelog 段落，或该段落为空，Workflow 会在创建 Tag 前阻止发布。

## 本地验证

在干净的临时 Spec Kit 项目中安装所有本地 Extension 和三个 Workflow，将 Bundle
复制到该项目后再执行校验；这样 CLI 才会解析临时项目中的已安装组件：

```bash
uv run --with pyyaml python scripts/stamp_release.py --version <version> --check
uv run --with pyyaml python scripts/validate_distribution.py
uv run --with pyyaml python scripts/test_validate_distribution.py
uv run --with pyyaml python scripts/test_stamp_release.py
python scripts/test_bundle_install.py
cp -R /path/to/speckit-delivery/bundle /tmp/speckit-bundle-check/bundle
specify bundle validate --path /tmp/speckit-bundle-check/bundle
specify bundle build --path /path/to/speckit-delivery/bundle --output ./dist
python scripts/check_links.py
```

`test_bundle_install.py` 会从本地 release-shaped Catalog 安装实际构建的 Bundle；它要求
Spec Kit `>=1.2.3`，也是 Bundle 的最低版本。单独 Extension/Workflow 仍支持 `>=0.16.4`。
发布前还要在第二个干净项目中验证已发布 Catalog 安装。只有 Manifest、Catalog、
Workflow requirements、压缩包根布局、README 命令和版本完全一致时，才能认为可发布。

## README 归属

根目录 README 负责产品价值、快速开始、支持宿主和状态；根目录双语参考文档负责
长期说明；Extension README 负责命令安装、输出、配置和安全；Catalog 与 Manifest
负责精确的机器可读版本。
