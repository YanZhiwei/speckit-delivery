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

## 独立 Code Review 参考

选择性借鉴 Superpowers 的 Reviewer Packet 和反馈核实、Codex 的具体可行动缺陷校准、
Anthropic 的分阶段评审、PR-Agent 的持续问题记录、Trail of Bits 的 diff／调用方分析及
Matt Pocock 的聚焦 Task Review，不引入无界多 Reviewer 扩散，也不把置信分当成证据。
PR 状态与链接见 [英文参考评审](REFERENCE-REVIEW.md#independent-review-references)：
Superpowers #1299 已合并，#1481 在调研快照仍开放；PR-Agent #2722 已合并，遗漏不代表解决。

SD 增加统一六维 Task／最终契约、实际内容与需求身份、覆盖／独立性缺口、编排器负责的
Lane 修复和持续有界预算。合成评估仅验证行为，不代表完整业务仓库端到端交付或万能缺陷检测。
