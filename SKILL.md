---
name: feishu-am-workbench
description: Analyze customer materials, Feishu workbench records, user notes, and public updates for an AM. Use when the user wants account analysis, meeting prep, post-meeting synthesis, update recommendations, or confirmed write-back into a Feishu-based account management platform.
---

# Feishu AM Workbench

## Overview

Use this skill for a personal AM workflow built around Feishu Base, Feishu docs, and Feishu Todo. The skill turns mixed inputs into a structured account view, proposes updates across the workbench, and only writes after explicit user confirmation.

The workbench is layered:

- `客户主数据`
  - Index and snapshot layer for one customer
- Detail tables
  - `合同清单`
  - `行动计划`
  - `客户关键人地图`
  - `客户联系记录`
  - `竞品交锋记录`
- `客户档案`
  - Narrative archive and decision-support layer
- Feishu Todo
  - Reminder and execution layer, including customer work and non-customer work

## Use This Skill When

- The user asks for account analysis based on local files, Feishu records, notes, or public information.
- The user wants meeting prep, post-meeting synthesis, or customer strategy suggestions.
- The user wants to update Feishu customer archives, master data, action plans, contact maps, contract records, or Todo items.
- The input may mix several dimensions at once, such as contacts, competitors, contracts, risks, opportunities, schedules, and action items.

## Core Workflow

1. Identify the customer intent and candidate customer names from the input.
2. Resolve the customer to one `客户ID` from the customer master table before planning any write.
3. Extract all relevant entities from the input before routing anything. Do not write while still extracting.
4. Read the minimum additional context needed from local files, Feishu workbench objects, and public sources if requested.
5. Before any write plan, run a live schema preflight for every Base table and field you may touch.
6. Separate facts from judgment. Use the fact grading rules in [references/fact-grading.md](./references/fact-grading.md).
7. Produce two outputs:
   - Account analysis and recommendations
   - A structured change plan listing each target object, whether it is a create or update, and the key fields involved
8. Wait for explicit confirmation before any Feishu write.
9. After confirmation, write structured tables first, archive and meeting-note docs second, and Todo last.
10. Report success, partial failure, schema drift, or blocked status clearly.

## Hard Rules

- Always use `客户主数据` as the source of truth for `客户ID`.
- If customer matching is ambiguous, do not write. Ask for clarification or provide a no-write recommendation.
- Treat the customer master table as protected. Only update fields allowed by [references/master-data-guardrails.md](./references/master-data-guardrails.md).
- Use the actual Base schema, not guessed field names. Treat [references/actual-field-mapping.md](./references/actual-field-mapping.md) as a cached schema snapshot, not the sole source of truth.
- Before any Base write:
  - confirm the target table still exists in the live Base
  - confirm the target field still exists
  - confirm the field type still matches the intended write
  - if the field is `select` or `multi_select`, fetch live options first and resolve against those live options
- If the live schema disagrees with the cached mapping, trust the live schema and surface the drift in the change plan.
- Treat `客户主数据` as an index and current snapshot, not as a running log. Do not push detailed historical facts, long meeting notes, or dense delivery history into the master table.
- All date output and write-back must use absolute time expressions. Do not write relative dates such as `近期`, `昨天`, `明天`, `今年`, or `明年`.
- If the source only provides an imprecise date, keep the highest-confidence absolute form available, such as `YYYY-MM-DD`, `YYYY-MM`, `YYYY年Qn`, or `YYYY年M月`, and call out any missing precision before writing.
- Do not mix public news into meeting notes, and do not mix meeting notes into `最新资讯`.
- Store full meeting notes as Feishu docs and keep only the document link in tables. Treat those docs as cold memory that should be loaded only when needed.
- Unless the user says otherwise, store meeting-note cold-memory docs in the dedicated Feishu folder `OlBCfU7IKl2oSbd09lXckKJlnTc`.
- Do not present inferred business judgment as objective fact.
- Do not treat historical plans, modelled incentives, or draft commercials as actual revenue unless the source clearly says they were signed and paid.
- By default, historical contracts belong in the customer archive doc, not in `合同清单`. Use `合同清单` only for current or still-operational contracts that matter to active tracking such as validity, renewal, collections, or ongoing execution.
- Each customer must have only one canonical customer archive doc. Before creating or linking any archive content, first find the existing archive linked from customer master data and update that doc instead of creating a second archive.
- If the archive link in customer master is empty, invalid, or obviously stale, search the customer-archive folder by `客户ID` and `简称` before creating a new archive doc.
- If one `客户ID` covers multiple brands, product lines, or project tracks, do not add a generic `品牌` field just for that customer. Use a stable text prefix such as `品牌｜主题` in titles, key nodes, notes, and action subjects instead.
- `客户档案` is not a table dump and not a running log. It should explain the customer's full picture, historical arc, current state, and the basis for strategy changes.
- `行动计划` and Feishu Todo are not the same thing. `行动计划` is the structured customer-operating detail table. Todo is the reminder and execution carrier.
- Any new Feishu Todo task must have an explicit owner. If no responsible person can be resolved with confidence, do not create the task yet; surface the missing owner in the change plan.
- Strategy fields in `客户主数据` should move slowly. Do not update them just because a new meeting happened. Update them only when the evidence is mature enough to change the account's operating posture.
- Before writing, apply idempotency rules from [references/update-routing.md](./references/update-routing.md) to avoid duplicates.
- For Todo creation, dedupe by meaning, not just by exact title match. If a closely related task already exists, prefer updating it or attaching a subtask instead of creating a new sibling task.
- Do not rely on a permanently static field or option map. The skill should degrade safely when the Base schema changes:
  - use live discovery first
  - use alias matching second
  - if still unresolved, stop at recommendation mode instead of writing to a guessed field

