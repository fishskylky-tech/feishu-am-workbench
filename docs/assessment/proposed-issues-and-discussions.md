# 待提交的 Issues 和 Discussions

本文档包含根据 [skill-standards-evaluation.md](./skill-standards-evaluation.md) 评估报告提出的改进建议，准备提交到 GitHub。

---

## GitHub Issues（共 8 个）

### Issue #1: [Security] 移除代码仓库中的敏感配置信息

**优先级**: P0
**标签**: `security`, `P0`, `immediate`

#### 描述
当前 `references/live-resource-links.md` 包含个人飞书资源的真实 URL 和资源 ID（包括 Base token、文件夹 token 及任务列表 GUID），存在安全风险。应将敏感配置移至环境变量或本地配置文件，并加入 `.gitignore`。

#### 当前问题
- `references/live-resource-links.md` 包含真实资源链接
- 资源 ID（Base token、文件夹 token 等）和 workspace 信息可能暴露
- 缺少 pre-commit hook 检查 secrets

#### 建议方案
1. 重命名 `live-resource-links.md` → `live-resource-links.example.md`（仅包含示例）
2. 创建 `.env.example` 模板
3. 真实配置通过 `.env` 或 `config/local.yaml` 提供
4. 更新 `.gitignore` 排除敏感文件
5. 更新 `runtime/runtime_sources.py` 支持从环境变量读取

#### Action Items
- [ ] 重命名 `references/live-resource-links.md` → `references/live-resource-links.example.md`
- [ ] 移除示例文件中的真实值，替换为占位符
- [ ] 创建 `.env.example` 模板
- [ ] 更新 `.gitignore` 添加 `.env`, `config/local.yaml`, `config/*.local.yaml`
- [ ] 更新 `runtime/runtime_sources.py` 优先从环境变量读取
- [ ] 添加 `.pre-commit-config.yaml` 配置 detect-secrets hook
- [ ] 更新 README.md 添加"安全配置指南"

#### 参考
- [SECURITY-MODEL.md](../../SECURITY-MODEL.md)
- 评估报告: 维度 10 - 安全性和数据保护

---

### Issue #2: [Structure] 进一步精简 SKILL.md 以提升跨平台兼容性（目标 <2,000 tokens）

**优先级**: P1
**标签**: `documentation`, `structure`, `skill-compliance`

#### 描述
根据 Google ADK 和 Anthropic skills 标准，L2 层指令应保持在 5,000 tokens 以内。当前 SKILL.md 主体约 2,063 词（估计 2,750+ tokens），已满足该限制；本 Issue 的目标是进一步精简至更易移植的规模（如 <2,000 tokens），以提升在不同 agent 平台上的兼容性。

#### 当前状态
- SKILL.md 主体: ~2,063 词
- 包含大量详细规则和指导
- 部分内容适合移至 references/ (L3 层)

#### 改进目标
- 精简 SKILL.md 主体至 <2,000 tokens
- 保留核心工作流和关键原则
- 详细规则移至 references/

#### 建议调整

**保留在 SKILL.md (L2)**:
- Runtime Prerequisites
- Use This Skill When
- Core Workflow（精简版）
- Hard Rules（仅核心清单，不展开细节）
- Output Pattern（简化版）
- Write Order
- Scope

**移至新文档 `references/core-hard-rules.md` (L3)**:
- Hard Rules 的详细展开（约 50+ 条详细规则）
- 每条规则的 why 和边界说明

**移至其他 references/ (L3)**:
- Extraction First 详情 → `entity-extraction-schema.md` (已存在)
- Read These References As Needed → 保留简化版导航

#### Action Items
- [ ] 创建 `references/core-hard-rules.md` 整合详细硬规则
- [ ] 精简 SKILL.md "Hard Rules" 部分为核心清单
- [ ] 精简 "Core Workflow" 为步骤列表，细节链接到 references
- [ ] 优化 "Output Pattern" 为结构模板，详情移至 `meeting-output-standard.md`
- [ ] 在 SKILL.md 顶部添加 L1/L2/L3 分层说明
- [ ] 更新 `references/INDEX.md` 添加 `core-hard-rules.md`
- [ ] 验证精简后 token 数 <2,000

#### 参考
- AgentSkills.io 规范: L2 层 <5,000 tokens
- 评估报告: 维度 1 - Skill 结构规范性

---

### Issue #3: [Metadata] 补全 SKILL.md frontmatter 标准字段

**优先级**: P1
**标签**: `metadata`, `skill-compliance`

#### 描述
根据 AgentSkills.io 标准，skill frontmatter 应包含完整的元数据以便 agent 平台发现和加载。当前缺少 `version`, `author`, `tags`, `license` 等推荐字段。

#### 当前 frontmatter
```yaml
---
name: feishu-am-workbench
description: >
  Personal AM workflow skill for Feishu-based account management. ...
compatibility: requires lark-cli in PATH; Python 3.10+ for runtime/ modules; personal Feishu token configured in environment
---
```

