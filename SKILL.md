---
name: feishu-am-workbench
version: 1.3.0
author: fishskylky-tech
license: MIT
description: >
  Personal AM workflow skill for Feishu. Use this skill whenever the user
  mentions: 飞书工作台, 客户档案, 会议纪要, 行动计划, 客户主数据, 合同,
  联系记录, 竞品, Todo, 客户更新, 会前准备, 会后总结, account analysis,
  meeting prep, post-meeting synthesis, or wants to write back to Feishu.
  Also trigger when user pastes meeting transcript, shares customer file,
  or asks "这个客户最近怎样", "帮我整理会议", "更新行动计划", "准备明天拜访".
triggers:
  keywords: [飞书工作台, 客户档案, 会议纪要, 行动计划, Todo, 客户更新, 会前准备, 会后总结]
  patterns: [meeting prep, post-meeting, account analysis, customer update]
  file_types: [transcript, meeting notes, customer materials]
load_strategy: progressive
tier:
  L1: frontmatter + scene_index
  L2: core_workflow + hard_rules + output_pattern + write_order + closed_loop + scope
  L3: references/*.md + scenes/*/expert-cards.yaml + agents/*.md (on-demand)
---

# Feishu AM Workbench

## Overview

Use this skill for a personal AM workflow built around Feishu Base, docs, and Todo. It turns mixed inputs into a structured account view, proposes updates across the workbench, and only writes after explicit user confirmation. The workbench has four layers: `客户主数据` (index), detail tables (合同/行动计划/关键人/联系记录/竞品), `客户档案` (narrative archive), and Feishu Todo (execution reminders).

## Available Scenes (7)

| Scene | Purpose | Expert Cards |
|-------|---------|--------------|
| post-meeting-synthesis | Meeting -> structured account judgment | input + output |
| customer-recent-status | 4-lens customer status query | input |
| archive-refresh | Canonical archive update | input + output |
| todo-capture-and-update | Todo follow-on capture | output |
| cohort-scan | Customer cohort analysis | input |
| meeting-prep | 7-dim meeting brief | input + output |
| proposal | 5-dim proposal/report | input + output |

## Core Workflow (10 steps)

1. Identify customer intent and candidate customer names
2. Resolve one `客户ID` from `客户主数据` before planning any write
3. Use Feishu workbench gateway for live data access
4. Run live-first gate for meeting notes/transcripts
5. Classify meeting type before deciding write scope
6. Extract all relevant entities before routing anything
7. Read minimum extra context needed
8. Run live schema preflight before any write plan
9. Separate facts from judgment
10. Produce account analysis + structured change plan; wait for confirmation (recommendation-first)

## Hard Rules

- Always use `客户主数据` as source of truth for `客户ID`
- If customer matching is ambiguous, stop and ask for clarification
- Treat customer master table as protected — only update allowed fields
- Use actual Base schema, not guessed field names
- Before any Base write: confirm table/field exists and type matches
- Treat dates as absolute — never relative expressions
- Never store raw transcript as formal meeting-note doc
- Do not present inferred business judgment as objective fact
- Each customer must have only one canonical archive doc
- Strategy fields in `客户主数据` should move slowly

## Output Pattern

1. Meeting framing and context recovery
2. Confirmed facts and judgment
3. Structured summary
4. Recommendation-mode updates
5. Open questions or blocked items
6. After user confirmation: write results and change summary

## Write Order

1. Update structured Feishu tables first
2. Create/update supporting docs (archive, meeting-note) after table state is correct
3. Create/update Todo items last
4. If later step fails, report completed writes and remaining failures

## Closed Loop

1. User input creates/updates detail records
2. Detail records and public inputs are distilled into customer archive
3. Customer archive becomes decision basis for `客户主数据` strategy changes
4. Todo items help execution, but do not replace structured detail records

## Scope

This skill is for the user's personal account book, not a generic CRM. Prefer precision, cautious write-back, and preserving cross-table integrity.

## Read These References As Needed

For quick overview: see [references/INDEX.md](./references/INDEX.md)

- [references/entity-extraction-schema.md](./references/entity-extraction-schema.md) — before parsing mixed inputs
- [references/master-data-guardrails.md](./references/master-data-guardrails.md) — before changing customer master data
- [references/update-routing.md](./references/update-routing.md) — before deciding where each extracted item belongs
- [references/feishu-runtime-sources.md](./references/feishu-runtime-sources.md) — for runtime setup and prerequisites
- [references/feishu-workbench-gateway.md](./references/feishu-workbench-gateway.md) — for Feishu workbench access
- [references/meeting-context-recovery.md](./references/meeting-context-recovery.md) — for meeting note/transcript tasks
- [references/meeting-live-first-policy.md](./references/meeting-live-first-policy.md) — for meeting tasks
- [references/meeting-type-classification.md](./references/meeting-type-classification.md) — for meeting type and write ceiling
- [references/customer-archive-rules.md](./references/customer-archive-rules.md) — before updating customer archive
- [references/task-patterns.md](./references/task-patterns.md) — for common workflows

## Expert Cards

Each scene has expert card configurations in `scenes/{scene_name}/expert-cards.yaml`. These provide input/output audit at key scene nodes.

### LLM-Based Expert Review

For scenes with `prompt_file` field in expert-cards.yaml, the runtime uses LLM-based expert review instead of keyword-based audit:

```yaml
input_review:
  enabled: true
  expert_name: "会议材料审核专家"
  review_type: "materials_audit"
  check_signals:
    - "遗漏的关联信息"
  output_field: "input_audit_notes"
  prompt_file: agents/sales-account-strategist.md  # LLM mode
```

When `prompt_file` is set:
1. Runtime reads the agent prompt template from `agents/{filename}.md`
2. Substitutes placeholders: {evidence}, {check_signals}, {expert_name}
3. Invokes LLM via OpenAI or Anthropic API
4. Parses LLM response into findings (PASS/FLAG/BLOCK format)

Fallback: If LLM invocation fails (missing API key, timeout, rate limit), the runtime falls back to keyword-based audit.

Available expert prompts in `agents/`:
- `sales-account-strategist.md` — Account strategy expert
- `customer-service.md` — Customer service quality expert
- `sales-proposal-strategist.md` — Sales proposal strategy expert
- `sales-data-extraction-agent.md` — Data extraction (future use)
