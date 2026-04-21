# 架构文档

<!-- generated-by: gsd-doc-writer -->

## 系统概述

飞书 AM 工作台是一个围绕飞书 Base、多维表格、文档和待办事项构建的个人客户经理（AM）工作流技能。它将混合输入（如会议记录、客户材料）转化为结构化的客户全貌视图，并在各工作台层提出更新建议，所有变更都需要用户确认后才真正执行。

系统的核心设计原则是：**先读清楚，再给建议，最后才行动**。工作台不会凭空输出，而是在做任何判断之前先拉取客户的最新上下文（联系记录、合同进展、关系变化）。

系统包含两套专家审核机制：
1. **关键词模式** - 基于预定义关键词的快速审核（内置兜底）
2. **LLM 模式** - 基于专家卡片配置调用 OpenAI/Anthropic API 进行深度审核（可配置降级）

## 四层架构

工作台采用分层设计，数据层从底向上依次是：

### 第一层：客户主数据（Customer Master Data Index）

客户主数据表是整个工作台的**数据基准**。所有客户的唯一标识（客户ID）必须从这张表获取，不能自行杜撰。这张表是受保护的——只有特定的字段允许更新，策略类字段（如客户定位、战略方向）应当缓慢变动。

```
客户主数据表
├── 客户ID（主键，唯一数据源）
├── 客户名称
├── 客户简称
├── 战略字段（受保护，变动需谨慎）
└── 其他基本信息
```

### 第二层：结构化明细表（Detail Tables）

飞书 Base 中的明细表是客户数据的结构化存储层，包括：

| 表名 | 用途 | 特点 |
|------|------|------|
| 合同 | 客户合同台账 | 记录合同状态、金额、期限 |
| 行动计划 | 待执行事项 | 结构化跟进任务 |
| 关键人 | 客户组织关系 | 联系人、决策链 |
| 联系记录 | 每次沟通的历史 | 时间、内容摘要 |
| 竞品 | 竞争态势跟踪 | 竞品名称、影响程度 |

每张表有明确的字段schema，更新前需要验证字段存在性和类型匹配。

### 第三层：客户档案（Customer Archive）

客户档案是多维表格和公开输入的**提炼产物**——每个客户只有一份标准的档案文档，以叙事风格记录客户的完整弧线：历史背景、关键人物、风险与机会、当前姿态。这份文档是从明细记录和公开材料中蒸馏出来的，是客户状态的权威叙述。

### 第四层：飞书待办（Feishu Todo）

飞书待办是执行提醒，帮助推进具体事项。**待办不替代结构化明细记录**——待办是提醒层，而明细表才是事实层。待办的创建和更新需要与明细表状态保持一致。

```
┌─────────────────────────────────────────────────────┐
│                    用户输入                          │
└────────────────────┬────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────┐
│              Scene 调度层 (scene_registry)           │
│  7 个注册场景：会后整理 / 客户状态 / 档案刷新 /       │
│  待办管理 / 客户群分析 / 会前准备 / 提案生成           │
└────────────────────┬────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────┐
│          Runtime 核心 (scene_runtime.py)            │
│  场景执行引擎：实体提取 → 上下文恢复 → 预检 → 建议    │
└────────────────────┬────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────┐
│         Expert Agent 层 (expert_agent_invoker)      │
│  专家审核：input_review → evidence聚合 → output_review │
│  CircuitBreaker 防止级联失败                          │
└────────────────────┬────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────┐
│              Gateway (gateway.py)                   │
│         统一入口，调度各 Adapter 访问飞书             │
└──────────┬──────────────────────────┬───────────────┘
           ▼                          ▼
┌─────────────────────┐  ┌─────────────────────────────┐
│   Live Adapter      │  │   Expert Card Loader        │
│  (live_adapter.py)  │  │ (expert_card_loader.py)      │
│   实时数据访问       │  │    专家卡片 YAML 加载        │
│   Schema 预检       │  │    Schema 验证 + 安全检查   │
└──────────┬──────────┘  └──────────────┬──────────────┘
           │                              ▼
           │               ┌─────────────────────────────┐
           │               │   Default LLM Adapter       │
           │               │ (default_llm_adapter.py)    │
           │               │   OpenAI / Anthropic API     │
           │               │   幻觉检测 + 错误分类        │
           │               └─────────────────────────────┘
           ▼                             ▼
┌─────────────────────────────────────────────────────┐
│              飞书基础设施                              │
│     Base 多维表格 / 文档 / 待办 / 会议笔记            │
└─────────────────────────────────────────────────────┘
```