#### 建议补全
```yaml
---
name: feishu-am-workbench
version: 0.1.0  # 从 VERSION 文件同步
author: fishskylky-tech
description: >
  Personal AM workflow skill for Feishu-based account management.
  Use when user mentions: 客户档案, 会议纪要, 行动计划, etc.
tags: [feishu, account-management, am-workflow, chinese, crm, pipeline]
license: MIT  # 或其他合适的许可证
repository: https://github.com/fishskylky-tech/feishu-am-workbench
compatibility: requires lark-cli in PATH; Python 3.10+; Feishu access token
load_strategy: progressive
tier:
  L1: frontmatter + core_workflow
  L2: main body
  L3: references/*.md (on-demand)
---
```

#### Action Items
- [ ] 添加 `version` 字段（从 VERSION 文件读取）
- [ ] 添加 `author: fishskylky-tech`
- [ ] 添加 `tags: [feishu, account-management, am-workflow, chinese, crm, pipeline]`
- [ ] 选择并添加 `license` 字段
- [ ] 添加 `repository` URL
- [ ] 添加 `load_strategy: progressive`
- [ ] 添加 `tier` 说明 L1/L2/L3 边界
- [ ] 考虑添加 `triggers` 元数据（关键词和模式）
- [ ] 更新 CHANGELOG.md 记录元数据变更

#### 可选增强
```yaml
triggers:
  keywords: [飞书工作台, 客户档案, 会议纪要, 行动计划, Todo, 客户更新]
  patterns: [meeting prep, post-meeting, account analysis, customer update]
  file_types: [transcript, meeting notes, customer materials]
```

#### 参考
- AgentSkills.io metadata 规范
- 评估报告: 维度 2 - Skill 元数据完整性

---

### Issue #4: [Architecture] 建立明确的 L1/L2/L3 渐进式披露边界

**优先级**: P1
**标签**: `architecture`, `progressive-disclosure`, `skill-compliance`

#### 描述
根据 Google ADK skills 标准，应实现三层渐进式披露（L1: metadata, L2: instructions, L3: resources）以最小化 agent 上下文窗口占用。当前虽有 21 个 reference 文档作为 L3 层，但缺少明确的加载层级和技术层面的按需加载机制。

#### 当前问题
1. SKILL.md 中 "Read These References As Needed" 是文档约定，依赖 agent 自律
2. 21 个 reference 文档未明确加载优先级
3. 无技术手段保证不预加载所有文档
4. 在不支持渐进式加载的平台上可能超出上下文窗口

#### 建议方案

**1. 在 SKILL.md 添加显式分层标注**
```markdown
## Skill Loading Tiers

### L1: Metadata (~100 tokens)
Always loaded by the agent platform.
- Frontmatter: name, description, compatibility, tags, version

### L2: Core Instructions (<2,000 tokens)
Loaded when skill is activated.
- Runtime Prerequisites
- Core Workflow (simplified)
- Hard Rules (checklist only)
- Output Pattern (template only)

### L3: Extended References (on-demand)
Loaded only when needed based on task context.

#### Always Load First (if accessing Feishu)
- [feishu-workbench-gateway.md] - Feishu resource access protocol

#### Load by Scenario
- **Meeting tasks**: meeting-context-recovery, meeting-type-classification, meeting-output-standard
- **Write operations**: live-schema-preflight, schema-compatibility, update-routing
- **Customer operations**: customer-archive-rules, master-data-guardrails
- **Extraction tasks**: entity-extraction-schema, fact-grading

#### Load on Demand (when specific conditions met)
- All other references/ documents
```

**2. 为每个 reference 文档添加加载元数据**

在每个 `references/*.md` 文件顶部添加 frontmatter:

```yaml
---
# meeting-context-recovery.md
title: Meeting Context Recovery
load_triggers:
  - user_input_contains: [会议, meeting, transcript, 纪要]
  - skill_stage: [meeting-prep, post-meeting]
  - task_type: [meeting-note, meeting-analysis]
load_priority: high  # high | medium | low
estimated_tokens: 800
dependencies: [feishu-workbench-gateway, customer-archive-rules]
---
```

**3. 优化 references/INDEX.md**

添加"加载策略"列:

| File | Summary | When to Load | Priority | Est. Tokens |
|------|---------|-------------|----------|-------------|
| feishu-workbench-gateway.md | Unified gateway | Always (if Feishu) | Critical | 600 |
| meeting-context-recovery.md | Context recovery | Meeting tasks | High | 800 |
| entity-extraction-schema.md | Extraction bundle | All tasks | High | 1000 |
| task-patterns.md | Common playbooks | Known task types | Medium | 600 |
| ... | ... | ... | ... | ... |

#### Action Items
- [ ] 在 SKILL.md 添加 "Skill Loading Tiers" 章节（如上）
- [ ] 为所有 21 个 reference 文档添加 frontmatter（加载元数据）
- [ ] 更新 `references/INDEX.md` 添加"加载策略"相关列
- [ ] 估算每个文档的 token 数
- [ ] 在 ARCHITECTURE.md 说明渐进式披露设计
- [ ] 创建加载策略文档 `docs/loading-strategy.md`
- [ ] 验证总 token 预算合理性

