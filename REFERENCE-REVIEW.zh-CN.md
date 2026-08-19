# 参考项目评审

本分发方案参考了 GitHub Spec Kit、Anthropic Skills、Superpowers 和 DeepSeek Harness
的公开结构与实践。

采用的模式包括：根目录单一入口、一个 Extension 负责一个能力、Workflow 可组合、
使用易记的 `$sd` 门面、渐进式披露、固定版本 Catalog，以及发布前的干净项目安装证据。

明确不采用：仓库专属路径或命令、包含所有能力的单体 Prompt、宣称所有宿主并行能力
等价、直接编辑生成投影，以及与当前需求无关的全仓库简化。
