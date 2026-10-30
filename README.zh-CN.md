# Spec Kit Delivery

基于 [GitHub Spec Kit](https://github.com/github/spec-kit) 的证据驱动交付层。它保留
Spec Kit 的 `Spec → Plan → Tasks` 主线，并补充 ADR 决策记忆、项目质量闸门、Ralph
任务编排、实现收敛、简化审查、代码评审、文档同步、交付证据和 PR 交接。

> [!IMPORTANT]
> 当前为 `0.2.x` 初期分发阶段。引导式 Workflow 和命令契约可用于评估；可移植的
> Ralph 路径按任务串行并逐 Task 提交 Git，已支持交付切片与合并策略，Provider 级并行
> 调度和完全机器化的语义分支仍属于后续里程碑。

[English](README.md)

## 快速导航

| 目标 | 入口 |
| --- | --- |
| 从需求启动流程 | `$sd <需求>` 或 `/sd <需求>` |
| 安装到目标项目 | [快速开始](#快速开始) |
| 将已有项目快速接入 SD | [SD 快速配置](快速配置.md) |
| 配置语言质量门禁 | [质量闸门指南](QUALITY-GATE.zh-CN.md) · [配置示例](examples/quality-gate/) |
| 理解 ADR、Ralph 和证据归属 | [架构说明](ARCHITECTURE.zh-CN.md) |
| 打包和发布 | [分发说明](DISTRIBUTION.zh-CN.md) |

`speckit.*` 扩展命令是跨宿主的稳定接口；`$sd` 和 `/sd` 只是 Codex、Claude
Code 等宿主上的便捷入口。

## 为什么需要它

Spec Kit 已经提供了良好的 `specify → plan → tasks → implement` 主线，但通用工程
交付还需要回答：

- 当前工作受哪些既有 ADR 约束？新 ADR 何时从 Proposed 变为 Accepted？
- 功能是否已经存在，关联 Issue／PR／Commit 如何解释当前实现，这次具体改哪些文件？
- 多 Agent 如何只基于 `tasks.md` 安全调度，并由编排器确认完成？
- 实现是否真正收敛到 Spec，是否引入了重复状态、无消费者 API 或投机性扩展？
- 当前 outgoing diff 需要哪些可信验证？复杂度、注释、lint、类型和测试规则如何
  真正阻止任务关闭？
- Spec 文件被忽略后，哪些长期背景仍然保留？

## 主流程与变更 Lane

```text
doctor → 既有决策发现 → 代码／历史／GitHub 参考取证
       → 展示现状＋候选改动目录树 → 范围确认 → specify → clarify
       → ADR 解析 → plan → Proposed ADR → 确定版目录／设计确认
       → tasks → slice／slice gate → analyze → quality brief → Ralph → quality + standards
        → converge → simplify → docs sync → 有界 review/fix → 最终 Review Gate
        → Accepted ADR → Review 时效核对 → evidence → 快照核对后 PR handoff
```

| Lane | 适用范围 | 主要路径 |
| --- | --- | --- |
| Feature | 新功能、跨模块修改、架构变化 | 完整 SDD 流程 |
| Bugfix | 预计有界的缺陷报告 | 结构取证 → 评估／红色证据 → 修复范围确认 → 修复 → 验证 |
| Lightweight | 文档、机械修改、极小的行为不变变更 | 范围 → 修改 → 定向证据 |

### 先看结构与证据，再确定需求和设计

`speckit.delivery.explore` 区分已有能力、全新能力与缺陷调查，先读取代码／测试／ADR，
追踪当前项目相关 Issue、PR、Commit 的实际变更、评审理由和后续修正。全新能力与新机制／
架构选择默认检索 GitHub 成熟实现，记录参考版本或固定 SHA、代码路径、关联 PR／Commit、
采用和不采用的部分；已理解的小范围扩展可以说明原因后跳过外部检索。

Spec 前必须在对话中展示**现状目录树和候选改动目录树**，标注职责、预计新增／修改、复用、
不改、待确认和测试位置，并给出最小方案、替代方案、风险与未知项。确认范围后才进入 Spec；
Plan 完成后在原有 Gate 展示确定版文件、接口和测试方案，再确认详细设计。Bug 根因诊断和复现
仍由官方 `bug.assess` 负责，有界修复不强制完整 Feature Spec；Lightweight 不增加完整调研和
两轮确认。复杂关系可配 Mermaid／SVG 技术图，但不能替代目录树，也不使用 AI 文生图。

Tasks 生成后，`speckit.delivery.slice` 把真实 Task ID 绑定到可独立评审的 Slice，并根据
trunk-safe 证据推导合并方式：默认 stacked PR；只有中间层无法安全进入目标分支时才使用
integration branch。Slice 边界需要单独 Gate 确认；prefix check 失败时回到切片重新分类，
而不是继续堆叠。`tasks.md` 仍是唯一执行队列，`slices.md` 只提供评审／合并边界。

CodeGraph 有可用索引时优先使用；否则明确降级为源码／测试调查，不静默建索引。网络、
GitHub 凭据或参考缺失要说明限制；影响范围判断的关键证据缺口阻断推进，非关键限制由用户明确
接受。正式位置确定后，取证包保存到 `.specify/delivery/<feature-or-run>/exploration.md`，遵循
`artifact_policy`；此前显式保留上下文，不虚构 Feature 路径。后续 Spec／Plan／Tasks 必须消费
已确认的证据；重大范围扩大需要重新确认。详见 [Delivery 契约](extensions/delivery/README.md)。

## 环境要求

- 单独安装 Extension 或 Workflow：Spec Kit CLI `>=0.16.4`
- 使用 Bundle 安装路径：Spec Kit CLI `>=1.2.3`
- 支持 Spec Kit 的宿主集成、Git，以及目标项目自己的构建和测试工具

> [!NOTE]
> `v0.1.1` 已修复 Workflow Catalog 对齐问题，Bundle 在 Spec Kit `>=1.2.3` 上可用；
> `v0.1.2` 增加 Diagram 扩展。请安装与所需组件匹配的固定版本 Catalog，不要把不同
> Tag 的组件混装。

## 快速开始

以下命令在**目标项目**中执行，而不是在本分发仓库中执行。

### 1. 初始化 Spec Kit

```powershell
cd D:\Repos\Acme\my-project
specify init . --integration codex --integration-options="--skills" --script ps
```

按目标宿主选择 Integration：

| 宿主 | 初始化示例 | 原生命令位置 |
| --- | --- | --- |
| Claude Code | `specify init . --integration claude --script sh` | `.claude/skills/` |
| Codex | `specify init . --integration codex --integration-options="--skills" --script ps` | `.agents/skills/` |
| OpenCode | `specify init . --integration opencode --script sh` | OpenCode 命令目录 |
| 其他宿主 | `specify init . --integration generic ...` | 自定义命令目录 |

初始化会创建 `.specify/` 和宿主命令面，不会替换项目现有治理。不要随意使用
`--force`。

### 2. 安装 Delivery 扩展

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

### 3. 初始化项目治理

通过当前宿主调用 `speckit.delivery.init`。它会发现项目已有的 Agent 指令、CI、
hooks、ADR 目录、文档投影和 Spec 文件策略，并生成本地配置。审核配置后再开始
Feature。

它也会生成：

```text
.specify/extensions/quality/quality-config.yml
```

这个文件必须由项目自己确认：每种源码目录配置一个 Profile，每条命令都必须能在
项目根目录执行。分发包不会猜测 Python、Node.js、包管理器或测试框架。

### 4. 选择入口并开始

```text
$sd 为特权配置变更增加审计轨迹。
```

Codex skills 模式会把已安装的 Delivery 扩展渲染成 `speckit-delivery-route`
技能，而不是 shell 可执行命令。不要用 `Get-Command speckit*` 判断 Codex 环境
是否缺少 Delivery 扩展；应检查实际 skills root 下是否存在
`speckit-delivery-route` 技能。

这个规则同样适用于其他宿主：Claude Code 的入口是
`/speckit-delivery-route`，OpenCode 是 `/speckit.delivery.route`，通用适配器
则执行渲染出的命令文件。不要用 `which speckit*` 这类 PATH 检查判断宿主扩展
是否已安装。

`speckit.delivery.context` 是 Feature 规划前和 Bugfix 诊断前的可选上下文步骤：
项目存在 `.codegraph/` 时报告入口、调用方和受影响测试，不存在时返回带缺口说明的
部分结果。它不会初始化索引，也不把代码图当作测试或正确性证据；可用
`code_context: off` 关闭。

`speckit.delivery.handoff` 会把审阅后的 PR 正文写入
`.specify/delivery/<run>/pull-request.md`（或 `pull-request-<slice>.md`），输出
`PR_BODY_PATH` 和 `gh pr create --body-file` 提示。安装扩展不会替换目标仓库的
`.github` PR 模板；GitHub UI 仍读取目标仓库文件，除非显式传入 body 文件。

路由器会选择 Feature、Bugfix 或 Lightweight，不会默认所有需求都走完整 Feature
流程。也可以直接运行：

```bash
specify workflow run feature-delivery --input delivery_run=audit-trail-01 --input spec="描述需要交付的变更"
```

## 质量闸门如何生效

直接 Workflow 必须传入唯一安全 `delivery_run` 标识，恢复沿用同一值。Explore 在进程退出前
保存 `.specify/delivery/<delivery_run>/exploration.md`，后续命令接收确切路径和实际 Gate
选择，再记录所批准的范围／快照；Feature／Bug 标识确定后也不搬移该记录。只有同会话
Router 可暂存上下文；临时模式的直接 Workflow 仍需本地忽略文件。Bugfix 复审修复采用
版本化续修记录，保留官方原始 fix/test 报告，不绕过自动覆盖保护。

直接 Bugfix 还需单独指定规范化 `bug_slug`；官方 Assess 仅写自己的 Bug 评估，编排器核对
并保存身份映射。续修必须执行适用的强制前后置 fix/test Hook，显式传递当前轮报告；不兼容、
缺失或失败的必需 Hook 阻断完成，不能复用原始旧报告冒充本轮上下文。

质量规则的归属保持清晰：

| 规则 | 真实配置位置 | SD 负责什么 |
| --- | --- | --- |
| 格式、lint、类型、测试、复杂度 | Ruff、ESLint、tsconfig、Go/Java/.NET 工具和 CI | 按变更路径执行并记录结果 |
| 注释规范 | 风格文档，必要时配合 linter | 没有可执行检查时报告治理缺口 |
| DRY、重复状态、无消费者 API | Simplify、Review | 生成发现并转成任务 |
| 目录和依赖边界 | 架构文档、依赖规则、ADR | 检查约束，重大变化进入 ADR |

模型开始编辑前调用 `speckit.quality.brief` 获取目标文件规则；Ralph 关闭 Task 前再调用
`speckit.quality.check`、`speckit.review.standards` 与独立
`speckit.review.run scope=task task=<id>`。三种结果均覆盖当前代码和需求快照、
任务变更范围匹配后才能标记 `[X]`，并立即创建和验证对应 Git commit：

```text
QUALITY_VERDICT: pass
STANDARDS_VERDICT: pass
REVIEW_VERDICT: pass
HEAD: <当前 SHA>
SCOPE: T014
```

没有 Profile、必需命令无法运行、检查失败或结果已过期，统一为 `blocked`，不能以
“未验证”当作通过。详细字段、语言配置和关联方式见
[质量闸门配置指南](QUALITY-GATE.zh-CN.md)；可复制的原生配置与 Profile 对照见
[质量闸门示例](examples/quality-gate/)。

Review 独立覆盖**需求符合性、代码质量、架构与设计规范、运行正确性、安全与兼容性、
测试有效性**。它复用有效检查而不重复跑整套测试；既定 Plan 不能掩盖有证据的设计缺陷。
Reviewer 只读，Delivery 负责已核实修复和独立复审；Feature 保持 `tasks.md` 唯一队列，
Bugfix／Lightweight 不强制完整 Feature 文档。

三条 Workflow 最多三次安全修复槽位，取配置上限较小值；完整当前 pass 后 no-op，
跨恢复／新 HEAD 不重置预算。稳定问题 ID 不能因本轮遗漏而关闭，修复者不能自批。
报告绑定实际内容及需求指纹，包含未提交和相关未跟踪文件；覆盖／证据／独立性不足是
incomplete，不能通过 Gate。ADR 等后置变化需复审，handoff 再核对快照。这仍是引导式
契约而非自动语义引擎，详见 [Reviewer 契约](extensions/review/templates/reviewer.md)。

Quality 的复用依据是**原始执行时**的检查输入／配置身份；HEAD／路径相同不足以复用 Hook。
身份缺失或内容不同需重跑受影响检查，不能给旧结果补当前哈希冒充新证据。

## 典型使用场景

| 场景 | 入口 | 关键结果 |
| --- | --- | --- |
| 增加 Redis L2 缓存 | `$sd` | 检索本地缓存 ADR，生成 Proposed ADR，评审后形成自包含 Accepted ADR |
| 大型多模块功能 | `$sd` | 先用 `speckit.delivery.slice` 切分可独立评审的 Slice，确认 stacked／integration 与 merge policy，再逐层交付 |
| 修复重试重复通知 | `$sd` | 先建立红色回归证据，再修复和验证；只有架构决策变化才升级 ADR |
| 修正文档标题 | `$sd` | 走 Lightweight，只运行文档检查，不创建完整 Spec/Ralph 队列 |
| 已有 Tasks 继续实现 | `speckit.ralph.run` | 先创建或复用并验证 `ralph/<feature>` 分支，报告适用治理/代码风格规则；逐 Task 输出治理包并检测，通过关闭门禁后勾选 `[X]` 并立即提交 |

## 长期记录与临时文件

即使 `spec.md`、`plan.md`、`tasks.md` 被 gitignore，以下内容仍应持久化：

- Constitution：跨 Feature 的项目规则
- Issue：问题、范围和验收条件
- ADR：长期架构决策
- 代码、测试和文档：实际行为
- PR：最终变化、风险和验证证据

最终 ADR 和 PR 不应引用临时 Task ID、Review 轮次或被忽略的 Plan 章节。

## Release 安装

维护者通过手动 **Prepare release PR** 统一写入版本和 Catalog URL、完成校验，并创建
`release/v<version>` PR。合并后再运行 **Release distribution**；发布 Pipeline 不回写
`main`，也不移动已有 Tag。

> [!NOTE]
> 安装命令指向准备中的 `v0.2.2`。发布前请使用已发布的 `v0.2.1` Catalog；该版本包含
> PR 正文路径的 Handoff 修复，但不包含中文兜底模板。不要混用不同 Tag 的组件。

指定版本的 Catalog 和 Bundle 安装命令见根目录 `README.md` 的 Release installation
一节；Bundle 要求 Spec Kit `>=1.2.3`，单独组件仍支持 `>=0.16.4`。

## 分发与本地开发

仓库同时发布独立 Extension 压缩包、版本固定的 Extension/Workflow Catalog 和
`speckit-delivery` Bundle。Bundle 校验应在干净目标项目中进行：CLI 会从 Bundle
所在目录向上寻找项目根，不能让 checkout 中仅用于缓存的 `.specify` 目录抢占校验上下文。

```bash
# 在安装完本地组件的干净目标项目中：
cp -R /path/to/speckit-delivery/bundle ./bundle
specify bundle validate --path ./bundle

# 在分发仓库 checkout 中：
specify bundle build --path ./bundle --output ./dist
```

完整的干净项目安装、Catalog 和发布要求见[分发说明](DISTRIBUTION.zh-CN.md)。

## 当前状态

- `0.1.x`：命令契约、引导式 Workflow、Catalog、质量 Profile 和发布结构
- `0.2.x`：交付切片与合并策略，随后是更完整的机器可读状态与跨宿主语义 Gate
- `0.3.x`：Ralph Provider 并行适配
- `1.0.0`：完成多 Integration 的干净项目安装验证

## 参考与贡献

- [架构说明](ARCHITECTURE.zh-CN.md)
- [SD 快速配置](快速配置.md)
- [质量闸门配置指南](QUALITY-GATE.zh-CN.md)
- [质量闸门示例](examples/quality-gate/)
- [分发说明](DISTRIBUTION.zh-CN.md)
- [贡献指南](CONTRIBUTING.md)
- [安全说明](SECURITY.md)

## License

[MIT](LICENSE)