#### 未来增强（可选）
- 实现技术层加载器（读取 frontmatter，按需加载）
- 支持 agent 平台的 progressive loading API
- 添加 token 预算监控

#### 参考
- Google ADK Skills Guide: Progressive Disclosure
- AgentSkills.io: Three-tier loading
- 评估报告: 维度 4 - 渐进式披露实施

---

### Issue #5: [Portability] 实现 workspace 配置层抽象

**优先级**: P1
**标签**: `portability`, `configuration`, `architecture`

#### 描述
当前 skill 高度个人化（"only for you"），个人资源硬编码在文档中，限制了在不同飞书 workspace 或给其他 AM 使用的能力。根据 ROADMAP M4 规划，需要实现配置与代码分离，建立 workspace 配置层抽象。

#### 当前问题
- `references/live-resource-links.md` 包含个人特定资源
- `runtime/semantic_registry.py` 中字段映射硬编码
- STATUS.md 指出 "目前只覆盖你当前个人环境"
- 难以在其他飞书 workspace 部署

#### 改进目标
- 配置与代码分离
- 支持多 workspace 环境
- 提供标准化部署流程
- 保持个人使用的便利性

#### 建议方案

**1. 设计 workspace 配置模板**

创建 `config/workspace.example.yaml`:

```yaml
# Feishu AM Workbench - Workspace Configuration Template
workspace:
  name: "{{workspace_name}}"
  owner: "{{owner_name}}"

feishu:
  # 从环境变量读取
  base_token: "${FEISHU_AM_BASE_TOKEN}"
  app_id: "${FEISHU_APP_ID}"  # 可选

tables:
  customer_master:
    table_id: "{{customer_master_table_id}}"
    semantic_slots:
      customer_id: "客户ID"
      customer_short_name: "简称"
      archive_link: "客户档案"
      # ... 其他字段映射

  contact_records:
    table_id: "{{contact_records_table_id}}"
    # ...

folders:
  customer_archive:
    token: "{{archive_folder_token}}"
    name: "客户档案"

  meeting_notes:
    token: "{{meeting_notes_folder_token}}"
    name: "会议纪要"

todo:
  tasklist_guid: "{{tasklist_guid}}"
  custom_fields:
    customer: "{{customer_field_guid}}"
    priority: "{{priority_field_guid}}"
  priority_options:
    - name: "高"
      guid: "{{high_priority_guid}}"
    - name: "中"
      guid: "{{medium_priority_guid}}"
    - name: "低"
      guid: "{{low_priority_guid}}"

# 字段别名（可选，用于兼容性）
field_aliases:
  customer_master:
    customer_id: ["客户ID", "客户编号", "CustomerID"]
    customer_short_name: ["简称", "客户简称", "ShortName"]
  # ...
```

**2. 创建部署脚本**

创建 `scripts/setup.sh`:

```bash
#!/bin/bash
# Feishu AM Workbench Setup Script

echo "=== Feishu AM Workbench 配置向导 ==="

# 1. 检查依赖
check_dependencies() {
    # 检查 lark-cli, python3.10+
}

# 2. 引导用户配置
configure_workspace() {
    echo "请输入 workspace 名称:"
    read workspace_name
    # ... 收集其他配置
}

# 3. 生成配置文件
generate_config() {
    cp config/workspace.example.yaml config/local.yaml
    # 替换占位符
}

# 4. 运行诊断
python3 -m runtime .

echo "✅ 配置完成！"
```

**3. 更新 runtime 加载逻辑**

更新 `runtime/runtime_sources.py`:

```python
def load_from_workspace_config(config_path: str) -> RuntimeSources:
    """从 workspace.yaml 加载配置"""
    # 读取 YAML
    # 解析环境变量
    # 返回 RuntimeSources
```

#### Action Items
- [ ] 设计 `config/workspace.example.yaml` 模板（参考 CONFIG-MODEL.md）
- [ ] 创建 `config/local.example.yaml` 用于本地开发
- [ ] 实现 `runtime/config_loader.py` 解析 workspace 配置
- [ ] 更新 `runtime/runtime_sources.py` 支持从配置文件加载
- [ ] 创建 `scripts/setup.sh` 部署脚本
- [ ] 更新 `.gitignore` 排除 `config/local.yaml`, `config/*.local.yaml`
- [ ] 更新 README.md 添加 "多环境部署" 章节
- [ ] 创建 `docs/deployment-guide.md` 详细部署文档
- [ ] 保持向后兼容：优先从 config 读取，fallback 到现有方式

#### 多环境支持（未来）
```
config/
├── workspace.example.yaml    # 模板
├── local.example.yaml         # 本地开发示例
├── dev.yaml                   # 开发环境（可选）
├── staging.yaml               # 预发环境（可选）
└── prod.yaml                  # 生产环境（可选）
```

