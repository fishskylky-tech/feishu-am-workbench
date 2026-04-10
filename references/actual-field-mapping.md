# Actual Field Mapping

This file is a cached snapshot of the live Feishu account-management schema as of `2026-04-10`.

Use it as a fast reference, not as the sole source of truth.
Before any write, confirm the target schema live and treat this file as a compatibility cache.

## How to use this file

- Use this file to understand the current intent of each table and field.
- Do not assume it is always current.
- If the live Base schema differs from this file, trust the live schema.
- If a field was renamed, added, or removed:
  - try semantic matching and alias matching
  - if still uncertain, stop at recommendation mode instead of writing blind
- For `select` or `multi_select` fields, fetch live options at write time instead of relying on a hard-coded option list here.

## Current tables

- `客户主数据`
- `合同清单`
- `行动计划`
- `客户关键人地图`
- `竞品基础信息表`
- `竞品交锋记录`
- `客户联系记录`
- `潜在客户池`

There is currently no separate `客户联系计划` table in the Base. Use `客户联系记录` as the communication-detail table.

## 客户主数据

Purpose:

- One-row snapshot per customer
- Stable commercial and ownership baseline
- Current operating summary
- Link to the canonical customer archive

Important writable fields:

- `当前对接人`
- `备注`
- `策略摘要`
- `增购机会`
- `下次行动计划`
- `上次接触日期`
- `最后更新时间`
- `续费风险`
- `健康评分`
- `客户档案`

Important protected or slow-moving fields:

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
- `26年策略方向`

Notes:

- `客户档案` is a URL text field, not a relational link.
- `实际-*` and `目标达成率` include lookup/formula outputs and must be treated as read-only.
- `下次行动计划` and `上次接触日期` should hold only the latest useful snapshot item.

## 合同清单

Purpose:

- Current or actively managed contracts only
- Renewal, collection, acceptance, and execution tracking

Actual fields:

- `合同编码`
- `客户ID`
- `客户名称` (lookup)
- `关键节点`
- `合同类型`
- `合同状态`
- `签约日期`
- `合同生效日期`
- `合同到期日期`
- `节点日期`
- `合同金额(万)`
- `已回款金额(万)`
- `回款状态`
- `验收状态`
- `负责人`
- `风险提示`
- `目标毛利(%)`
- `毛利实际达成(%)`
- `备注`

Write guidance:

- Historical contracts should usually stay in `客户档案`, not here.
- When a single customer contains multiple brand tracks, use `品牌｜主题` in `关键节点` and, when helpful, in `备注`.

## 行动计划

Purpose:

- Structured customer-operating actions
- Detail layer for account work, not reminder orchestration

Actual fields:

- `行动 ID`
- `客户ID`
- `客户名称` (lookup)
- `具体行动`
- `行动类型_单选`
- `计划完成时间`
- `完成状态_单选`
- `实际完成时间`
- `产出结果`

Write guidance:

- This table does not currently have a dedicated owner field or Todo link field.
- Put the actionable statement in `具体行动`.
- Put reminder/execution burden into Feishu Todo when needed; do not invent missing Base fields.
- Current live select options can be discovered at write time:
  - `完成状态_单选`: `未开始`, `进行中`, `已完成`, `已推迟`, `取消`
  - `行动类型_单选`: `新增客户拓展`, `续费沟通`, `增购推进`, `问题处理`, `日常维护`, `项目启动`, `项目验收`, `客户拜访`, `客户经营`
- Treat the above option list as a snapshot only. Query live options before writing because the user may add or retire values later.

## 客户关键人地图

Purpose:

- Contact-by-contact map for current and historical people

Actual fields:

- `关键人ID`
- `客户ID`
- `客户名称` (lookup)
- `姓名`
- `职位`
- `部门`
- `角色`
- `关系强度`
- `关系评分`
- `联系频率`
- `最近联系时间`
- `上次沟通（停用）`
- `下次联系计划`
- `微信/飞书`
- `联系方式`
- `邮箱`
- `关键诉求`
- `实施需求（可选）`
- `个人特点`
- `备注`
- `动态备注`