## 核心组件

### scene_runtime.py（场景执行引擎）

这是工作台的核心运行时，大小约 77KB。负责：

1. 接收 SceneRequest 请求
2. 通过 Gateway 访问飞书实时数据
3. 执行实体提取和上下文恢复
4. 调用 Expert Analysis Helper 进行分析
5. 通过 Expert Agent 进行专家审核（input_review / output_review）
6. 生成 WriteCandidate（写回候选）
7. 构建确认清单，等待用户确认
8. 执行写回并返回结果

### gateway.py（统一网关）

大小约 3.6KB，负责协调资源发现、客户解析和写入安全检查：

- `FeishuWorkbenchGateway`：主网关类，协调所有后端
- `for_live_lark_cli()`：工厂方法，初始化完整的 Lark CLI 后端栈
- 管理 `CustomerResolver`、`SchemaPreflightRunner`、`WriteGuard` 等组件

### live_adapter.py（实时数据访问适配器）

大小约 41KB，是访问飞书 Base 的核心适配器：

- `LarkCliBaseQueryBackend`：Base 多维表格查询
- `LarkCliCustomerBackend`：客户主数据查询
- `LarkCliSchemaBackend`：Schema 探测和验证
- `LarkCliResourceProbe`：资源探测（表、字段是否存在）
- `LiveCapabilityReporter`：平台能力检测
- `LiveWorkbenchConfig`：配置聚合类

所有对飞书 Base 的操作都通过这个适配器，它屏蔽了底层 lark-cli 的复杂性。

### expert_analysis_helper.py（专家分析辅助）

大小约 23KB，负责证据聚合和推理辅助：

- `EvidenceContainer`：证据容器，存储从各数据源获取的证据
- `EvidenceSource`：证据源（客户档案、会议笔记、联系记录等）
- 四维度分析（风险、机会、关系、项目进展）

### expert_agent_invoker.py（专家代理调用编排器）

大小约 9KB，负责专家代理的调用编排和安全防护：

- `ExpertAgent`：抽象基类，定义平台适配器接口
- `CircuitBreaker`：熔断器模式，防止级联失败（5 次失败后熔断，60 秒恢复）
- `AggregatedFailureResult`：聚合失败结果，触发降级到关键词模式
- `build_input_review_prompt()` / `build_output_review_prompt()`：构建审核提示词
- `invoke_llm_expert()`：LLM 专家调用入口

关键设计：
- **熔断器模式**：连续失败 5 次后熔断，60 秒后尝试半开状态恢复
- **显式错误分类**：Timeout、AuthFailure、RateLimit、EmptyResponse、ParseFailure、APIError
- **失败即降级**：任何 LLM 错误都触发降级到关键词模式

### expert_card_loader.py（专家卡片加载器）

大小约 17KB，负责从 YAML 配置加载专家卡片：

- `ExpertCardConfig`：专家卡片配置数据结构（frozen=True，不可变）
- `load_expert_cards()`：从 `scenes/{scene}/expert-cards.yaml` 加载配置
- `validate_agent_reference()`：验证 agent_name 在 agent-registry.yaml 中存在
- `RegistryCache`：单例缓存，带 mtime + TTL（60秒）双保险失效策略

安全特性：
- **YAML 安全**：仅使用 `yaml.safe_load()`，无 eval
- **路径安全**：禁止 symlink、强制 .md 扩展、路径遍历防护
- **Schema 验证**：必填字段、类型检查、check_signals 非空验证