通过环境变量切换:
```bash
export FEISHU_WORKSPACE_CONFIG=config/staging.yaml
python3 -m runtime .
```

#### 参考
- [CONFIG-MODEL.md](../../CONFIG-MODEL.md)
- ROADMAP M4: 降低硬编码，增强兼容性
- 评估报告: 维度 9 - 兼容性和可移植性

---

### Issue #6: [Documentation] 创建架构可视化图和快速上手指南

**优先级**: P2
**标签**: `documentation`, `usability`, `onboarding`

#### 描述
当前文档体系虽然完整，但缺少可视化架构图和"5 分钟快速上手"指南，新贡献者门槛较高。ARCHITECTURE.md 中有 mermaid 图但未导出为图片，README.md 缺少直观的架构概览。

#### 当前问题
- mermaid 图仅在 Markdown 中，GitHub 以外平台可能不渲染
- 缺少数据流图、调用链可视化
- 无快速上手指南
- 新贡献者需要阅读大量文档才能理解架构

#### 改进目标
- 导出架构图为独立图片
- 创建直观的可视化文档
- 提供 5 分钟快速上手路径
- 降低新贡献者门槛

#### 建议内容

**1. 架构图可视化**

导出 ARCHITECTURE.md 中的图为 PNG/SVG:
- `docs/images/architecture-overview.png` - 6 层架构总览
- `docs/images/gateway-components.png` - 飞书工作台底座 4 组件
- `docs/images/meeting-sequence.png` - 会议场景调用链

**2. 补充新图**
- `docs/images/data-flow.png` - 数据流图
- `docs/images/write-pipeline.png` - 写回流程图
- `docs/images/skill-loading-tiers.png` - L1/L2/L3 加载层级

**3. 创建快速上手指南**

`docs/quickstart.md`:

```markdown
# 5 分钟快速上手

## 前提条件
- ✅ lark-cli 已安装并认证
- ✅ Python 3.10+
- ✅ 有权限访问目标飞书 Base/文档/Todo

## 步骤 1: 环境诊断 (1 分钟)
\`\`\`bash
python3 -m runtime .
\`\`\`

预期输出:
- base_access: available ✅
- docs_access: available ✅
- task_access: available ✅

## 步骤 2: 配置环境 (2 分钟)
\`\`\`bash
# 复制配置模板
cp config/workspace.example.yaml config/local.yaml

# 编辑 config/local.yaml，填入你的资源 ID
# 或使用设置脚本
bash scripts/setup.sh
\`\`\`

## 步骤 3: 运行示例 (2 分钟)
\`\`\`bash
python3 -m evals.meeting_output_bridge \
  --eval-name quickstart-test \
  --transcript-file tests/fixtures/transcripts/20260410-联合利华\ Campaign活动分析优化-阶段汇报.txt \
  --run-gateway \
  --customer-query 联合利华
\`\`\`

## 下一步
- 📖 阅读 [SKILL.md](../SKILL.md) 了解核心工作流
- 🏗️ 阅读 [ARCHITECTURE.md](../ARCHITECTURE.md) 了解架构设计
- 📚 浏览 [references/INDEX.md](../references/INDEX.md) 了解所有参考文档
```

**4. 更新 README.md**

在顶部添加架构图:
```markdown
## 架构概览

![Architecture Overview](docs/images/architecture-overview.png)

feishu-am-workbench 采用 6 层架构...
```

#### Action Items
- [ ] 使用 mermaid-cli 或在线工具导出现有图为 PNG/SVG
- [ ] 创建 `docs/images/` 目录存放架构图
- [ ] 绘制数据流图、写回流程图
- [ ] 创建 `docs/quickstart.md` 快速上手指南
- [ ] 更新 README.md 添加架构图和快速上手链接
- [ ] 创建 `docs/contributing.md` 贡献者指南
- [ ] 在 references/INDEX.md 添加可视化辅助

#### 工具推荐
- mermaid-cli: `npm install -g @mermaid-js/mermaid-cli`
- 在线工具: https://mermaid.live

#### 参考
- 评估报告: 维度 8 - 文档和可维护性

---

### Issue #7: [Runtime] 将 Context Hydrator 独立为 runtime/ 层通用组件

**优先级**: P2
**标签**: `runtime`, `refactoring`, `architecture`

#### 描述
根据 ARCHITECTURE.md 设计，飞书工作台底座应包含 4 个内部能力，其中 Context Hydrator 负责为需要深度解释的场景补齐上下文。当前实现分散在 `evals/meeting_output_bridge.py` 中，应抽象为 runtime/ 层的通用组件。

#### 当前问题
- Context Hydrator 逻辑在 `meeting_output_bridge.py` 中
- 未形成可复用的独立组件
- 其他场景（会前准备、客户分析）难以复用

#### 改进目标
- 独立 `runtime/context_hydrator.py`
- 定义清晰的接口和数据模型
- 支持多级恢复（minimal, standard, full）
- 供多个场景复用

#### 建议设计

**1. 创建数据模型**

