# 参考项目评审

本分发方案参考了 GitHub Spec Kit、Anthropic Skills、Superpowers 和 DeepSeek Harness
的公开结构与实践。

采用的模式包括：根目录单一入口、一个 Extension 负责一个能力、Workflow 可组合、
使用易记的 `$sd` 门面、渐进式披露、固定版本 Catalog，以及发布前的干净项目安装证据。

明确不采用：仓库专属路径或命令、包含所有能力的单体 Prompt、宣称所有宿主并行能力
等价、直接编辑生成投影，以及与当前需求无关的全仓库简化。

## 取证优先的规划参考

本轮选择性借鉴，而非引入完整框架或自动安装外部 Skill：

- GSD 的目录树、关键文件职责和新增代码／测试位置表达。
- Superpowers `writing-plans` 的先确定文件职责、再拆任务及精确修改／测试路径。
- Superpowers `systematic-debugging` 的边界追踪、正常／异常路径对比和先取证后修复。
- OpenSpec `explore` 的先理解现状再形成提案，探索不等于实现。
- Spec Kit 原有 Plan 模板的真实源码路径与结构选择理由。

固定版本源码链接见 [英文参考评审](REFERENCE-REVIEW.md#evidence-first-planning-references)。
SD 在此基础上增加有界 Issue／PR／Commit 溯源、按场景检索 GitHub 参考、两棵目录树及
范围／设计确认点；参考方案不能覆盖目标项目既有治理和 ADR。

## 问题定义与专项复盘

用户提供的十条调查／评审提示，按职责选择性融入现有契约。它们是方法要求，不代表
已经执行过对应审计，也不成为所有任务的固定前置流程：

| 提示意图 | 执行归属 | 采纳边界 |
| --- | --- | --- |
| 1. 从本质原因修复 | [诊断 Profile](extensions/delivery/templates/method-diagnose.md) 与官方 Bug 评估 | 用证据连接症状、违反的不变量和故障路径；第一性原理不能替代复现，也不强求单一根因。 |
| 2. 澄清偏好、比较方案 | [目标与方案](extensions/delivery/templates/exploration.md#outcome-and-problem-framing) | 复用已知偏好，只问影响决策的未知项；比较真实可行方案，明确要求且可行时才固定三版。 |
| 3. 质疑问题定义 | [目标定义](extensions/delivery/templates/exploration.md#outcome-and-problem-framing) | 区分目标、症状和手段，有证据时建议重定义；保留用户意图与范围决定权。 |
| 4. 推演间接影响 | [范围风险](extensions/delivery/templates/exploration.md#scope-risks-and-verification) 与 [Review](extensions/review/templates/reviewer.md#review-method-and-calibration) | 用可信因果链连接模块、用户行为与维护成本；尚未验证的影响保持为假设。 |
| 5. 跨领域参考 | [方案比较](extensions/delivery/templates/exploration.md#options-and-candidate-change-tree) | 核对共享不变量、前提和失败模式，记录来源；类比不能证明适配或全局最优。 |
| 6. 主动反驳首选方案 | [方案比较](extensions/delivery/templates/exploration.md#options-and-candidate-change-tree)、诊断与 Review | 检查最强合理反例和区分性证据，复用现有决策／评审路径。 |
| 7. 还原设计历史 | [历史专项审计](extensions/delivery/templates/focused-audits.md#2-history-and-current-design-intent) | 明确请求才扩大历史范围；关联原始理由与当前约束，证据缺失保留为未知。 |
| 8. 评估新人认知成本 | [接手成本审计](extensions/delivery/templates/focused-audits.md#3-newcomer-comprehension) 与 [Simplify](extensions/simplify/commands/speckit.simplify.scan.md) | 沿真实变更追踪 owner 与隐含不变量；代码／层数减少不等于更易理解。 |
| 9. 找出慢 PR 或慢代码 | [PR 性能审计](extensions/delivery/templates/focused-audits.md#4-pr-performance) | 定义时间口径与完整覆盖，区分流程等待和运行性能，要求可比较的实测证据。 |
| 10. 将重复失败转为预防措施 | [重复缺陷复盘](extensions/delivery/templates/focused-audits.md#5-recurring-bugs-rework-and-rollbacks) | 关联真实事件，区分修复尝试与复发，先提出有 owner、验证方法和成本的控制措施，再按项目治理采纳。 |

普通交付仍做有界历史调查和适度评审；可选 [审计方法](extensions/delivery/templates/focused-audits.md)
复用同一 Explore 工件并返回建议，不增加远程写入、规则采纳权、自动跨 Run 关联或分析运行时。
缺失的 Tracker 分页、性能测量和事故记录必须如实作为覆盖缺口。行为场景位于
`evals/evals.json`；结构与安装检查不证明这些分析的语义效果。

## 独立 Code Review 参考

选择性借鉴 Superpowers 的 Reviewer Packet 和反馈核实、Codex 的具体可行动缺陷校准、
Anthropic 的分阶段评审、PR-Agent 的持续问题记录、Trail of Bits 的 diff／调用方分析及
Matt Pocock 的聚焦 Task Review，不引入无界多 Reviewer 扩散，也不把置信分当成证据。
PR 状态与链接见 [英文参考评审](REFERENCE-REVIEW.md#independent-review-references)：
Superpowers #1299 已合并，#1481 在调研快照仍开放；PR-Agent #2722 已合并，遗漏不代表解决。

SD 增加统一六维 Task／最终契约、实际内容与需求身份、覆盖／独立性缺口、编排器负责的
Lane 修复和持续有界预算。合成评估仅验证行为，不代表完整业务仓库端到端交付或万能缺陷检测。

## 借鉴的纪律标准

Code Review 与 Standards Review 从
[unclebob/ub-mode](https://github.com/unclebob/ub-mode) 借鉴了四条标准：测试行为而非
实现、修复根因而非症状、先减后加、只关闭可独立验证的单元。该 skill 本身不纳入分发：
它“最后推送到主线”和按频率提交的建议与本分发明确的授权边界和任务门禁冲突；其
CRAP/重复度/变异工具只输出报告、不会让进程失败，必须先有项目自有 wrapper 才能成为
Quality Gate 命令。

## 架构 Skill 方法参考

2026-11-03 按固定提交读取了以下 MIT 开源方法，源码链接见
[英文调研表](REFERENCE-REVIEW.md#architecture-skill-methods)。这些来源不作为必装依赖；
实际执行契约由 Delivery 取证模板中的 [Plan 检查点](extensions/delivery/templates/exploration.md#architecture-constraints)
统一维护。

- Jeffallan `architecture-designer`：借鉴非功能需求、方案取舍、运维成本和失败模式检查；
  示例指标不成为项目要求，示例 Accepted ADR 不绕过 SD 的 Proposed／评审／定稿流程。
- Matt Pocock `codebase-design` 和 `Design It Twice`：借鉴接口方案比较、调用方认知负担、
  状态／复杂度归属和接口测试；保留项目术语，不强制三 Agent 并行或全仓架构扫描。
- Superpowers `brainstorming`：借鉴先读现状、比较方案、明确约束；复用 SD 已有确认点，
  不引入另一轮问答、设计文档和规划队列。
- wshobson `architecture-patterns`：后端场景可参考依赖方向、数据归属和测试边界；
  Clean／Hexagonal／DDD 按需要选择，不强迫所有项目分层。

Architecture Guard 3.5.0 已是相邻的完整编排方案，其独立安装器为主入口，旧 Spec Kit
扩展仅接收安全与故障修复。SD 不将其设为前置依赖，也不继承默认不阻断的违规策略。

共享 [方法适配器契约](extensions/delivery/templates/method-adapter.md) 把上述来源规则
落实为设计、诊断测试、评审三个可选提供者流程：校验本地资源摘要，默认 builtin，只向
现有 owner 返回分析；不继承来源 Skill 的计划、队列、修复预算、提交或评审关闭权。

可选诊断与评审 profile 采用同一来源规则，固定快照与取舍：

- Superpowers `systematic-debugging`：借鉴稳定复现、跨边界取证、正常／故障路径对比、
  单一假设与最小实验；其修复／TDD／完成循环不替代官方 Bug 与 SD 修复预算。
- Superpowers `writing-good-tests`：借鉴有意义的接口行为、独立推导期望值和可命名的
  真实缺陷；不把“所有改动必须先写测试”变成通用闸门，测试策略仍由项目决定。
- Superpowers `requesting-code-review`：借鉴新上下文、精确 scope、带位置和证据的问题；
  其提交／Worktree 假设及预算耗尽后搁置问题不能替代 SD 关闭规则。
- Matt Pocock `tdd`：借鉴公共接口行为测试、单条纵向红绿循环、重构留给评审；用户确认
  seam 与仓库命令不是通用默认值。
- Matt Pocock `code-review`：借鉴规范与需求分轴、仓库规则优先；两轴报告不能替代 SD
  六维、快照和问题生命周期。

固定源码链接见 [英文参考评审](REFERENCE-REVIEW.md#workflow-method-references)。已可用
Skill 的额外方法仍需记录版本／内容哈希、资源路径和采纳／拒绝理由，先作为候选建议。
项目治理和已批准设计决定约束，Quality 运行项目自有检查；隐式导入或运行时 DI 等无法
读取的图覆盖范围必须如实报告，不能以绿色结果代替未执行的验证。
