# 产物生命周期

| 产物 | 负责人 | 默认生命周期 | 最终要求 |
| --- | --- | --- | --- |
| Constitution | 项目 | 持久 | 约束所有 Feature，不能重复 ADR |
| Issue | Tracker | 持久 | 问题、范围、验收和结果 |
| `spec.md` / `plan.md` | Feature | 项目配置 | 行为契约和当前实现方案 |
| `tasks.md` | Feature/Ralph | 项目配置 | 唯一任务队列和完成状态 |
| Proposed ADR | 架构 | 跟踪 | 编码前的实现基线 |
| Accepted ADR | 架构 | 跟踪 | 与 HEAD 对齐的自包含事实 |
| Review 报告 | 交付运行 | 默认临时 | 结构化 Verdict 和问题 |
| Quality Verdict | Task/Ralph | 默认临时 | HEAD、范围、Profile、检查和结果 |
| Evidence 报告 | 交付运行/PR | 持久摘要 | 命令、结果和环境风险 |
| PR 正文 | Pull Request | 持久 | 变更、风险、决策和证据 |

## Spec 临时模式

允许忽略 Spec 文件，但恢复依赖原工作区；跨 Worktree Worker 必须注入 Task Packet
或复制相关摘录。Issue 和 PR 要保留稳定的需求与验收摘要，ADR 不能链接被忽略的
Feature 路径。只有交接、Review 和 ADR 对齐完成后才能清理。

对于多人协作，跟踪模式仍然更安全。