在 `runtime/models.py` 添加:

```python
@dataclass
class HydrationScope:
    level: Literal["minimal", "standard", "full"]
    include_master: bool = True
    include_contacts: bool = False
    include_actions: bool = False
    include_contracts: bool = False
    include_archive_content: bool = False
    include_meeting_history: bool = False
    contact_limit: int = 5
    action_limit: int = 10
    meeting_limit: int = 5

@dataclass
class HydrationResult:
    customer_id: str
    level: Literal["minimal", "standard", "full"]
    status: Literal["completed", "partial", "failed"]
    master_data: dict[str, Any] | None = None
    recent_contacts: list[dict[str, Any]] = field(default_factory=list)
    recent_actions: list[dict[str, Any]] = field(default_factory=list)
    contracts: list[dict[str, Any]] = field(default_factory=list)
    archive_link: str | None = None
    archive_content: str | None = None
    meeting_history: list[dict[str, Any]] = field(default_factory=list)
    sources_used: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
```

**2. 创建 Context Hydrator**

创建 `runtime/context_hydrator.py`:

```python
class ContextHydrator:
    """Hydrate customer context for deep analysis scenarios."""

    def __init__(
        self,
        client: LarkCliClient,
        config: LiveWorkbenchConfig,
        adapter: LarkCliSchemaBackend,
    ):
        self.client = client
        self.config = config
        self.adapter = adapter

    def hydrate(
        self,
        customer_id: str,
        scope: HydrationScope
    ) -> HydrationResult:
        """
        Hydrate customer context based on scope.

        Scope levels:
        - minimal: 客户主数据 only
        - standard: + 最近联系记录 + 行动计划
        - full: + 档案正文 + 历史会议纪要
        """
        result = HydrationResult(customer_id=customer_id, level=scope.level)

        # Stage 1: Master data
        if scope.include_master:
            result.master_data = self._load_master_data(customer_id)

        # Stage 2: Recent records
        if scope.include_contacts:
            result.recent_contacts = self._load_recent_contacts(
                customer_id, scope.contact_limit
            )

        if scope.include_actions:
            result.recent_actions = self._load_recent_actions(
                customer_id, scope.action_limit
            )

        # Stage 3: Archive
        if scope.include_archive_content and result.master_data:
            archive_link = result.master_data.get("archive_link")
            if archive_link:
                result.archive_content = self._load_archive_content(archive_link)

        # Stage 4: Meeting history
        if scope.include_meeting_history:
            result.meeting_history = self._load_meeting_history(
                customer_id, scope.meeting_limit
            )

        result.status = self._determine_status(result)
        return result

    @classmethod
    def for_live_lark_cli(cls, repo_root: str) -> "ContextHydrator":
        sources = RuntimeSourceLoader(repo_root).load()
        config = LiveWorkbenchConfig.from_sources(sources)
        client = LarkCliClient()
        adapter = LarkCliSchemaBackend(client, config)
        return cls(client, config, adapter)
```

**3. 定义预设 Scope**

```python
# runtime/context_hydrator.py

MINIMAL_SCOPE = HydrationScope(
    level="minimal",
    include_master=True,
)

STANDARD_SCOPE = HydrationScope(
    level="standard",
    include_master=True,
    include_contacts=True,
    include_actions=True,
    contact_limit=5,
    action_limit=10,
)

FULL_SCOPE = HydrationScope(
    level="full",
    include_master=True,
    include_contacts=True,
    include_actions=True,
    include_archive_content=True,
    include_meeting_history=True,
    contact_limit=10,
    action_limit=20,
    meeting_limit=5,
)
```

**4. 更新 meeting_output_bridge.py**

```python
# 旧代码：直接调用 adapter
# contacts = adapter.query_customer_contacts(customer_id, limit=5)

# 新代码：使用 ContextHydrator
from runtime.context_hydrator import ContextHydrator, STANDARD_SCOPE

hydrator = ContextHydrator.for_live_lark_cli(repo_root)
hydration = hydrator.hydrate(customer_id, STANDARD_SCOPE)

# 使用结果
recent_contacts = hydration.recent_contacts
recent_actions = hydration.recent_actions
```

#### Action Items
- [ ] 在 `runtime/models.py` 添加 `HydrationScope`, `HydrationResult` 数据模型
- [ ] 创建 `runtime/context_hydrator.py`
- [ ] 实现 `ContextHydrator` 类及核心方法
- [ ] 定义 MINIMAL_SCOPE, STANDARD_SCOPE, FULL_SCOPE 预设
- [ ] 更新 `evals/meeting_output_bridge.py` 使用新组件
- [ ] 添加单元测试 `tests/test_context_hydrator.py`
- [ ] 更新 ARCHITECTURE.md 说明 Context Hydrator 实现
- [ ] 更新 `runtime/README.md` 添加 Context Hydrator 说明

#### 未来增强
- 支持并行加载（异步 I/O）
- 缓存机制（避免重复查询）
- 增量更新（只加载变化部分）

