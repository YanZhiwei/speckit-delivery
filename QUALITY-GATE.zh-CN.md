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
  - id: test-layout
    owner: quality
    mechanism: "pnpm check:test-layout"
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
excluded_paths: ["poc/**"] # 不在正式产品治理范围；会报告，但不算通过。
reuse_passing_hooks: true
```

`match` 匹配变更文件；`discovery_files` 证明工具链；命令从项目根目录执行；
`rules` 只有在某条已配置命令真正执行时才是门禁。未知占位符不能直接执行。

`standards` 用来显式登记语义规则。每条规则都必须有 owner 和可产出证据的 mechanism；
否则 `speckit.delivery.doctor` 会在计划前阻断流程。它不是伪装成 linter 的配置。

`excluded_paths` 只用于明确不在产品治理范围的代码，例如一次性原型。Quality Brief、
Quality Check 和 Standards Review 会报告排除路径，但不会把它当作已验证。原型成为产品
代码后，应移出排除路径并为新路径增加 Profile。

## 超出 lint 的结构阈值

CRAP、重复度相似度和变异覆盖可以作为 Profile 命令，但前提是项目拥有一个会让进程
失败的命令。只打印表格或写 `.metrics/` 报告的工具本身不是门禁：需要用项目内的小脚本
解析报告、比较配置阈值、打印违规函数并以非零退出。

```yaml
profiles:
  - id: python
    match: ["backend/**/*.py"]
    discovery_files: ["pyproject.toml", "uv.lock"]
    commands:
      complexity: "uv run python tools/crap_gate.py --max 10"
      duplication: "uv run python tools/duplication_gate.py --max 0.8"
      mutation: "uv run python tools/mutation_gate.py --changed"
    rules:
      complexity_max: 10
      duplication_max: 0.8
```

- 工具调用由 wrapper 拥有；本分发仓库不附带任何 wrapper。
- 没有可失败命令时，`rules` 只是元数据。此时应明确报告治理缺口，不能算作通过。
- 变异测试先跑改动范围；首次全树运行既慢，对 outgoing diff 的证明力也更弱。
- 阈值属于项目决定。不要把一个从未同意 `10` 或 `0.8` 的项目直接套用这组数字。

## 规则归属

格式、lint、类型、测试和复杂度应配置在 Ruff、ESLint、Go、Maven/Gradle、.NET 或
项目现有 CI 中。DRY、重复状态、模块归属和架构一致性由 Simplify、Review 和 ADR 负责。
目录边界也是如此，除非项目提供了范围明确、可信的结构 checker；测试目录 checker 就是
一个合适例子。原生配置与 Profile 配对示例见[质量闸门示例](examples/quality-gate/)。

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
