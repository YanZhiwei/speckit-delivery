<div align="center">

# Spec Kit Delivery

**在 GitHub Spec Kit 之上，把 Spec / Plan / Tasks 送到可合并的交付。**

[![Latest release](https://img.shields.io/github/v/release/YanZhiwei/speckit-delivery)](https://github.com/YanZhiwei/speckit-delivery/releases/latest)
[![License](https://img.shields.io/github/license/YanZhiwei/speckit-delivery)](LICENSE)
[![Spec Kit](https://img.shields.io/badge/Spec%20Kit-%E2%89%A51.2.3-blue)](https://github.com/github/spec-kit)

[简体中文](README.md) · [English](README.en.md)

</div>

Spec Kit 负责把需求变成 `Spec → Plan → Tasks`。Spec Kit Delivery 负责让这些工件真正走到可合并的交付：先看清代码、历史与影响面，把架构决策固化为 ADR，用项目本地质量门禁和独立评审约束每个任务，再生成绑定当前 HEAD 的证据与 PR 正文。

它建立在 Spec Kit 的 Extension、Workflow 和 Bundle 机制上，**不替换 Spec Kit，也不绑定模型或宿主**。

> [!IMPORTANT]
> 当前发布线是 `0.3.x`。Workflow、Gate 和命令契约可直接使用；可移植的 Ralph 路径按 Task 串行，每个 Task 一个已验证提交。Provider 级并行和完全机器化的语义分支仍在路线图中。

## 目录

- [适合谁](#适合谁)
- [能力地图](#能力地图)
- [交付如何闭环](#交付如何闭环)
- [快速开始](#快速开始)
- [常用命令](#常用命令)
- [持久记录与临时工件](#持久记录与临时工件)
- [兼容性与宿主](#兼容性与宿主)
- [本地开发与发布](#本地开发与发布)
- [文档地图](#文档地图)
- [状态与路线图](#状态与路线图)

## 适合谁

- 已经在用 Spec Kit，但 Spec / Plan / Tasks 之后仍靠临时提示推进实现和评审。
- 需要 ADR、质量门禁、独立评审和可审计证据，而不是“测试应该跑过”。
- 需要把执行扩展到多 Agent / 多 Worktree，同时保留逐 Task 的边界和提交确认。
- 需要从 PR 结果反查当时改了什么、跑了什么、哪些风险仍未解决。
- 需要大改动拆成可独立评审的 PR，而不是一次提交几千行。

## 能力地图

| 你需要 | 交付层提供 | 入口 |
| --- | --- | --- |
| 判断需求该走哪条流程 | 三 Lane 路由与 Doctor 预检 | `speckit.delivery.route`、`$sd` |
| 先看清现状、影响面和参考实现 | Explore、现状/候选目录树、外部参考调研 | `speckit.delivery.explore` |
| 让架构决策可追溯 | ADR 发现、提案、定稿与一致性检查 | `speckit.decision.context`、`.propose`、`.finalize`、`.check` |
| 把大改动拆成可评审 PR | Slice 边界、trunk-safe 分类、合并策略 | `speckit.delivery.slice` |
| 安全执行任务 | 逐 Task 门禁、独立 Review、已验证提交 | `speckit.ralph.run` |
| 让“完成”有证据 | 项目质量门禁、规范评审、六维代码评审、证据收集 | `speckit.quality.*`、`speckit.review.*`、`speckit.evidence.collect` |
| 生成可提交的 PR 正文 | 绑定快照的 Handoff | `speckit.delivery.handoff` |
| PR 合并或关闭后收口 | 结果记录、工作区退役、单页证据 | `speckit.delivery.close` |
| 文档和包 README 不腐化 | 投影同步、包 README 漂移判断 | `speckit.docs-sync.run`、`.package-readme` |
| 用图解释改动 | Mermaid 默认、可选渲染 | `speckit.diagram.render` |

## 交付如何闭环

```text
route → doctor → 决策发现 → explore 代码/历史/参考
      → 现状 + 候选目录树 → 范围确认
      → specify → clarify → ADR 解析 → plan → 设计确认
      → tasks → slice → 切片确认 → analyze
      → quality brief → Ralph → quality → standards → review
      → converge → simplify → docs / package README
      → 最终 Review → evidence → handoff
      → （授权后）PR 合并/关闭 → close
```

三道 Gate 把“想清楚”和“写代码”分开：**范围确认**发生在 Spec 之前，**设计确认**发生在 Plan 之后，**切片确认**发生在 Task 生成之后。`tasks.md` 始终是唯一执行队列，`slices.md` 只提供评审与合并边界。

三条 Lane 保持比例感：

| Lane | 适用范围 | 主要路径 |
| --- | --- | --- |
| Feature | 新行为、跨模块、架构变化 | 完整 SDD 流程 + Slice |
| Bugfix | 预计有界的缺陷 | 取证 → 评估/红色证据 → 修复范围确认 → 修复 → 验证 |
| Lightweight | 机械、文档、行为不变的小改动 | 范围 → 修改 → 定向证据 |

`$sd` 或 `/sd` 只是宿主上的便捷入口；真正的跨宿主契约是 `speckit.delivery.route` 扩展命令。

## 快速开始

> [!NOTE]
> 以下命令在**目标项目**中执行，不是在本分发仓库中执行。

### 1. 准备 Spec Kit CLI

```bash
uv tool install "specify-cli>=1.2.3"
specify self check
```

- Bundle 安装路径要求 Spec Kit CLI `>=1.2.3`。
- 单独安装 Extension 或 Workflow 要求 `>=0.16.4`。
- 还需要 Git，以及目标项目自己的构建、测试和质量工具。

### 2. 初始化目标项目

```powershell
cd D:\Repos\Acme\my-project
specify init . --integration codex --integration-options="--skills" --script ps
```

| 宿主 | 初始化示例 | 原生命令位置 |
| --- | --- | --- |
| Claude Code | `specify init . --integration claude --script sh` | `.claude/skills/` |
| Codex | `specify init . --integration codex --integration-options="--skills" --script ps` | `.agents/skills/` |
| OpenCode | `specify init . --integration opencode --script sh` | OpenCode 命令目录 |
| 其他宿主 | `specify init . --integration generic ...` | 自定义命令目录 |

初始化会创建 `.specify/` 和宿主命令面，不会替换项目现有治理。不要随意使用 `--force`。

### 3. 安装 Bundle

```bash
specify extension catalog add \
  https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.3.1/catalogs/extensions.json \
  --name speckit-delivery --install-allowed

specify workflow catalog add \
  https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.3.1/catalogs/workflows.json \
  --name speckit-delivery

specify bundle catalog add \
  https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.3.1/catalogs/bundles.json \
  --id speckit-delivery --policy install-allowed

specify bundle install speckit-delivery
```

Bundle 会安装 Delivery、Decision、Ralph、Review、Simplify、Evidence、Quality、Docs Sync、Diagram 扩展，以及 Spec Kit 官方的 Bug 扩展和 Feature、Bugfix、Lightweight 三条 Workflow。不要混用不同 Tag 的组件。

### 4. 初始化项目治理

通过当前宿主调用 `speckit.delivery.init`。它会发现项目已有的 Agent 指令、CI、Hooks、ADR 目录、文档投影和 Spec 文件策略，并生成：

```text
.specify/extensions/delivery/delivery-config.yml
.specify/extensions/quality/quality-config.yml
```

审核配置后再开始 Feature。`quality-config.yml` 必须由项目自己确认：每种源码目录配置一个 Profile，每条命令都必须能在项目根目录执行；分发包不会猜测 Python、Node.js、包管理器或测试框架。参考 [质量闸门指南](QUALITY-GATE.zh-CN.md) 和 [配置示例](examples/quality-gate/)。

### 5. 开始第一次交付

```text
$sd 为特权配置变更增加审计轨迹。
```

路由器会检查项目并选择 Feature、Bugfix 或 Lightweight，不会默认所有需求都走完整流程。也可以直接运行 Workflow：

```bash
specify workflow run feature-delivery \
  --input delivery_run=audit-trail-01 \
  --input spec="为特权配置变更增加审计轨迹"
```

## 常用命令

| 能力 | 命令 |
| --- | --- |
| 路由与交付 | `speckit.delivery.route`、`.doctor`、`.explore`、`.slice`、`.context`、`.lightweight`、`.review-fix`、`.handoff`、`.close` |
| 决策记忆 | `speckit.decision.context`、`.propose`、`.finalize`、`.check` |
| 任务执行 | `speckit.ralph.run` |
| 缺陷处理 | `speckit.bug.assess`、`.fix`、`.test`（Spec Kit 官方 Bug 扩展） |
| 质量门禁 | `speckit.quality.brief`、`speckit.quality.check`、`speckit.review.standards` |
| 代码评审 | `speckit.review.run` |
| 简化审查 | `speckit.simplify.scan`、`.verify` |
| 交付证据 | `speckit.evidence.collect` |
| 文档同步 | `speckit.docs-sync.run`、`speckit.docs-sync.package-readme` |
| 图表 | `speckit.diagram.render` |

几个关键命令的边界：

- `speckit.delivery.handoff` 把审阅后的 PR 正文写到 `.specify/delivery/<run>/pull-request.md`，输出 `PR_BODY_PATH` 和 `gh pr create --body-file` 提示，但**不创建、不推送、不合并 PR**。
- `speckit.delivery.close` 记录 PR 的真实结果：合并记为 `delivered`；未合并关闭记为 `abandoned`，只保留一份自包含的 `evidence.md` 退役说明；被替代记为 `superseded`。它不修改远端。
- `speckit.docs-sync.package-readme` 从包的真实清单、公开导出、CLI、配置和测试命令生成 README；新包会对比 2–3 个同类项目，已有包按变更面输出 `updated` / `unchanged-with-reason` / `gap`。
- `speckit.delivery.context` 可选读取本地 `.codegraph/`；没有索引时返回带缺口说明的部分结果，不会自动建索引，也不把代码图当作正确性证据。

## 持久记录与临时工件

项目可以决定 `spec.md`、`plan.md`、`tasks.md` 是否提交。无论选择哪种策略，以下内容都应能在仓库 HEAD 独立理解：

- **Constitution**：跨 Feature 的项目规则。
- **Issue**：问题、范围和验收条件。
- **ADR**：长期架构决策与理由。
- **代码、测试、文档**：实际行为。
- **PR**：最终变化、风险与验证证据。
- **交付证据**：`.specify/delivery/<run>/evidence.md` 及其记录的 `delivered` / `abandoned` / `superseded` 结果。

`exploration.md`、`slices.md`、`receipts/`、`task-verdicts.yml`、Review 工作区和渲染后的 PR 正文属于运行工作区，遵循 `artifact_policy`；`ephemeral` 时只保留在本地。证据绑定实际内容与需求快照，过期即重跑，不能给旧结果补当前哈希。

见 [产物生命周期](LIFECYCLE.zh-CN.md) 和 [架构说明](ARCHITECTURE.zh-CN.md)。

## 兼容性与宿主

| 项目 | 要求 |
| --- | --- |
| Bundle 安装 | Spec Kit CLI `>=1.2.3` |
| 单独 Extension / Workflow | Spec Kit CLI `>=0.16.4` |
| 宿主 | Codex、Claude Code、OpenCode、通用适配器 |
| 运行时 | Git；目标项目的构建与测试工具 |

Extension 命令是跨宿主的稳定接口。各宿主入口：

| 宿主 | 调用方式 |
| --- | --- |
| Claude Code | `/speckit-delivery-route <request>` |
| Codex | `$speckit-delivery-route <request>`，或可选的 `$sd <request>` |
| OpenCode | `/speckit.delivery.route <request>` |
| 通用适配器 | 执行渲染出的 `speckit.delivery.route` 命令文件 |

不要用 `Get-Command speckit*` 或 `which speckit*` 判断扩展是否安装。Codex Skills 模式应检查实际 skills root 下的 `speckit-delivery-route` 技能；其他宿主检查渲染后的命令文件。

## 本地开发与发布

仓库同时发布独立 Extension 压缩包、版本固定的 Extension/Workflow/Bundle Catalog，以及 `speckit-delivery` Bundle。Bundle 校验应在干净目标项目中进行：CLI 会从 Bundle 所在目录向上寻找项目根，不能让 checkout 中仅用于缓存的 `.specify` 目录抢占校验上下文。

```bash
# 在安装完本地组件的干净目标项目中：
cp -R /path/to/speckit-delivery/bundle ./bundle
specify bundle validate --path ./bundle

# 在分发仓库 checkout 中：
specify bundle build --path ./bundle --output ./dist
```

<details>
<summary>从本地 checkout 安装全部组件（维护者）</summary>

```powershell
$delivery = "D:\Repos\Github\speckit-delivery"

specify extension add --dev "$delivery\extensions\decision"
specify extension add --dev "$delivery\extensions\ralph"
specify extension add --dev "$delivery\extensions\review"
specify extension add --dev "$delivery\extensions\simplify"
specify extension add --dev "$delivery\extensions\evidence"
specify extension add --dev "$delivery\extensions\quality"
specify extension add --dev "$delivery\extensions\docs-sync"
specify extension add --dev "$delivery\extensions\diagram"
specify extension add --dev "$delivery\extensions\delivery"

specify workflow add --dev "$delivery\workflows\feature-delivery\workflow.yml"
specify workflow add --dev "$delivery\workflows\bugfix-delivery\workflow.yml"
specify workflow add --dev "$delivery\workflows\lightweight-delivery\workflow.yml"
```

</details>

提交前运行分发检查：

```bash
uv run --with pyyaml python scripts/validate_distribution.py
uv run --with pyyaml python scripts/test_validate_distribution.py
uv run --with pyyaml python scripts/test_workflow_handoff.py
uv run --with pyyaml python scripts/check_links.py
uv run --with pyyaml python scripts/test_bundle_install.py --integration opencode
```

`test_workflow_handoff.py` 需要已安装 Spec Kit CLI 1.2.3。

发布分两步：先运行 **Prepare release PR** 写入版本与 Catalog URL（同时更新本 README 中的固定版本安装地址），合并 `release/v<version>`；再运行 **Release distribution** 创建 Tag 和发布资产。发布 Pipeline 不回写 `main`，也不移动已有 Tag。完整要求见 [分发说明](DISTRIBUTION.zh-CN.md)。

## 文档地图

| 文档 | 内容 |
| --- | --- |
| [架构说明](ARCHITECTURE.zh-CN.md) | 组件边界、控制面和职责归属 |
| [产物生命周期](LIFECYCLE.zh-CN.md) | 持久记录、临时工件、证据与退役 |
| [质量闸门](QUALITY-GATE.zh-CN.md) | 项目 Profile、命令与阻断语义 |
| [交付契约](extensions/delivery/README.md) | Explore、Slice、Handoff、Close 的完整契约 |
| [评审契约](extensions/review/templates/reviewer.md) | 六维评审、快照、独立性与问题状态 |
| [SD 快速配置](快速配置.md) | 已有项目的快速接入清单 |
| [分发说明](DISTRIBUTION.zh-CN.md) | Catalog、打包、发布与干净安装验证 |
| [变更日志](CHANGELOG.zh-CN.md) | 版本变化与升级说明 |
| [贡献指南](CONTRIBUTING.md) | 提交与评审约定 |
| [安全说明](SECURITY.md) | 凭据、执行与发布边界 |

## 状态与路线图

- `0.1.x`：命令契约、引导式 Workflow、Catalog、质量 Profile 和发布结构。
- `0.2.x`：交付切片与合并策略、Handoff 正文路径、中文兜底模板。
- `0.3.x`：交付结果收口与退役、包 README 节点，以及三条 Lane 的文档漂移判断。
- 后续：Provider 级并行 Ralph、机器可读的 Workflow 状态、跨宿主语义 Gate。
- `1.0.0`：完成多 Integration 的干净项目安装验证。

## 贡献与许可

- 新命令应保持窄边界、有明确的完成条件，并至少附带一条行为 eval。
- 提交前运行上面的分发检查；不要混用不同 Tag 的组件版本。
- 安全相关问题请先读 [SECURITY.md](SECURITY.md)。

[MIT](LICENSE)
