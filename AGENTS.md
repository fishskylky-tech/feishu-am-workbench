# AGENTS.md

**Last Updated:** 2026-04-19

---

This document describes the expert agent roles that can be invoked at key decision points in the Feishu AM Workbench skill.

## Role Architecture

The skill uses a "活页夹" (loose-leaf binder) pattern for expert roles. Each expert is defined in a separate configuration file that can be loaded on demand when the skill encounters specific input/output boundary points.

Expert roles are **not hardcoded** into the scene logic. They are invoked as reviewers at critical checkpoints:

- **Input checkpoint**: User materials are reviewed by a domain expert before analysis
- **Output checkpoint**: Recommendations are reviewed by a business consultant before delivery

## Registered Expert Roles

### 1. 风险分析师 (Risk Analyst)

**Purpose:** Review raw user input for missed risk signals before analysis begins.

**Triggers:**
- When the input contains customer meeting materials or status updates
- When the task involves identifying risks and mitigation strategies

**Expertise:**
-识别合同执行风险
- 识别收款风险
- 识别客户关系风险
- 识别项目交付风险

### 2. 经营顾问 (Business Consultant)

**Purpose:** Review output recommendations for business professionalism before delivery.

**Triggers:**
- When the task produces Todo items, action plans, or strategic recommendations
- When the output involves writing back to Feishu tables

**Expertise:**
- 建议的专业性和可执行性
- 业务逻辑的一致性
- 优先级判断的合理性

### 3. 客户档案官 (Archive Officer)

**Purpose:** Review customer archive updates for completeness and accuracy.

**Triggers:**
- When creating or updating customer archive documents
- When linking meeting notes to customer archives

**Expertise:**
- 档案结构的完整性
- 历史弧线的连贯性
- 关键决策的溯源性

## Expert Configuration Schema

Each expert configuration follows this structure:

```yaml
name: <expert-name-zh>
name_en: <expert-name-en>
role: <input|output>
trigger_scenes:
  - <scene-name>
checkpoints:
  - input_validation
  - output_review
expertise:
  - <expertise-area-1>
  - <expertise-area-2>
review_criteria:
  - <criterion-1>
  - <criterion-2>
```

## Loading Mechanism

Experts are loaded via the scene runtime contract. See [references/scene-runtime-contract.md](references/scene-runtime-contract.md) for the technical integration details.

## Scene-to-Expert Mapping

| Scene | Input Expert | Output Expert |
|-------|-------------|---------------|
| post-meeting-synthesis | 风险分析师 | 经营顾问 |
| customer-recent-status | 风险分析师 | 经营顾问 |
| archive-refresh | 客户档案官 | 经营顾问 |
| todo-capture-and-update | - | 经营顾问 |
| cohort-scan | 风险分析师 | 经营顾问 |
| meeting-prep | 风险分析师 | 经营顾问 |
| proposal | 风险分析师 | 经营顾问 |

---

*This document defines the expert role interface. Individual expert configurations are loaded on demand during scene execution.*