#### 参考
- ARCHITECTURE.md: 4.2 Context Hydrator
- 评估报告: 维度 6 - 运行时层架构

---

### Issue #8: [Testing] 增强自动化回归测试和 CI/CD 集成

**优先级**: P2
**标签**: `testing`, `ci-cd`, `automation`

#### 描述
当前虽有 3 个真实案例用于回归验证，但主要依赖手工执行和人工判定。需要增强 `evals/runner.py` 支持批量自动化执行，并集成 CI/CD 流程，确保每次代码变更都能自动验证。

#### 当前问题
- 验证主要靠手工执行和文档记录
- `evals/runner.py` 存在但未充分使用
- 无自动化 CI/CD 流程
- 测试覆盖率未量化

#### 改进目标
- 自动化 3 个真实案例的回归测试
- CI/CD 集成（GitHub Actions）
- 量化测试覆盖率
- 每次 PR 自动验证

#### 建议方案

**1. 增强 evals/runner.py**

支持批量执行和结构化断言:

```python
# evals/runner.py

class ValidationRunner:
    def run_all_cases(self) -> ValidationReport:
        """运行所有 evals.json 中的案例"""
        cases = self.load_cases_from_json()
        results = []

        for case in cases:
            result = self.run_case(case)
            results.append(result)

        return ValidationReport(results=results)

    def run_case(self, case: EvalCase) -> CaseResult:
        """运行单个案例并执行断言"""
        # 执行 meeting_output_bridge
        output = self.execute_bridge(case)

        # 执行断言
        assertions = self.check_assertions(output, case.expected)

        return CaseResult(
            case_name=case.name,
            passed=all(a.passed for a in assertions),
            assertions=assertions,
        )
```

添加命令行接口:
```bash
# 运行所有案例
python3 -m evals.runner --all

# 运行特定案例
python3 -m evals.runner --case unilever-campaign

# 生成报告
python3 -m evals.runner --all --report validation-report.md
```

**2. 创建 GitHub Actions 工作流**

创建 `.github/workflows/validation.yml`:

```yaml
name: Skill Validation

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          # 安装 lark-cli（如果有安装脚本）

      - name: Run diagnostic
        run: python3 -m runtime .

      - name: Run validation suite
        run: python3 -m evals.runner --all --report validation-report.md
        env:
          # 使用测试环境配置（不含真实数据）
          FEISHU_WORKSPACE_CONFIG: config/test.yaml

      - name: Upload validation report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: validation-report
          path: validation-report.md

      - name: Comment PR with results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('validation-report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## Validation Report\n\n${report}`
            });
```

**3. 添加测试覆盖率**

创建 `.github/workflows/test-coverage.yml`:

```yaml
name: Test Coverage

on:
  pull_request:
  push:
    branches: [main]

jobs:
  coverage:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests with coverage
        run: |
          python3 -m pytest tests/ \
            --cov=runtime \
            --cov=evals \
            --cov-report=xml \
            --cov-report=html \
            --cov-report=term

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

      - name: Check coverage threshold
        run: |
          # 要求 runtime/ 覆盖率 >80%
          coverage report --fail-under=80