### default_llm_adapter.py（默认 LLM 适配器）

大小约 13KB，实现基于 OpenAI/Anthropic API 的专家审核：

- `DefaultLLMExpertAgent`：主适配器类，支持 OpenAI 和 Anthropic
- `validate_api_key_config()`：启动时验证 API key，友好错误提示
- `_invoke_openai()` / `_invoke_anthropic()`：具体 API 调用（30 秒超时）
- `_parse_result()`：解析 LLM 响应为 ExpertReviewResult
- `_check_hallucination()`：幻觉检测，阻止引用不在 check_signals 中的信号

错误处理：
- 显式处理：Timeout、AuthFailure(401)、RateLimit(429)、EmptyResponse、ParseFailure
- 所有其他异常触发降级到关键词模式

### 其他关键组件

| 组件 | 文件 | 职责 |
|------|------|------|
| 客户解析器 | customer_resolver.py | 从客户名称解析客户ID，处理歧义 |
| Schema预检 | schema_preflight.py | 写前回查表/字段是否存在 |
| 写保护器 | write_guard.py | 控制哪些字段可写、哪些受保护 |
| 待办写入器 | todo_writer.py | 创建和更新飞书待办 |
| 确认清单 | confirmation_checklist.py | 构建用户确认清单 |
| 语义注册表 | semantic_registry.py | 管理表语义配置和字段映射（模块级常量） |
| 运行时源加载器 | runtime_sources.py | 从配置文件加载资源信息 |
| 诊断模块 | diagnostics.py | 运行时能力诊断和友好错误提示 |
| 环境加载器 | env_loader.py | 简单的 .env 文件加载 |
| CLI 封装 | lark_cli.py | lark-cli 命令行工具封装 |
| 资源解析器 | resource_resolver.py | 运行时资源发现和状态追踪 |
| 平台能力 | scene_runtime.py | PlatformCapabilities 定义各平台能力 |

## 专家代理系统

### Agent 注册表（agent-registry.yaml）

SOLE SOURCE OF TRUTH，定义所有可用的专家代理：

```yaml
agents:
  sales-account-strategist:
    platform: openclaw
    enabled: true
    prompt_file: sales-account-strategist.md

  customer-service:
    platform: hermes
    enabled: true
    prompt_file: customer-service.md

  sales-proposal-strategist:
    platform: claude_code
    enabled: true
    prompt_file: sales-proposal-strategist.md
```

### 专家卡片配置（scenes/{scene}/expert-cards.yaml）

每个场景独立的审核配置：

```yaml
input_review:
  enabled: true
  expert_name: "会议材料审核专家"
  review_type: "materials_audit"
  check_signals:
    - "遗漏的关联信息"
    - "关键人变更"
  output_field: "input_audit_notes"
  prompt_file: agents/sales-account-strategist.md  # 启用 LLM 模式
  agent_name: sales-account-strategist

output_review:
  enabled: true
  expert_name: "策略建议审核专家"
  review_type: "strategy_audit"
  check_signals:
    - "风险信号"
    - "机会信号"
  output_field: "output_audit_notes"
  prompt_file: agents/sales-account-strategist.md
  agent_name: sales-account-strategist
```

### 审核流程

```
用户输入
    │
    ▼
[Input Review - 关键词模式或 LLM 模式]
    │
    ├── PASS：所有信号通过，继续
    ├── FLAG：信号缺失，降级建议或阻断
    └── BLOCK：严重问题，阻断写回
    │
    ▼
证据聚合（EvidenceContainer）
    │
    ▼
[Output Review - 关键词模式或 LLM 模式]
    │
    ├── PASS：建议通过
    ├── FLAG：建议有问题
    └── BLOCK：建议不可接受
    │
    ▼
确认清单 → 用户确认 → 执行写回
```

### 降级策略

