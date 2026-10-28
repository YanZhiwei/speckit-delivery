# 参考项目评审

本分发方案参考了 GitHub Spec Kit、Anthropic Skills、Superpowers 和 DeepSeek Harness
的公开结构与实践。

采用的模式包括：根目录单一入口、一个 Extension 负责一个能力、Workflow 可组合、
使用易记的 `$sd` 门面、渐进式披露、固定版本 Catalog，以及发布前的干净项目安装证据。

明确不采用：仓库专属路径或命令、包含所有能力的单体 Prompt、宣称所有宿主并行能力
等价、直接编辑生成投影，以及与当前需求无关的全仓库简化。

## 借鉴的纪律标准

Code Review 与 Standards Review 从
[unclebob/ub-mode](https://github.com/unclebob/ub-mode) 借鉴了四条标准：测试行为而非
实现、修复根因而非症状、先减后加、只关闭可独立验证的单元。该 skill 本身不纳入分发：
它“最后推送到主线”和按频率提交的建议与本分发明确的授权边界和任务门禁冲突；其
CRAP/重复度/变异工具只输出报告、不会让进程失败，必须先有项目自有 wrapper 才能成为
Quality Gate 命令。