```

**4. 更新 evals.json 添加断言**

```json
{
  "version": "0.1.0",
  "cases": [
    {
      "name": "unilever-campaign-phase-report",
      "transcript_file": "tests/fixtures/transcripts/20260410-联合利华 Campaign活动分析优化-阶段汇报.txt",
      "customer_query": "联合利华",
      "expected": {
        "gateway_executed": true,
        "customer_resolved": true,
        "context_status": "completed",
        "meeting_type": "探索型阶段汇报",
        "write_ceiling": "recommendation_only",
        "has_facts_section": true,
        "has_judgment_section": true,
        "has_open_questions": true,
        "no_auto_todo_creation": true,
        "relative_dates_converted": true
      }
    },
    // ... 其他案例
  ]
}
```

#### Action Items
- [ ] 增强 `evals/runner.py` 支持批量执行和结构化断言
- [ ] 更新 `evals/evals.json` 添加每个案例的 expected 断言
- [ ] 创建 `.github/workflows/validation.yml` 自动化验证
- [ ] 创建 `.github/workflows/test-coverage.yml` 覆盖率检查
- [ ] 添加 `pytest` 和 `pytest-cov` 到 requirements
- [ ] 设置覆盖率目标: runtime/ >80%
- [ ] 创建 `config/test.yaml` 测试环境配置
- [ ] 在 README.md 添加 CI/CD 状态徽章
- [ ] 创建 `docs/testing-guide.md` 测试指南

#### 覆盖率目标
- runtime/: >80%
- evals/: >70%
- tests/: >90%

#### 参考
- VALIDATION.md: 验证协议
- 评估报告: 维度 7 - 验证和质量保障

---

## GitHub Discussions（共 2 个）

### Discussion #1: 如何与 agentskills.io 标准对齐并增强可移植性？

**类别**: Architecture & Standards

#### 背景
本技能在架构设计和运行时实现方面非常优秀，但在标准化结构和可移植性方面与 ADK/Anthropic skills 标准存在差距。根据评估报告（详见 `docs/assessment/skill-standards-evaluation.md`），总体得分 8.13/10，主要差距在于：

1. **结构标准化**: SKILL.md 需要精简，建立明确的 L1/L2/L3 边界
2. **可移植性**: 当前高度个人化，限制了跨环境部署
3. **渐进式披露**: 缺少技术层面的按需加载机制

#### 讨论要点

**1. 渐进式披露实施**

问题：
- 当前 21 个 reference 文档通过文档约定 "Read These References As Needed"，依赖 agent 自律
- 在不支持渐进式加载的平台（如某些自定义 agent）上可能预加载所有文档
- 需要技术层面的保证机制

方案 A: 依赖 agent 平台能力
- 为每个 reference 添加加载元数据（frontmatter）
- 依赖 agent 平台解析并按需加载
- 优点：简单，不改变现有结构
- 缺点：依赖平台支持

方案 B: 实现自定义加载器
- 在 runtime/ 中实现 `reference_loader.py`
- 根据任务上下文动态加载文档
- 优点：完全可控
- 缺点：增加复杂度

方案 C: 混合方案
- 提供元数据供兼容平台使用
- 同时提供可选的加载器实现
- 优点：灵活性高
- 缺点：维护成本略高

**社区提问**:
- 你们认为哪种方案更合理？
- 在实际使用中，agent 是否会预加载所有 references？
- 有没有其他技能的最佳实践可参考？

---

**2. 配置抽象和可移植性**

问题：
- ROADMAP M4 规划 "降低硬编码，增强兼容性"
- 但当前明确定位为 "personal workflow skill"
- 如何平衡个人使用便利性和通用化？

方案 A: 激进通用化
- 立即实现完整的 workspace config 抽象
- 提供标准化部署流程
- 优点：符合开放标准
- 缺点：可能影响当前个人使用体验

方案 B: 渐进式通用化
- 先实现配置层，但保持现有 fallback
- 优先保证个人使用不受影响
- 逐步添加多环境支持
- 优点：平稳过渡
- 缺点：过渡期维护两套逻辑

方案 C: 双轨制
- 保留 "personal mode" 作为默认
- 提供 "shared mode" 供团队使用
- 优点：清晰分离
- 缺点：代码复杂度增加

**社区提问**:
- 个人使用 vs 团队复用，如何平衡？
- workspace.yaml 模板设计是否合理？（见 Issue #5）
- 是否有类似场景的参考案例？

---

**3. 标准对齐优先级**

问题：
- 与 agentskills.io 标准对齐 vs 个人使用价值提升
- ROADMAP 中优先级排序是否合理？

当前优先级:
1. M1 稳定化与查漏补缺
2. M2 经营闭环增强
3. M3 复杂输入深度解读
4. M4 降低硬编码，增强兼容性（标准对齐在这里）

替代优先级:
1. M1 稳定化 + **标准对齐**（结构、元数据）
2. M2 经营闭环增强
3. M3 复杂输入深度解读
4. M4 完整通用化

**社区提问**:
- 是否应该提前标准对齐的优先级？
- 标准化是否会带来足够的长期价值？
- 如何量化标准对齐的收益？

---

**4. 社区复用和发布**

问题：
- 是否计划将此技能发布到社区仓库（skills.sh, agentskills.io）？
- 是否将 runtime/ 层抽象为独立包供其他技能使用？

潜在收益：
- 成为复杂技能设计的参考实现
- runtime/ 中的 schema preflight, write guard 等组件可复用
- 社区反馈改进质量

潜在成本：
- 需要更完整的文档和示例
- 需要持续维护和支持
- 可能暴露设计细节

**社区提问**:
- 是否有兴趣发布到社区？
- runtime/ 组件独立化的优先级？
- 有没有类似的成功案例？

---

#### 相关资源
- 评估报告: `docs/assessment/skill-standards-evaluation.md`
- Google ADK Skills Guide: https://developers.googleblog.com/developers-guide-to-building-adk-agents-with-skills/
- AgentSkills.io: https://agentskills.io/home
- Anthropic Skills Repository: https://github.com/anthropics/skills

---

### Discussion #2: Skill 设计模式的深度应用和扩展

**类别**: Design Patterns & Best Practices

#### 背景
当前技能已优秀应用 **Pipeline + Reviewer + Inversion** 模式组合，非常适合 AM 工作流场景。根据评估报告，设计模式应用得分 9/10，但仍有优化和扩展空间。

#### 当前模式应用

**1. Pipeline 模式** (主模式)
```
输入 → 场景识别 → 抽取 → 判断 → 路由 → 建议 → 确认 → 写回
```
- ✅ 明确的检查点
- ✅ 结构化的阶段输出
- ✅ 可审计的决策链

**2. Reviewer 模式** (质量门)
- ✅ fact-grading: 分级事实 vs 判断
- ✅ schema-preflight: 写前安全检查
- ✅ write-guard: 最终写入保护

**3. Inversion 模式** (风险缓解)
- ✅ 会前准备: 先恢复上下文，再给建议
- ✅ 写回确认: "先建议，后确认"

**未充分应用**:
- ⚠️ Tool Wrapper: lark-cli 包装较薄
- ❌ Generator: 无独立的格式化输出组件

#### 讨论要点

**1. Generator 模式补充**

问题：
- 当前有 `meeting-output-standard.md` 定义输出格式
- 但未形成独立的 "格式化内容生成器" 组件
- 是否需要补充 Generator 模式？

建议设计：
```python
# formatters/meeting_summary.py
class MeetingSummaryGenerator:
    def generate(self, context: MeetingContext) -> str:
        """生成标准化会议摘要"""
        # 按 meeting-output-standard.md 格式生成