Preferred write behavior:

- Prefer `最近联系时间` as the primary “last meaningful touch” field.
- Treat `上次沟通（停用）` as legacy unless the user explicitly wants both fields maintained.
- Prefer `关键诉求` for the contact's outward business ask or concern.
- Use `实施需求（可选）` only when a second implementation-oriented need is genuinely useful.
- Use `备注` for stable status labeling such as “历史联系人，不作为当前经营对象”.
- Use `动态备注` for dated or contextual notes that support later interpretation.

## 客户联系记录

Purpose:

- Structured communication detail plus cold-memory link

Actual fields:

- `记录标题`
- `客户ID`
- `客户名称` (lookup)
- `联系日期`
- `下次联系计划`
- `联系人员`
- `联系人`
- `对接人职位`
- `沟通要点`
- `关键进展`
- `待办事项`
- `客户顾虑/风险`
- `会议纪要文档`
- `联系方式`

Preferred write behavior:

- `记录标题` is the primary field. Keep it concise and searchable.
- Preferred format for `记录标题`: `客户/品牌｜主题`
- `联系人员` means the user's side / internal attendees or owners.
- `联系人` means customer-side participants.
- `会议纪要文档` should store the cold-memory doc URL.
- Full meeting content belongs in the meeting-note doc, not in Base text fields.

## 竞品基础信息表

Purpose:

- Competitor master data

Actual fields:

- `竞品ID`
- `竞品公司名称`
- `公司全称`
- `产品类型`
- `核心功能`
- `优势特点`
- `劣势不足`
- `定价模式`
- `市场占有率`
- `目标客户`
- `调研状态`
- `调研完成时间`
- `调研负责人`
- `备注信息`

## 竞品交锋记录

Purpose:

- Many-to-many bridge between customer accounts and competitors

Actual fields:

- `ID`
- `客户ID`
- `客户名称` (lookup)
- `竞品ID`
- `竞品名称` (lookup)
- `交锋时间`
- `交锋场景`
- `竞品报价`
- `竞品核心卖点`
- `客户顾虑`
- `我方应对话术`
- `应对结果`
- `经验总结`

## Feishu Todo tasklist: 神策

Tasklist:

- Name: `神策`
- `tasklist_guid`: `e50dda19-63e4-410a-a167-6813f3b3c86d`

Custom fields currently validated from live tasks:

- `客户`
  - `guid`: `a7009aff-7d85-4378-82c9-1584873f469d`
  - type: `text`
- `优先级`
  - `guid`: `f7587037-8ad1-443c-b350-f6600e0ccadd`
  - type: `single_select`
  - current known options:
    - `高`
    - `中`
    - `低`

Treat these task custom fields as live-configured resources. If tasklist settings drift, re-read a representative task before writing at scale.

Current validated custom fields:

- `客户`
  - `guid`: `a7009aff-7d85-4378-82c9-1584873f469d`
  - Type: `text`
  - Rule:
    - Fill for customer-related tasks
    - Leave empty for non-customer tasks
    - Preferred value: customer short name, optionally with `客户ID` in the description rather than in the field value itself

- `优先级`
  - `guid`: `f7587037-8ad1-443c-b350-f6600e0ccadd`
  - Type: `single_select`
  - Option mapping:
    - `高` -> `d7aff674-0ef8-6397-9108-fb260e21bde9`
    - `中` -> `6238286f-b2e2-5ab8-e902-a3bb9dc242b0`
    - `低` -> `9de7ca79-281c-0b3b-75d6-847a8c69a330`

Todo write guidance:

- Every new task must include an `assignee`
- Every customer-related task should populate `客户`
- Every new task should set `优先级`
- Prefer one parent task plus subtasks when several execution items belong to the same customer-operating theme
- When a meeting-note doc or archive doc is directly relevant, prefer linking it in the task description; `docx_source` is a valid future upgrade path