| 失败场景 | 处理方式 |
|----------|----------|
| API key 缺失 | 友好错误提示，建议设置或使用关键词模式 |
| Timeout (30s) | 降级到关键词模式 |
| Auth Failure (401) | 降级到关键词模式 |
| Rate Limit (429) | 降级到关键词模式 |
| Empty Response | 降级到关键词模式 |
| Parse Failure | 降级到关键词模式 |
| Circuit Breaker OPEN | 降级到关键词模式 |
| 场景目录不存在 | fail-open，返回 None |
| YAML 文件不存在 | fail-open，返回 None |

## 场景系统

工作台注册了 7 个场景，通过 scene_registry.py 统一调度：

| 场景标识 | 功能描述 | 核心流程 | 专家卡片 |
|----------|----------|----------|----------|
| `post-meeting-synthesis` | 会议内容 → 结构化客户判断 | 会议类型分类 → 实体提取 → 更新建议 | input + output |
| `customer-recent-status` | 四维度客户状态查询 | 拉取最新上下文 → 四维度分析 | input |
| `archive-refresh` | 客户档案刷新 | 汇聚历史档案 + 当前记录 → 生成更新建议 | input + output |
| `todo-capture-and-update` | 待办跟进捕获 | 提取待办事项 → 创建/更新飞书待办 | output |
| `cohort-scan` | 客户群分析 | 按维度聚合 → 风险/机会扫描 | input |
| `meeting-prep` | 会前准备 | 七维度简报生成 | input + output |
| `proposal` | 提案生成 | 五维度结构化提案草案 | input + output |

每个场景都遵循统一的执行范式：**输入 → 分析 → 建议 → 确认 → 写回**。

## 数据流

一次典型的场景执行数据流如下：

```
1. 用户输入 + 场景标识
       ▼
2. SceneRegistry 调度到对应场景处理函数
       ▼
3. CustomerResolver 解析客户ID（从客户主数据表）
       ▼
4. LiveAdapter 拉取实时数据（明细表、档案、会议笔记等）
       ▼
5. ExpertCardLoader 加载场景的 expert-cards.yaml
       ▼
6. Input Review（关键词模式或 LLM 模式）
       ▼
7. ExpertAnalysisHelper 聚合证据，执行四/五维度分析
       ▼
8. 提取实体（关键人、行动计划、风险点等）
       ▼
9. SchemaPreflightRunner 预检目标表的字段
       ▼
10. Output Review（关键词模式或 LLM 模式）
       ▼
11. 生成 WriteCandidate（建议态的写回内容）
       ▼
12. ConfirmationChecklist 构建确认清单
       ▼
13. 展示建议，等待用户确认
       ▼
14. 用户确认后，TodoWriter / LiveAdapter 执行写回
       ▼
15. 返回 WriteExecutionResult（执行结果）
```

**关键设计点**：

- **Live-first Gate**：在会议相关场景中，必须先拉取实时数据，再做判断
- **Schema Preflight**：任何写回操作前，必须验证目标表和字段存在
- **Confirmation-first**：所有变更以建议态呈现，用户确认后才执行
- **Expert Review Gate**：input_review 在证据聚合前执行，output_review 在建议生成后执行
- **Circuit Breaker**：LLM 调用连续失败 5 次后自动降级
- **写回顺序**：先更新明细表，再更新档案文档，最后创建待办

## 关键设计原则

### 1. 实时优先（Live-first）

所有判断基于实时数据，而不是本地缓存或推测。每次执行都会先访问飞书 Base 获取最新状态。

### 2. 确认前置（Confirmation-first）

所有变更（无论是更新明细表、刷新档案还是创建待办）都以"建议态"呈现给用户。用户明确确认后，系统才会真正执行写回操作。

### 3. Schema 预检（Schema Preflight）

在任何写回操作之前，系统会检查目标表是否存在、目标字段是否存在且类型匹配。如果 Schema 校验失败，写回会被阻止并提示具体原因。

### 4. 受保护的主数据