# formatters/customer_report.py
class CustomerReportGenerator:
    def generate(self, customer_id: str, analysis: dict) -> str:
        """生成客户经营分析卡"""
```

优点：
- 输出格式一致性
- 易于测试和迭代
- 可独立演进

缺点：
- 增加代码复杂度
- 格式本身可能频繁变化

**社区提问**:
- 是否需要独立的 Generator 组件？
- 还是保持现有的文档驱动格式？
- 有没有类似场景的最佳实践？

---

**2. 复杂输入深度解读模式设计**

ROADMAP M3 规划的 "复杂输入深度解读模式"，设计思路：

三阶段专家解读流程:
1. **事实抽取**: 只抽可见事实，不做过度推断
2. **经营解读**: AM 专家视角判断信号、风险、机会
3. **写回决策**: 决定哪些进主数据、明细表、档案、Todo

这是一个新的模式组合吗？还是现有模式的变体？

可能的模式归类：
- Pipeline 变体（三阶段 pipeline）
- Reviewer 增强版（深度审读）
- 混合模式（Pipeline + Reviewer + Domain Expert）

**社区提问**:
- 如何最好地设计这个"深度解读"模式？
- 是否有类似的 domain-expert pattern？
- 如何避免 over-engineering？

---

**3. Tool Wrapper 模式深化**

当前 `runtime/lark_cli.py` 是对 lark-cli 的薄包装：
```python
class LarkCliClient:
    def invoke_json(self, args: list[str]) -> dict:
        # 调用 lark-cli，返回 JSON
```

是否需要更厚的抽象层？

方案 A: 保持薄包装
- 优点：简单，直接
- 缺点：与 lark-cli 强耦合

方案 B: 抽象 Feishu API 接口
```python
class FeishuClient(ABC):
    @abstractmethod
    def get_base_table(...) -> Table: ...

class LarkCliFeishuClient(FeishuClient):
    # lark-cli 实现

class SDKFeishuClient(FeishuClient):
    # 官方 SDK 实现
```
- 优点：可切换后端
- 缺点：过度设计？

方案 C: 混合方案
- 保持 lark-cli 为主要实现
- 提供接口抽象但不强制
- 优点：灵活
- 缺点：设计边界模糊

**社区提问**:
- 是否需要抽象 Feishu API 接口？
- 还是继续依赖 lark-cli？
- 有没有切换后端的真实需求？

---

**4. 模式组合优化建议**

当前 Pipeline + Reviewer + Inversion 组合非常适合当前场景，但如果要扩展到更多场景（如 ROADMAP M2 的主动分析、M6 的多源输入），可能需要新模式。

潜在新模式：
- **Orchestrator 模式**: 协调多个子 agent 处理不同输入源
- **Aggregator 模式**: 汇总多个来源的信号
- **Monitor 模式**: 主动扫描和提醒

**社区提问**:
- 哪些新模式最适合未来演进？
- 如何避免模式过度膨胀？
- 有没有 multi-source aggregation 的参考案例？

---

#### 相关资源
- 评估报告: `docs/assessment/skill-standards-evaluation.md` 维度 5
- Google ADK 设计模式: https://lavinigam.com/posts/adk-skill-design-patterns/
- Anthropic Agent Design Patterns: https://haruiz.github.io/blog/implementing-anthropic's-agent-design-patterns-with-google-adk
- ROADMAP M3: 复杂输入深度解读模式

---

## 提交清单

准备提交时，请确认：

### Issues
- [ ] 所有 8 个 Issues 内容完整
- [ ] 优先级标签正确（P0/P1/P2）
- [ ] Action Items 清单明确
- [ ] 参考链接有效

### Discussions
- [ ] 两个 Discussions 主题明确
- [ ] 讨论要点具体
- [ ] 社区提问开放且有价值
- [ ] 相关资源链接完整

### 其他
- [ ] 评估报告已提交: `docs/assessment/skill-standards-evaluation.md`
- [ ] 本文档已提交: `docs/assessment/proposed-issues-and-discussions.md`
- [ ] CHANGELOG.md 已更新（如需要）

---

**生成时间**: 2026-04-12
**评估报告**: [skill-standards-evaluation.md](./skill-standards-evaluation.md)
