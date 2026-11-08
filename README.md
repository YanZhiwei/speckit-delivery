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
> 当前发布线是 `0.4.x`。Workflow、Gate 和命令契约可直接使用；可移植的 Ralph 路径按 Task 串行，每个 Task 一个已验证提交。Provider 级并行和完全机器化的语义分支仍在路线图中。

## 目录

- [适合谁](#适合谁)
- [能力地图](#能力地图)
- [交付如何闭环](#交付如何闭环)
- [快速开始](#快速开始)
- [兼容性与宿主](#兼容性与宿主)
- [本地开发与发布](#本地开发与发布)
- [文档地图](#文档地图)
- [状态与路线图](#状态与路线图)
- [贡献与许可](#贡献与许可)

## 适合谁

- 已经在用 Spec Kit，但 Spec / Plan / Tasks 之后仍靠临时提示推进实现和评审。
- 需要 ADR、质量门禁、独立评审和可审计证据，而不是“测试应该跑过”。
- 需要把执行扩展到多 Agent / 多 Worktree，同时保留逐 Task 的边界和提交确认。
- 需要从 PR 结果反查当时改了什么、跑了什么、哪些风险仍未解决。
- 需要大改动拆成可独立评审的 PR，而不是一次提交几千行。

## 能力地图

| 能力 | 命令 | 深入阅读 |
| --- | --- | --- |
| 路由与预检：三 Lane 选择、Doctor | `speckit.delivery.route`、`.doctor` | [入口说明](skills/README.md) |
| 取证与影响面：现状/候选目录树、外部参考 | `speckit.delivery.explore`、`.context` | [交付契约](extensions/delivery/README.md) |
| 决策记忆：ADR 发现、提案、定稿、一致性检查 | `speckit.decision.context`、`.propose`、`.finalize`、`.check` | [决策契约](extensions/decision/README.md) |
| 切片与合并：Slice 边界、trunk-safe 分类、PR 分组 | `speckit.delivery.slice` | [交付契约](extensions/delivery/README.md) |
| 任务执行：逐 Task 门禁、独立评审、已验证提交 | `speckit.ralph.run` | [Ralph](extensions/ralph/README.md) |
| 质量门禁：项目 Profile、Standards、六维评审 | `speckit.quality.brief`、`.check`、`speckit.review.standards` | [质量闸门](QUALITY-GATE.zh-CN.md) |
| 代码评审与修复：guarded Review、收敛、Repair | `speckit.review.run`、`speckit.delivery.review-fix` | [评审契约](extensions/review/templates/reviewer.md) |
| 简化审查：只处理已接受的候选 | `speckit.simplify.scan`、`.verify` | [Simplify](extensions/simplify/README.md) |
| 证据与收口：绑定快照的证据、Handoff、Close | `speckit.evidence.collect`、`speckit.delivery.handoff`、`.close` | [产物生命周期](LIFECYCLE.zh-CN.md) |
| 文档同步：投影同步、包 README 漂移判断 | `speckit.docs-sync.run`、`.package-readme` | [Docs Sync](extensions/docs-sync/README.md) |
| 图表：Mermaid 默认、可选渲染 | `speckit.diagram.render` | [Diagram](extensions/diagram/README.md) |
| 缺陷处理：评估、修复、回归 | `speckit.bug.assess`、`.fix`、`.test` | [Spec Kit](https://github.com/github/spec-kit) |

## 交付如何闭环

```text
route → doctor → 决策发现 → explore 代码/历史/参考
      → 现状 + 候选目录树 → 范围确认
      → specify → clarify → ADR 解析 → plan（架构约束 + 验证映射）→ 设计确认
      → tasks → slice → analyze → 执行／切片确认 → Ralph → quality → standards → Converge
      → (有追加任务时) Slice → Analyze → 切片再确认 → Ralph → 再评估
      → simplify（只处理已接受的候选）→ docs / package README
      → guarded Review／Repair → ADR 定稿／新鲜度检查 → evidence → handoff → （授权后）PR 合并/关闭 → close
```

三道 Gate 把“想清楚”和“写代码”分开：**范围确认**在 Spec 之前，**设计确认**在 Plan 之后，**执行／切片确认**在 Analyze 之后。`tasks.md` 始终是唯一执行队列，`slices.md` 只提供评审与合并边界。

运行时不变量（状态机与恢复细节见[交付契约](extensions/delivery/README.md#runtime-state-resume-and-conditional-dispatch)，本地协调状态与产物留存见[产物生命周期](LIFECYCLE.zh-CN.md#runtime-coordination-and-checkpoints)）：

- 逐 Task 的任务凭证与真实提交必须逐项成立；已勾选的队列或最终总评审不能替代缺失的逐任务证据。
- `action=status` 只反映同一 Run 的本地协调状态，`action=resume` 只恢复该 Run 的 pending ticket；Review 已通过时不重复调用 Repair，达到修复／收敛上限而仍有阻塞时最终机器守门失败。
- 语义判断由 Quality、Standards、Reviewer、Core 和 Ralph 负责，runtime 只守结构、指纹和新鲜度。

Plan 会写入架构约束来源、适用路径、设计响应、验证负责人和证据缺口，并把约束 ID 传给 Tasks、Brief 和 Review。`delivery-config.yml` 的 `method_adapters` 可分别选择设计、诊断测试和评审方法，默认 `builtin`；显式外部方法必须绑定本地入口、固定版本、资源清单和 SHA-256 摘要，只返回分析回执，不获得计划、队列、提交或评审关闭权。可选开源 Skill 的方法取舍与固定版本见[参考评审](REFERENCE-REVIEW.zh-CN.md#架构-skill-方法参考)和[方法契约](extensions/delivery/templates/method-adapter.md)。

三条 Lane 保持比例感：

| Lane | 适用范围 | 主要路径 |
| --- | --- | --- |
| Feature | 新行为、跨模块、架构变化 | 完整 SDD 流程 + Slice |
| Bugfix | 预计有界的缺陷 | 取证 → 评估/红色证据 → 修复范围确认 → 修复 → 验证 |
| Lightweight | 机械、文档、行为不变的小改动 | 范围 → 修改 → 定向证据 |

安装后可直接调用 `/sd`（OpenCode）、`$speckit-sd`（Codex Skills）、`/speckit-sd`（Claude Code）；快捷入口与完整入口共用同一路由源文件，由安装器统一管理。各宿主名称见[入口说明](skills/README.md)。

## 快速开始

> [!NOTE]
> 以下命令在**目标项目**中执行，不是在本分发仓库中执行。

### 1. 准备 Spec Kit CLI

```bash
uv tool install "specify-cli>=1.2.3"
specify self check
```

| 安装路径 | 要求 |
| --- | --- |
| Bundle | Spec Kit CLI `>=1.2.3` |
| 单独 Extension | Spec Kit CLI `>=0.16.4` |

还需要 Python `>=3.11`（Workflow 运行时）、Git，以及目标项目自己的构建、测试和质量工具。

### 2. 初始化目标项目

```bash
cd /path/to/my-project
specify init . --integration opencode --script sh
```

初始化会创建 `.specify/` 和宿主命令面，不会替换项目现有治理。其他宿主命令见[兼容性与宿主](#兼容性与宿主)；不要随意使用 `--force`。

### 3. 安装 Bundle

```bash
base=https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.4.6/catalogs
specify extension catalog add "$base/extensions.json" --name speckit-delivery --install-allowed
specify workflow catalog add "$base/workflows.json" --name speckit-delivery
specify bundle catalog add "$base/bundles.json" --id speckit-delivery --policy install-allowed
specify bundle install speckit-delivery
```

Bundle 会安装 Delivery、Decision、Ralph、Review、Simplify、Evidence、Quality、Docs Sync、Diagram 扩展，以及 Spec Kit 官方的 Bug 扩展和 Feature、Bugfix、Lightweight 三条 Workflow。不要混用不同 Tag 的组件。

#### 升级已有 Bundle

先备份项目配置与核心模板定制，再按[从 Catalog 升级 Bundle](快速配置.md#从-catalog-升级-bundle)替换版本固定的 Catalog 并运行 `specify bundle update speckit-delivery`。升级后核对 Bundle 版本、项目配置、核心定制和 `/sd` 入口。

### 4. 初始化项目治理

通过当前宿主调用 `speckit.delivery.init`。它会发现项目已有的 Agent 指令、CI、Hooks、ADR 目录、文档投影和 Spec 文件策略，并生成：

```text
.specify/extensions/delivery/delivery-config.yml
.specify/extensions/quality/quality-config.yml
```

审核配置后再开始 Feature。每种源码目录配置一个 Quality Profile，每条命令都必须能在项目根目录执行；分发包不会猜测 Python、Node.js、包管理器或测试框架。见[质量闸门](QUALITY-GATE.zh-CN.md)和[配置示例](examples/quality-gate/)。

### 5. 开始第一次交付

```text
/sd 为特权配置变更增加审计轨迹。
```

路由器会检查项目并选择 Feature、Bugfix 或 Lightweight，不会默认所有需求都走完整流程。也可以直接运行 Workflow：

```bash
specify workflow run feature-delivery \
  --input delivery_run=audit-trail-01 \
  --input spec="为特权配置变更增加审计轨迹"
```

Windows 使用 Python Launcher 时可加 `--input runtime_python="py -3"`，Linux/macOS 可选 `python3`；必须是项目已验证的本地解释器调用。系统 shell 的启动错误需先修复，运行时不会修改全局 shell 配置。

## 兼容性与宿主

| 宿主 | 初始化 | 安装后入口 | 原生命令面 |
| --- | --- | --- | --- |
| Claude Code | `specify init . --integration claude --script sh` | `/speckit-sd`，完整 `/speckit-delivery-route` | `.claude/skills/` |
| Codex | `specify init . --integration codex --integration-options="--skills" --script ps` | `$speckit-sd`，完整 `$speckit-delivery-route` | `.agents/skills/` |
| OpenCode | `specify init . --integration opencode --script sh` | `/sd`，完整 `/speckit.delivery.route` | OpenCode 命令目录 |
| 通用适配器 | `specify init . --integration generic ...` | 执行渲染出的 `speckit.delivery.route` 命令文件 | 自定义命令目录 |

Extension 命令是跨宿主的稳定接口。不要用 `Get-Command speckit*` 或 `which speckit*` 判断扩展是否安装：Codex Skills 模式检查实际 skills root 下的 `speckit-delivery-route` 技能，其他宿主检查渲染后的命令文件。

## 本地开发与发布

仓库同时发布独立 Extension 压缩包、版本固定的 Catalog 和 `speckit-delivery` Bundle；本地安装、干净校验与发布检查见[分发说明](DISTRIBUTION.zh-CN.md)。Bundle 校验必须在干净目标项目中完成：CLI 会从 Bundle 目录向上寻找项目根，checkout 中仅用于缓存的 `.specify` 不能抢占校验上下文。

```bash
cp -R /path/to/speckit-delivery/bundle ./bundle   # 干净目标项目
specify bundle validate --path ./bundle
specify bundle build --path ./bundle --output ./dist   # 分发仓库 checkout
```

提交前按分发说明运行全部分发检查：`scripts/validate_distribution.py`、回放测试、链接检查，以及每个改动宿主与 Workflow 的干净项目安装验证。

发布分两步：先运行 **Prepare release PR** 写入版本与 Catalog URL（同时更新本 README 的固定安装地址），合并 `release/v<version>`；再运行 **Release distribution** 创建 Tag 和发布资产。发布 Pipeline 不回写 `main`，也不移动已有 Tag。

## 文档地图

| 文档 | 内容 |
| --- | --- |
| [架构说明](ARCHITECTURE.zh-CN.md) | 组件边界、控制面和职责归属 |
| [产物生命周期](LIFECYCLE.zh-CN.md) | 持久记录、临时工件、证据与退役 |
| [质量闸门](QUALITY-GATE.zh-CN.md) | 项目 Profile、命令与阻断语义 |
| [交付契约](extensions/delivery/README.md) | Explore、Slice、Runtime、Handoff、Close 的完整契约 |
| [评审契约](extensions/review/templates/reviewer.md) | 六维评审、快照、独立性与问题状态 |
| [SD 快速配置](快速配置.md) | 已有项目的快速接入清单 |
| [分发说明](DISTRIBUTION.zh-CN.md) | Catalog、打包、发布、README 契约与干净安装验证 |
| [变更日志](CHANGELOG.zh-CN.md) | 版本变化与升级说明 |
| [贡献指南](CONTRIBUTING.md) | 提交与评审约定 |
| [安全说明](SECURITY.md) | 凭据、执行与发布边界 |

## 状态与路线图

- 当前线：`0.4.x` 提供持久运行时检查点、条件调度与恢复、Core/Ralph 兼容契约，以及 guarded Review／Converge。
- 下一步：Provider 级并行 Ralph、跨宿主语义 Gate。
- `1.0.0`：完成多 Integration 的干净项目安装验证。

逐版本变化见[变更日志](CHANGELOG.zh-CN.md)。

## 贡献与许可

- 新命令应保持窄边界、有明确的完成条件，并至少附带一条行为 eval。
- 提交前运行[分发说明](DISTRIBUTION.zh-CN.md)中的检查；不要混用不同 Tag 的组件版本。
- 安全相关问题请先读 [SECURITY.md](SECURITY.md)。

[MIT](LICENSE)
