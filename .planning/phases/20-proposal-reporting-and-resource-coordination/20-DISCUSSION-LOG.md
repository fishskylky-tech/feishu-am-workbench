# Phase 20: Proposal, Reporting, And Resource Coordination - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-18
**Phase:** 20-proposal-reporting-and-resource-coordination
**Areas discussed:** Scene variants + Input materials, Output structure, Feishu routing, Confirmation checklist design, Expert judgment relationship, Agency agent question

---

## Scene Variants + Input Materials

| Option | Description | Selected |
|--------|-------------|----------|
| 统一场景（推荐） | 一个 scene + proposal_type 参数，共享组装逻辑 | ✓ |
| 分开场景 | 三个独立 scene，各自独立的确认清单和输出格式 | |

**User's choice:** 统一场景（推荐）
**Notes:** 用户倾向减少重复代码，共享 EvidenceContainer 组装逻辑

---

## Input Materials

| Option | Description | Selected |
|--------|-------------|----------|
| 两者结合（推荐） | 用户显式指定主要材料，系统自动补充客户档案等相关上下文 | ✓ |
| 用户显式指定为主 | 系统只处理用户指定的材料，不主动拉取 | |
| 系统自动拉取为主 | 用户只需确认范围是否正确 | |

**User's choice:** 两者结合（推荐）
**Notes:** 既尊重用户意图（显式材料优先），又利用 Phase 16 的多源证据组装能力

---

## Output Structure

| Option | Description | Selected |
|--------|-------------|----------|
| 固定五段（推荐） | objective/core judgment/main narrative/resource asks/open questions，类型差异通过突出部分和内容量体现 | ✓ |
| 类型差异化结构 | 提案、报告、资源协调各有不同字段组合 | |

**User's choice:** 固定五段（推荐）
**Notes:** 结构一致性优先，类型差异通过内容量体现

---

## Feishu Routing

| Option | Description | Selected |
|--------|-------------|----------|
| 类型默认 + 清单确认（推荐） | 系统按类型推荐目的地，用户在确认清单里修改或确认 | ✓ |
| 用户每次手动选择 | 每次输出前用户指定目的地 | |
| 统一一个目的地 | 所有 proposal 类型输出都路由到同一个位置 | |

**User's choice:** 类型默认 + 清单确认（推荐）
**Notes:** 与 Phase 19 WRITE-02 设计一致：系统建议，用户确认

---

## Confirmation Checklist Design

| Option | Description | Selected |
|--------|-------------|----------|
| 最小清单（推荐） | 通用四项 + proposal_type + output_destination（6项） | ✓ |
| 完整清单 | 增加 need_internal_review、deadline、是否需要财务/法务参与等 | |

**User's choice:** 最小清单（推荐）
**Notes:** 确认清单应快速简便，不增加用户负担

---

## Expert Judgment Relationship

| Option | Description | Selected |
|--------|-------------|----------|
| 各场景独立（推荐） | 每个场景用自己的判断逻辑，复用 ExpertAnalysisHelper 做材料组装 | ✓ |
| 共享判断框架 | 所有场景共用一套核心判断的结构 | |

**User's choice:** 各场景独立（推荐）
**Notes:** Phase 17/18/19/20 各场景独立实现判断逻辑，ExpertAnalysisHelper 保持通用

---

## Additional Discussion: Agency Agent

**Question raised:** 现阶段引入 agency agent 了吗？按 roadmap，预计什么时候会引入 agency agent？

**Answer provided:**
- 目前没有引入 agency agent，v1.2 保持 human-in-the-loop 设计
- v1.2 的核心价值是 "expert-guided customer-operating workflows"，重点是辅助判断，不是自主执行
- 引入 agency 需要单独 milestone 定义授权边界、安全确认机制、责任模型
- Future Requirements（OPS-01、OPS-02）更像定时自动化，而非真正的 agency
- Agency 能力是潜在的未来 milestone，不是 v1.2 现阶段要处理的

**Noted as deferred idea** in CONTEXT.md D-19/D-20

---

## Claude's Discretion

- Exact implementation of `proposal_type` parameter (enum vs string)
- Exact default routing destination paths for each type (exact Drive folder structure)
- How to handle the "core judgment" emphasis differences between proposal type variants
- Whether to auto-detect proposal type from materials or require explicit user selection

---

## Deferred Ideas

- **Agency / autonomous agent capability** — discussed, explicitly out of scope for v1.2. Would require dedicated milestone.
- **Shared judgment framework** — not needed given scene-independent judgment choice.