客户主数据表是受保护的——只有特定字段（如联系方式、基本信息）允许更新，策略类字段的变更需要非常谨慎。

### 5. 实体分离

在输出中严格分离"事实"和"判断"——事实是来源于数据的客观记录，判断是基于证据的分析结论。这避免了将推测呈现为事实。

### 6. 单一档案原则

每个客户只能有一份权威的客户档案文档。如果存在多份，系统会提示去重，而不是盲目追加。

### 7. 专家代理安全

- agent-registry.yaml 是所有代理名称的**唯一真实来源**
- expert-cards.yaml 只能引用代理，不能定义代理
- 所有 agent_name 必须经过正则化（ lowercase、strip、字符过滤）后验证
- prompt_file 强制 .md 扩展，禁止 symlink，防止路径遍历

### 8. LLM 降级保活

任何 LLM 调用失败都触发降级到关键词模式，确保系统始终可用。熔断器模式防止持续失败导致的资源浪费。

## 目录结构

```
feishu-am-workbench/
├── runtime/                    # 核心运行时
│   ├── scene_runtime.py       # 场景执行引擎（主入口）
│   ├── scene_registry.py      # 场景注册与调度
│   ├── gateway.py              # 统一网关
│   ├── live_adapter.py        # 飞书实时数据访问适配器
│   ├── expert_analysis_helper.py  # 证据聚合与分析辅助
│   ├── expert_agent_invoker.py    # 专家代理调用编排器
│   ├── expert_card_loader.py      # 专家卡片 YAML 加载器
│   ├── default_llm_adapter.py     # OpenAI/Anthropic LLM 适配器
│   ├── models.py              # 数据模型定义
│   ├── confirmation_checklist.py  # 用户确认清单构建
│   ├── schema_preflight.py     # Schema 预检
│   ├── todo_writer.py          # 待办事项写入
│   ├── write_guard.py          # 写保护控制
│   ├── customer_resolver.py    # 客户ID解析
│   ├── semantic_registry.py    # 语义注册表
│   ├── runtime_sources.py      # 运行时资源加载
│   ├── resource_resolver.py    # 资源解析器
│   ├── lark_cli.py            # lark-cli 封装
│   ├── env_loader.py          # .env 文件加载
│   ├── diagnostics.py          # 运行时诊断
│   └── __main__.py            # CLI 入口
├── agents/                     # 专家代理提示词模板
│   ├── agent-registry.yaml     # 代理注册表（SOLE SOURCE OF TRUTH）
│   ├── sales-account-strategist.md
│   ├── customer-service.md
│   └── sales-proposal-strategist.md
├── scenes/                     # 场景定义
│   ├── post-meeting-synthesis/
│   │   └── expert-cards.yaml   # input + output 审核配置
│   ├── customer-recent-status/
│   │   └── expert-cards.yaml   # input 审核配置
│   └── ...                     # 其他场景目录
├── references/                 # 参考文档
│   ├── entity-extraction-schema.md    # 实体提取Schema
│   ├── master-data-guardrails.md      # 主数据保护规则
│   └── update-routing.md              # 更新路由规则
├── tests/                      # 测试套件
├── docs/                       # 文档
│   ├── ARCHITECTURE.md         # 本文档
│   └── loading-strategy.md     # 技能加载策略
├── SKILL.md                    # 技能定义
└── README.md                   # 项目概述
```

## 与飞书基础设施的集成

工作台通过 lark-cli 工具与飞书基础设施交互：

| 集成目标 | 访问方式 | 用途 |
|----------|----------|------|
| Base 多维表格 | lark-cli base query | 读写客户明细表 |
| 文档 | lark-cli doc | 读写客户档案、会议笔记 |
| 待办 | lark-cli todo | 创建和更新任务提醒 |
| 会议笔记 | lark-cli 通过文档层访问 | 恢复会议上下文 |

所有集成都通过 `LiveAdapter` 统一封装，底层调用 `LarkCliClient` 执行实际的 CLI 命令。