## Extraction First

Inputs may contain several dimensions at once. Always extract a full information bundle before planning updates. Use [references/entity-extraction-schema.md](./references/entity-extraction-schema.md).

The extraction bundle should cover, when present:

- Customer identity
- Contacts and org changes
- Competitors
- Contracts, amounts, and collections
- Risks
- Opportunities
- Key progress and blockers
- Todos
- Schedules and milestone dates
- Public updates
- Communication records
- Account judgment

If one input yields items for multiple tables, show all of them in the change plan. Do not collapse them into a single summary field.

## Read These References As Needed

- Read [references/entity-extraction-schema.md](./references/entity-extraction-schema.md) before parsing mixed inputs.
- Read [references/master-data-guardrails.md](./references/master-data-guardrails.md) before changing customer master data.
- Read [references/update-routing.md](./references/update-routing.md) before deciding where each extracted item belongs.
- Read [references/money-and-contract-rules.md](./references/money-and-contract-rules.md) whenever money, contracts, renewal terms, collections, or estimated value appear.
- Read [references/customer-archive-rules.md](./references/customer-archive-rules.md) before updating the customer archive doc.
- Read [references/task-patterns.md](./references/task-patterns.md) for common workflows such as meeting prep, post-meeting updates, and archive refreshes.
- Read [references/workbench-information-architecture.md](./references/workbench-information-architecture.md) whenever the task touches how the workbench should be interpreted, routed, or updated.
- Read [references/actual-field-mapping.md](./references/actual-field-mapping.md) whenever the task touches real Base fields or table-specific write behavior.
- Read [references/schema-compatibility.md](./references/schema-compatibility.md) whenever the task may be affected by renamed fields, added fields, deleted fields, option changes, or other schema drift.

## Output Pattern

Default to this shape:

1. Analysis and judgment
2. Proposed updates
3. Open questions or blocked items
4. Only after user confirmation: write results and return a change summary

For proposed updates, include:

- Resolved customer and `客户ID`
- Extracted entities
- Target objects to update
- Create vs update decision for each object
- Facts vs judgment
- Normalized absolute dates and any date precision gaps
- Any protected fields that were intentionally left unchanged
- Any schema drift, alias fallback, or unresolved live-field mismatch

## Write Order

When the user confirms:

1. Update structured Feishu tables first.
2. Create or update supporting docs after the table state is correct:
   - Customer archive doc
   - Meeting-note cold-memory doc when needed
3. Create or update Todo items last.
4. If a later step fails, report the already-completed writes and the remaining failures. Do not silently retry by inventing new values.

## Closed Loop

The workbench should form a loop:

1. User input and materials create or update detail records
2. Detail records and public inputs are distilled into the customer archive
3. The customer archive becomes the decision basis for any strategy change in `客户主数据`
4. Todo items help execution, but do not replace structured detail records

## Scope

This skill is for the user's personal account book, not a generic CRM. Prefer precision, cautious write-back, and preserving cross-table integrity over maximizing automation.

If a customer has no archive doc yet, the skill may create a minimal archive doc and backfill the link after confirmation.
