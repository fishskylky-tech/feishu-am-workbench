---
phase: 02-live-runtime-hardening
verified: 2026-04-15T03:27:06Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: 在已配置真实 FEISHU_AM_* 私有环境变量和有效 lark-cli 授权的 shell 中运行 python -m runtime . --json
    expected: resource_resolution 与 capability_report 反映真实 Base / Docs / Task 可用性，且 hint 来源只显示 env:FEISHU_AM_*
    why_human: 依赖当前操作者的私有环境变量、真实飞书资源和授权范围；本次会话只验证了缺失 env 时的 fail-closed 路径
  - test: 在真实 workspace 上以客户简称和客户 ID 各执行一次 gateway customer resolution
    expected: 已知客户返回 resolved；歧义客户返回 ambiguous；不存在客户返回 missing
    why_human: 需要真实 客户主数据、真实 CLI 权限与当前个人环境中的表结构/数据
---

# Phase 2: Live Runtime Hardening 验证报告

**Phase Goal:** 稳定私有配置加载、能力诊断、资源来源解析与客户解析，让 live 操作从可靠 ground truth 起步。目标定义见 [.planning/ROADMAP.md](.planning/ROADMAP.md#L55)。
**Verified:** 2026-04-15T03:27:06Z
**Status:** human_needed
**Re-verification:** 否，首次验证

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | live 资源 hint 只来自私有 env / private runtime input，不再从 checked-in repo 文档取真值 | 已验证 | [runtime/runtime_sources.py](runtime/runtime_sources.py#L33) 仅汇总 env:FEISHU_AM_* 来源；[runtime/runtime_sources.py](runtime/runtime_sources.py#L39) 到 [runtime/runtime_sources.py](runtime/runtime_sources.py#L75) 所有核心 hint 均由 _env_or_fallback 生成；[tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L177) 证明仓库 references 文件存在时仍不会补出 live hints；[tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L221) 证明 env 值会成为唯一来源。 |
| 2 | 缺失必需私有输入时，live 启动会 fail closed，并给出明确 next action | 已验证 | [runtime/resource_resolver.py](runtime/resource_resolver.py#L16) 定义必需键；[runtime/resource_resolver.py](runtime/resource_resolver.py#L44) 到 [runtime/resource_resolver.py](runtime/resource_resolver.py#L48) 将状态收敛为 resolved / unresolved / partial；[runtime/diagnostics.py](runtime/diagnostics.py#L53) 与 [runtime/diagnostics.py](runtime/diagnostics.py#L57) 输出 conclusion 和 next action；[tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L2002) 与 [tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L2033) 覆盖 blocked 文案和缺失输入场景；实际只读 spot-check 中 python -m runtime . --json 返回 unresolved，并把 base/docs/task 全部标为 blocked。 |
| 3 | capability diagnostics 使用 available / degraded / blocked 三态，并在必需资源层面表达清楚 | 已验证 | [runtime/live_adapter.py](runtime/live_adapter.py#L844) 的 LiveCapabilityReporter 为 base/docs/task 分别构建三态结果；其中缺少 base token、docs 资源、tasklist 时分别在 [runtime/live_adapter.py](runtime/live_adapter.py#L867)、[runtime/live_adapter.py](runtime/live_adapter.py#L943)、[runtime/live_adapter.py](runtime/live_adapter.py#L977) 标为 blocked；[runtime/diagnostics.py](runtime/diagnostics.py#L128) 到 [runtime/diagnostics.py](runtime/diagnostics.py#L156) 会把资源状态与 capability 状态汇总成 operator-facing 结论；[tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L1108) 验证 available/degraded 组合；[tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L2033) 验证缺失输入时三项都为 blocked。 |
| 4 | 客户解析保持确定性：精确简称/客户 ID 可解析，唯一候选可解析，歧义与缺失绝不自动猜测 | 已验证 | [runtime/customer_resolver.py](runtime/customer_resolver.py#L25) 先取精确简称或客户 ID；[runtime/customer_resolver.py](runtime/customer_resolver.py#L28) 到 [runtime/customer_resolver.py](runtime/customer_resolver.py#L31) 只允许 resolved / ambiguous / missing 三种保守输出；[tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L708) 验证客户 ID 精确命中；[tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L749) 验证多候选返回 ambiguous；[tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L1816) 验证 live customer backend 优先走 data-query。 |
| 5 | 文档与回归测试已经对齐 hardened contract，明确 .env 只是便利层，repo docs 不是 live truth | 已验证 | [tests/test_env_loader.py](tests/test_env_loader.py#L11) 与 [tests/test_env_loader.py](tests/test_env_loader.py#L35) 验证 .env 加载与显式 env 优先级；[STATUS.md](STATUS.md#L53) 写明 .env 仅是便利层；[STATUS.md](STATUS.md#L67) 写明 checked-in repo 文档不再参与 live truth 判定；[references/feishu-runtime-sources.md](references/feishu-runtime-sources.md#L108) 将 private env authoritative、.env convenience-only、repo docs descriptive only 作为近端规则固定下来。 |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| [runtime/runtime_sources.py](runtime/runtime_sources.py) | 仅产出 env-backed runtime hints | 已验证 | 代码中不再读取仓库 references 文件；source_files 只收集 env:FEISHU_AM_* 来源，见 [runtime/runtime_sources.py](runtime/runtime_sources.py#L33)。 |
| [runtime/env_loader.py](runtime/env_loader.py) | .env 仅作为注入进程环境的便利层，且显式 env 优先 | 已验证 | [runtime/env_loader.py](runtime/env_loader.py#L9) 定义最小 .env loader；[runtime/env_loader.py](runtime/env_loader.py#L40) 保证默认不覆盖已有 env。 |
| [runtime/resource_resolver.py](runtime/resource_resolver.py) | 对 required resources 计算 resolved / partial / unresolved | 已验证 | 必需键集固定在 [runtime/resource_resolver.py](runtime/resource_resolver.py#L16)，状态收敛逻辑在 [runtime/resource_resolver.py](runtime/resource_resolver.py#L44)。 |
| [runtime/diagnostics.py](runtime/diagnostics.py) | 产出 operator-facing 的 conclusion / reason / next action | 已验证 | [runtime/diagnostics.py](runtime/diagnostics.py#L45) 开始渲染文本，结论与 next action 分别在 [runtime/diagnostics.py](runtime/diagnostics.py#L53) 与 [runtime/diagnostics.py](runtime/diagnostics.py#L57)。 |
| [runtime/live_adapter.py](runtime/live_adapter.py) | 对 Base / Docs / Task 产出 capability checks，并提供 customer backend | 已验证 | LiveCapabilityReporter 在 [runtime/live_adapter.py](runtime/live_adapter.py#L844)；customer backend 的行为由 [tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L1816) 等回归测试约束。 |
| [runtime/customer_resolver.py](runtime/customer_resolver.py) | 确定性解析客户，不自动猜歧义 | 已验证 | 精确匹配、唯一候选和 ambiguous/missing 路径都在 [runtime/customer_resolver.py](runtime/customer_resolver.py#L22) 到 [runtime/customer_resolver.py](runtime/customer_resolver.py#L31)。 |
| [tests/test_runtime_smoke.py](tests/test_runtime_smoke.py) | 覆盖 env-only loader、capability 三态、customer 解析与 backend 查询 | 已验证 | 本次运行 python -m unittest tests.test_env_loader tests.test_runtime_smoke，47 tests 全部通过。 |
| [STATUS.md](STATUS.md) 与 [references/feishu-runtime-sources.md](references/feishu-runtime-sources.md) | 文档契约与实现一致 | 已验证 | 状态和参考文档均已改为 private env authoritative / .env convenience-only / repo docs descriptive only。 |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| FOUND-02 | [runtime/env_loader.py](runtime/env_loader.py) + [runtime/runtime_sources.py](runtime/runtime_sources.py) | CLI / gateway 先 load_dotenv，再由 source loader 读取 env-backed hints | 已连通 | [runtime/__main__.py](runtime/__main__.py#L16) 和 [runtime/gateway.py](runtime/gateway.py#L42) 到 [runtime/gateway.py](runtime/gateway.py#L47) 先 load_dotenv 再构建 RuntimeSourceLoader；随后 [runtime/gateway.py](runtime/gateway.py#L59) 到 [runtime/gateway.py](runtime/gateway.py#L66) 在 run 流程内使用这些 source。 |
| LIVE-01 / LIVE-02 | [runtime/resource_resolver.py](runtime/resource_resolver.py) + [runtime/live_adapter.py](runtime/live_adapter.py) + [runtime/diagnostics.py](runtime/diagnostics.py) | gateway.run 产出 resource_resolution / capability_report，diagnostic renderer 再渲染 operator-facing 文案 | 已连通 | [runtime/diagnostics.py](runtime/diagnostics.py#L13) 通过 gateway.build live report；[runtime/gateway.py](runtime/gateway.py#L59) 到 [runtime/gateway.py](runtime/gateway.py#L69) 组装 resource_resolution 与 capability_report；[runtime/diagnostics.py](runtime/diagnostics.py#L45) 消费这些结果。 |
| LIVE-03 | [runtime/customer_resolver.py](runtime/customer_resolver.py) + [runtime/live_adapter.py](runtime/live_adapter.py) + [tests/test_runtime_smoke.py](tests/test_runtime_smoke.py) | gateway.run 调 CustomerResolver，底层通过 LarkCliCustomerBackend 搜索 live customer master | 已连通 | [runtime/gateway.py](runtime/gateway.py#L70) 到 [runtime/gateway.py](runtime/gateway.py#L74) 在 preflight 之前先执行 customer resolution；[tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L1816) 验证 backend 精准查询，[tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L708) 与 [tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L749) 验证 resolver 的确定性分支。 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| [runtime/diagnostics.py](runtime/diagnostics.py) | report.resource_resolution / report.capability_report | [runtime/diagnostics.py](runtime/diagnostics.py#L13) 调 [runtime/gateway.py](runtime/gateway.py#L59) 的 gateway.run | 是，来自 RuntimeSourceLoader、ResourceResolver、LiveCapabilityReporter 的实际对象汇总 | FLOWING |
| [runtime/live_adapter.py](runtime/live_adapter.py#L844) | CapabilityCheck.checks | runtime sources + LarkCliResourceProbe.inspect 结果 | 是，base/docs/task 都根据实时 hint 与 probe outcome 生成，不是静态占位 | FLOWING |
| [runtime/customer_resolver.py](runtime/customer_resolver.py) | CustomerResolution.candidates | LarkCliCustomerBackend.search_customer_master 返回的候选行 | 是，代码路径真实连到 backend；当前只以结构化 CLI payload 回归测试验证，真实 workspace spot-check 仍需人工复核 | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Phase 2 回归测试可执行 | python -m unittest tests.test_env_loader tests.test_runtime_smoke | Ran 47 tests in 0.024s, OK | PASS |
| 缺失私有 env 时 runtime 会 fail closed，而不是回退 repo 文档 | python -m runtime . --json | resource_resolution.status=unresolved；missing_keys 为 4 项；base/docs/task 均为 blocked | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| FOUND-02 | Phase 2 / [02-01-PLAN.md](.planning/phases/02-live-runtime-hardening/02-01-PLAN.md) | Runtime 可从 shell env 或本地 .env 加载私有 FEISHU_AM_* 配置，且显式 env 优先 | 已满足 | [runtime/env_loader.py](runtime/env_loader.py#L9), [runtime/env_loader.py](runtime/env_loader.py#L40), [tests/test_env_loader.py](tests/test_env_loader.py#L11), [tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L221) |
| LIVE-01 | Phase 2 / [02-01-PLAN.md](.planning/phases/02-live-runtime-hardening/02-01-PLAN.md) | Runtime 可从 private runtime sources 解析 Base、archive folder、meeting-note folder、tasklist，且不泄漏 committed secrets | 已满足 | [runtime/runtime_sources.py](runtime/runtime_sources.py#L33), [runtime/resource_resolver.py](runtime/resource_resolver.py#L16), [tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L177), [tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L1108) |
| LIVE-02 | Phase 2 / [02-01-PLAN.md](.planning/phases/02-live-runtime-hardening/02-01-PLAN.md) | Runtime 可在业务推理开始前报告 Base / Docs / Task capability status | 已满足 | [runtime/live_adapter.py](runtime/live_adapter.py#L844), [runtime/diagnostics.py](runtime/diagnostics.py#L45), [tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L1108), [tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L2002), [tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L2033) |
| LIVE-03 | Phase 2 / [02-01-PLAN.md](.planning/phases/02-live-runtime-hardening/02-01-PLAN.md) | Runtime 可按客户名或客户 ID 从 live 客户主数据解析客户 | 已满足，另有 live spot-check 待人工复核 | [runtime/customer_resolver.py](runtime/customer_resolver.py#L25), [tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L708), [tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L749), [tests/test_runtime_smoke.py](tests/test_runtime_smoke.py#L1816) |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| 无 | 无 | 本次 phase 关键文件未发现 FIXME / PLACEHOLDER / not yet implemented 等 stub 标记 | Info | 未发现会阻断 Phase 2 目标的占位实现 |

### Human Verification Required

### 1. 真实私有环境下的 runtime diagnostic

**Test:** 在含真实 FEISHU_AM_* 私有环境变量和有效 lark-cli 授权的 shell 中运行 python -m runtime . --json。  
**Expected:** Base / Docs / Task 的 capability 状态与真实权限一致；hint 来源只显示 env:FEISHU_AM_*；不会出现 repo 文档回填。  
**Why human:** 需要真实私有配置、真实飞书资源和权限范围，本次会话无法代入这些外部依赖。

### 2. 真实 客户主数据 的客户解析

**Test:** 用一个已知客户简称和一个已知客户 ID 各执行一次 gateway customer resolution，再用一个已知歧义前缀执行一次解析。  
**Expected:** 精确客户返回 resolved，歧义前缀返回 ambiguous，不存在客户返回 missing。  
**Why human:** 需要当前个人 workspace 中真实 Base 数据、权限与表字段状态；自动化回归只验证了 integration shape 与确定性分支。

### Gaps Summary

本次验证未发现代码级 must-have 缺口，也没有发现未连线或明显 stub 的关键实现。Phase 2 的核心硬化目标已经在代码、测试和文档层面落地：runtime source 不再信任 checked-in repo 文档，缺失私有输入时会 fail closed，capability diagnostics 使用三态并提供 next action，customer resolution 保持确定性。

当前没有需要进入 gap closure 的实现缺陷。之所以不是 passed，而是 human_needed，只是因为 Phase 2 触及真实飞书资源与私有环境变量，这两条 live 集成复核仍需要操作者在自己的真实环境中完成最后确认。

---

_Verified: 2026-04-15T03:27:06Z_  
_Verifier: Claude (gsd-verifier)_
