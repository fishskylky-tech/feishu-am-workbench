# AGENTS.md

**核心原则：** live-first（实时数据优先）+ recommendation-first（建议态确认后再行动）。

**Last Updated:** 2026-04-19

---

本文档描述了在 Feishu AM Workbench skill 关键决策点可调用的专家角色。Skill 可被 OpenClaw、Hermes、Codex 等 Agent 调用。

## 角色架构

Skill 采用"活页夹"（loose-leaf binder）模式管理专家角色。每个专家定义在独立配置文件中，在 skill 遇到特定输入/输出边界点时按需加载。

专家角色**不硬编码**到场景逻辑中。它们在关键检查点作为审核者被调用：

- **输入检查点**：用户材料在分析前由领域专家审核
- **输出检查点**：建议在交付前由经营顾问审核

## LLM-Based Expert Review

The skill supports two expert review modes:

1. **Keyword-Based Audit** (existing): Uses check_signals to match keywords in evidence
2. **LLM-Based Expert Review** (new): Uses AI-driven review with prompts from `agents/` directory

### How LLM Mode Works

When an expert card has `prompt_file` field set:

```yaml
input_review:
  enabled: true
  expert_name: "会议材料审核专家"
  prompt_file: agents/sales-account-strategist.md  # Triggers LLM mode
```

The runtime:
1. Loads the prompt template from `agents/sales-account-strategist.md`
2. Substitutes placeholders: {evidence}, {check_signals}, {expert_name}
3. Invokes LLM via OpenAI or Anthropic API
4. Parses response into findings (PASS/FLAG/BLOCK format)

### Fallback Behavior

Per D-06: LLM failure falls back to keyword-based audit. No scene blocks on LLM unavailability. Error handling covers: timeout, auth failure (401), rate limit (429), empty response, parse failure.

### Prompt Templates

Expert prompts are stored in `agents/`:
- `sales-account-strategist.md` — Account strategy expert
- `customer-service.md` — Customer service quality expert
- `sales-proposal-strategist.md` — Sales proposal strategy expert
- `sales-data-extraction-agent.md` — Data extraction (disabled)

## 已注册专家角色

### 1. 风险分析师 (Risk Analyst)

**用途：** 在分析开始前审核原始用户输入，识别遗漏的风险信号。

**触发条件：**
- 输入包含客户会议材料或状态更新时
- 任务涉及识别风险和缓解策略时

**专业领域：**
- 识别合同执行风险
- 识别收款风险
- 识别客户关系风险
- 识别项目交付风险

### 2. 经营顾问 (Business Consultant)

**用途：** 在交付前审核输出建议的业务专业性。

**触发条件：**
- 任务产生 Todo 事项、执行计划或战略建议时
- 输出涉及回写 Feishu 表格时

**专业领域：**
- 建议的专业性和可执行性
- 业务逻辑的一致性
- 优先级判断的合理性

### 3. 客户档案官 (Archive Officer)

**用途：** 审核客户档案更新的完整性和准确性。

**触发条件：**
- 创建或更新客户档案文档时
- 关联会议记录与客户档案时

**专业领域：**
- 档案结构的完整性
- 历史弧线的连贯性
- 关键决策的溯源性

## 专家配置架构

每个专家配置遵循以下结构：

```yaml
name: <专家名称-中文>
name_en: <专家名称-英文>
role: <input|output>
trigger_scenes:
  - <场景名称>
checkpoints:
  - input_validation
  - output_review
expertise:
  - <专业领域-1>
  - <专业领域-2>
review_criteria:
  - <审核标准-1>
  - <审核标准-2>
```

## Agent Registry

Expert agents are registered in `agents/agent-registry.yaml` — the **SOLE SOURCE OF TRUTH** for agent definitions (per AA-01-PLAN.md).

```yaml
# agents/agent-registry.yaml — Schema Version 1.1
schema_version: "1.1"

agents:
  sales-account-strategist:
    platform: openclaw
    enabled: true
    prompt_file: agents/sales-account-strategist.md
    supports_council: true
    supports_sequential: true
```

### Validation Rules

- Only agents defined in `agent-registry.yaml` can be invoked
- `validate_agent_reference()` validates agent names before use
- Disabled agents (`enabled: false`) cannot be invoked
- `prompt_file` paths are validated against `agents/` directory (strict: resolve(), no symlinks, only .md)

### Error Handling

Per OpenCode review, LLM invocation handles these failure modes explicitly:
- **Timeout**: Request exceeds 30s — fallback to keyword
- **Auth failure (401)**: Invalid API key — fallback to keyword
- **Rate limit (429)**: API rate exceeded — fallback to keyword
- **Empty response**: No content from LLM — fallback to keyword
- **Parse failure**: Response doesn't match PASS/FLAG/BLOCK format — fallback to keyword

## 加载机制

专家通过场景运行时契约加载。技术集成细节请参阅 [references/scene-runtime-contract.md](references/scene-runtime-contract.md)。

## 场景到专家映射

| 场景 | 输入专家 | 输出专家 | 审核模式 |
|-------|-------------|---------------|----------|
| post-meeting-synthesis | 风险分析师 | 经营顾问 | LLM (prompt_file set) |
| customer-recent-status | 风险分析师 | 经营顾问 | LLM (prompt_file set) |
| archive-refresh | 客户档案官 | 经营顾问 | Keyword |
| todo-capture-and-update | - | 经营顾问 | Keyword |
| cohort-scan | 风险分析师 | 经营顾问 | Keyword |
| meeting-prep | 风险分析师 | 经营顾问 | Keyword |
| proposal | 风险分析师 | 经营顾问 | LLM (prompt_file set) |

The "审核模式" column indicates whether LLM-based or keyword-based audit is used.

---

*本文档定义专家角色接口。各个专家配置在场景执行期间按需加载。*
