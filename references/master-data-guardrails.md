---
title: Master Data Guardrails
load_triggers:
  - skill_stage: [master-data-write, customer-update]
  - task_type: [customer-update, master-data-change]
load_priority: high
estimated_tokens: 706
dependencies: []
tier: L3-scenario-customer
---

# Master Data Guardrails

The customer master table is the primary anchor for the workbench.
These rules are based on the current live `客户主数据` schema, not on guessed CRM-style fields.

## Primary key rule

- Always resolve and use `客户ID` from `客户主数据`.
- Other tables, docs, and tasks should be referenced through that `客户ID`.
- If the input only matches a nickname, group name, or brand alias, verify the final customer record before writing.

## Protected fields

These fields are treated as read-only unless the user explicitly overrides the rule after seeing the proposed change:

- `客户 ID`
- `公司名称`
- `简称`
- `客户分层`
- `经营分层`
- `客户状态`
- `销售`
- `项目管理`
- `分析师`
- `AM`
- `细分行业`
- `已购产品`
- `合作模式`
- `首次签约`
- `应续费年`
- `应续月份`
- `应续金额(万)`
- `目标-续费(万)`
- `目标-增购(万)`
- `目标-汇总(万)`
- `23年收入(万)`
- `24年收入(万)`
- `25年收入(万)`
- `实际-续约（万）`
- `实际-增购（万）`
- `实际-汇总（万）`
- `目标达成率`
- Any auto-calculated, lookup, or formula field

When in doubt, do not write and call out the field as protected.

## Three write tiers

### Tier 1: Do not change

- `客户主键id`
- `客户 ID`
- `公司名称`
- `简称`
- `客户分层`
- `经营分层`
- `客户状态`
- `销售`
- `项目管理`
- `分析师`
- `AM`
- `细分行业`
- `已购产品`
- `合作模式`
- `首次签约`
- `应续费年`
- `应续月份`
- `应续金额(万)`
- `目标-续费(万)`
- `目标-增购(万)`
- `目标-汇总(万)`
- `23年收入(万)`
- `24年收入(万)`
- `25年收入(万)`
- `实际-续约（万）`
- `实际-增购（万）`
- `实际-汇总（万）`
- `目标达成率`
- Auto-calculated, lookup, and formula fields

### Tier 2: Change only with mature evidence

- `26年策略方向`
- `策略摘要`
- `续费风险`
- `健康评分`
- Similar operating-posture fields that should not swing with every new meeting

### Tier 3: Normal operating updates

- `当前对接人`
- `备注`
- `增购机会`
- `下次行动计划`
- `上次接触日期`
- `最后更新时间`
- `客户档案`

## Typically writable fields

These are normal operating fields and can be proposed for update after confirmation:

- `当前对接人`
- `备注`
- `增购机会`
- `下次行动计划`
- `上次接触日期`
- `最后更新时间`
- `客户档案`

Use this list together with the three tiers above. If a field is in conflict, the stricter rule wins.

## Matching rule

Before write-back, show:

- Raw customer mentions
- Resolved customer record
- `客户ID`
- Confidence

If confidence is low or there are multiple candidate records, stop before writing.

## Schema drift rule

- Treat this file and the cached field mapping as guardrails, not as proof that a field still exists.
- Before writing any master-data field, confirm the field live in Base.
- If the field name changed, try a narrow alias fallback that preserves the same business meaning.
- If the field no longer exists or the meaning is no longer clear, treat it as protected and stop at recommendation mode.
- Never redirect a protected or Tier 2 write into a vaguely similar field just to make the write succeed.

## Field protection behavior

- Protected field in change plan: show it under `left unchanged`.
- Tier 2 field in change plan: explicitly state why the evidence is mature enough to update it.
- Protected field explicitly requested by user: flag the risk, ask for confirmation, then proceed only if the user clearly wants the override.
- Unknown field: treat as protected until verified.
