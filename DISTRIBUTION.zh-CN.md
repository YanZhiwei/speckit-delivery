# 分发说明

## 发布单元

每个 Extension 打包为根目录包含 `extension.yml` 的压缩包；Workflow 是固定版本的
YAML；Bundle 在 Catalog 引用全部解析后构建。

```text
decision  ralph  review  simplify  evidence  quality  docs-sync  diagram  delivery
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
python scripts/test_docs_readme_structure.py
python scripts/test_delivery_runtime.py
python scripts/test_workflow_runtime.py
python scripts/test_bundle_install.py
python scripts/test_bundle_install.py --integration codex
cp -R /path/to/speckit-delivery/bundle /tmp/speckit-bundle-check/bundle
specify bundle validate --path /tmp/speckit-bundle-check/bundle
specify bundle build --path /path/to/speckit-delivery/bundle --output ./dist
python scripts/check_links.py
```

`test_bundle_install.py` 会从本地 release-shaped Catalog 安装实际构建的 Bundle；它要求
Spec Kit `>=1.2.3`，也是 Bundle 和 `0.4.x` Workflow 的最低版本；单独 Extension 命令
仍支持 `>=0.16.4`。
发布前还要在第二个干净项目中验证已发布 Catalog 安装。只有 Manifest、Catalog、
Workflow requirements、压缩包根布局、README 命令和版本完全一致时，才能认为可发布。

本地 Bundle 测试还检查 Explore／Review 模板、review-fix 与 Ralph 资源是否完整打包／安装、
宿主是否渲染命令，以及三个已安装 Workflow 是否与源码一致。它还校验 `sd` 别名与路由
共用正文／输入和登记归属，重装能恢复入口，卸载会清理入口并保留项目配置。默认验证
OpenCode，Codex 变体验证 Skills 模式。结构检查不能证明调研质量或用户实际批准；
行为验收案例位于 `evals/evals.json`。

`scripts/test_workflow_handoff.py` 使用 Spec Kit Command／Gate 的真实传输边界、假宿主消费者和
临时磁盘包，验证新上下文、真实 Gate 选择和缺包失败。在已安装 `specify_cli` 与 PyYAML
的 Python 环境运行（已验证 Spec Kit 1.2.3）；它不是实际模型调用、语义评估、性能验证或端到端交付。

随包提供的 Delivery Runtime Helper 在目标项目根目录运行时需要 Python 3.11
或更高版本以及 Git，只使用标准库和 Git。Helper 新增的本地忽略规则包括 Spec Kit 的
`.specify/workflows/runs/` 运行账本，以及精确的
`.specify/delivery/<delivery_run>/runtime/`；Run 根目录的规划工件和 `evidence.md`
仍遵循项目原有的 Artifact Policy。

`scripts/test_delivery_runtime.py` 使用临时 Git 项目、真实 Helper CLI 和假的原生报告／
回执文件，检查身份、新鲜度、证据哈希、路径边界、原生回执绑定、可重放操作键、规划
检查点关联以及持久尝试记账。`scripts/test_workflow_runtime.py` 使用真实 Shell／Runtime
传输、假 Consumer 和确定性的 Spec Kit `WorkflowEngine`，检查条件派发、恢复、修复上限
和最终守门。这些都是确定性的契约探针，不是实际模型或语义质量验证。

## README 归属

根目录 README 负责产品价值、快速开始、支持宿主和状态；根目录双语参考文档负责
长期说明；Extension README 负责命令安装、输出、配置和安全；Catalog 与 Manifest
负责精确的机器可读版本。

根目录 README 是入口页，不是变更记录：

- **一条事实一个 owner。** Runtime、产物、安装和发布细节留在各自文档里，README
  只保留一句结论加链接。
- **只描述当前行为。** “从 X 起……”属于 `CHANGELOG.md`；README 写现在成立什么。
- **替换，不追加。** 新结论替换它作废的段落；`_check_readme_structure` 中的节清单
  与行数预算就是契约，新增节或增加长度必须先搬走细节。
- **不允许静默漂移。** 用户可见行为变化时，发布 PR 要么更新 README，要么写明
  `unchanged-with-reason`；只改 CHANGELOG 是文档缺口，不是豁免。

`快速配置.md` / `QUICK-CONFIGURATION.md` 负责安装与升级步骤，包括
`scripts/stamp_release.py` 与根目录 README 一起改写版本固定的 Catalog URL。
