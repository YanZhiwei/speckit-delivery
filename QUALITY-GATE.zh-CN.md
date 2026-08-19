# 质量闸门配置

`speckit.quality.check` 执行项目自己声明的质量 Profile，并返回是否可以关闭 Task；
它不替代语言原生工具。

开始编辑前先调用 `speckit.quality.brief`。它读取同一份 Profile，输出目标文件适用
的规范、架构边界、应避免的模式和编辑后的验证命令。它只是事前提醒，不代表代码
已经通过检查。

## 配置方式

在 `.specify/extensions/quality/quality-config.yml` 中按源码族配置 Profile：

```yaml
policy_sources:
  architecture: [Docs/architecture/repo-structure.md]
  style: [Docs/architecture/code-style.md]
standards:
  - id: layer-boundaries
    owner: review
    mechanism: "speckit.review.standards against the architecture policy"
  - id: avoid-duplication
    owner: simplify
    mechanism: "speckit.simplify.scan before final review"
profiles:
  - id: python
    match: ["backend/**/*.py"]
    discovery_files: ["pyproject.toml", "uv.lock"]
    commands:
      format: "uv run ruff format --check {changed_files}"
      lint: "uv run ruff check {changed_files}"
      typecheck: "uv run mypy backend"
      test: "uv run pytest {affected_tests}"
    rules:
      complexity_max: 10
unprofiled_changed_paths: block
reuse_passing_hooks: true
```

`match` 匹配变更文件；`discovery_files` 证明工具链；命令从项目根目录执行；
`rules` 只有在某条已配置命令真正执行时才是门禁。未知占位符不能直接执行。

`standards` 用来显式登记语义规则。每条规则都必须有 owner 和可产出证据的 mechanism；
否则 `speckit.delivery.doctor` 会在计划前阻断流程。它不是伪装成 linter 的配置。

## 规则归属

格式、lint、类型、测试和复杂度应配置在 Ruff、ESLint、Go、Maven/Gradle、.NET 或
项目现有 CI 中。DRY、重复状态、模块归属、目录边界和架构一致性由 Simplify、Review
和 ADR 负责。原生配置与 Profile 配对示例见[质量闸门示例](examples/quality-gate/)。

Ralph 只有收到当前 HEAD 的两类结果，才能把 Task 标记为 `[X]`：

```text
QUALITY_VERDICT: pass
STANDARDS_VERDICT: pass
HEAD: <当前 SHA>
SCOPE: T014
```

缺少 Profile、必需命令不可执行、检查失败或范围过期，都是 `blocked`，不能默认为
通过。Quality verdict 负责可执行检查；Standards verdict 负责 DRY、模块归属、分层方向、
公共接口、注释意图与 ADR 是否需要调整。
