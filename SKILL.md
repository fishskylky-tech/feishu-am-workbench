---
name: feishu-am-workbench
description: >
  Personal AM workflow skill for Feishu-based account management. Use this skill whenever the user
  mentions: 飞书工作台, 客户档案, 会议纪要, 行动计划, 客户主数据, 合同, 联系记录, 竞品, Todo, 客户更新, 会前准备, 会后总结,
  account analysis, meeting prep, post-meeting synthesis, or wants to write back to Feishu Base, Docs, or Todo.
  Also trigger when the user pastes a meeting transcript, shares a customer file, or asks questions like
  "这个客户最近怎样", "帮我整理一下今天的会议", "更新一下飞书上的行动计划", "帮我准备一下明天的拜访". When in doubt, use this skill.
compatibility: requires lark-cli in PATH; Python 3.10+ for runtime/ modules; personal Feishu token configured in environment
---

# Feishu AM Workbench

## Overview

Use this skill for a personal AM workflow built around Feishu Base, Feishu docs, and Feishu Todo. The skill turns mixed inputs into a structured account view, proposes updates across the workbench, and only writes after explicit user confirmation.

## Runtime Prerequisites

This skill has an optional local runtime layer (`runtime/`) that enables live Feishu access, schema preflight, and write guard. To use live features:

- `lark-cli` must be in PATH and authenticated with a valid Feishu token
- Python 3.10+ required for `runtime/` modules
- Personal resource hints must exist in `references/live-resource-links.md`

Run `python3 -m runtime <skill-path>` to verify capability status before first use. If the runtime is unavailable, the skill falls back to recommendation mode (analysis and proposed updates only, no live write-back).

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
3. If the task touches Feishu workbench data, use the Feishu workbench gateway first. Use [references/feishu-workbench-gateway.md](./references/feishu-workbench-gateway.md).
4. For meeting-note or transcript scenarios, recover the minimum necessary historical context before deep interpretation. Use [references/meeting-context-recovery.md](./references/meeting-context-recovery.md) and [references/meeting-live-first-policy.md](./references/meeting-live-first-policy.md).
5. Classify the meeting type before deciding write scope. Use [references/meeting-type-classification.md](./references/meeting-type-classification.md).
6. Extract all relevant entities from the input before routing anything. Do not write while still extracting.
7. Read the minimum additional context needed from local files, Feishu workbench objects, and public sources if requested.
8. Before any write plan, run a live schema preflight for every Base table and field you may touch.
9. Separate facts from judgment. Use the fact grading rules in [references/fact-grading.md](./references/fact-grading.md).
10. Produce two outputs:
   - Account analysis and recommendations
   - A structured change plan listing each target object, whether it is a create or update, and the key fields involved
11. Wait for explicit confirmation before any Feishu write.
12. After confirmation, write structured tables first, archive and meeting-note docs second, and Todo last.
13. Report success, partial failure, schema drift, or blocked status clearly.

## Hard Rules

- Always use `客户主数据` as the source of truth for `客户ID`. Every downstream write, routing decision, and archive lookup depends on a single stable customer identifier — resolving this first prevents writes landing on the wrong customer or creating phantom records.
- If customer matching is ambiguous, stop and ask for clarification before writing anything. A misidentified customer means corrupted records that are hard to undo, and the cost of asking is always lower than the cost of a wrong write.
- Treat the customer master table as protected. Only update fields allowed by [references/master-data-guardrails.md](./references/master-data-guardrails.md).
- Use the actual Base schema, not guessed field names. Treat [references/actual-field-mapping.md](./references/actual-field-mapping.md) as a cached schema snapshot, not the sole source of truth.
- If a workspace config exists, resolve table ids, semantic field slots, and enum policies from that config before falling back to the cached mapping.
- Before any Base write:
  - confirm the target table still exists in the live Base
  - confirm the target field still exists
  - confirm the field type still matches the intended write
  - if the field is `select` or `multi_select`, fetch live options first and resolve against those live options
- If the live schema disagrees with the cached mapping, trust the live schema and surface the drift in the change plan.
- Treat `客户主数据` as an index and current snapshot, not as a running log. Do not push detailed historical facts, long meeting notes, or dense delivery history into the master table.
- All date output and write-back must use absolute time expressions — never relative ones like `近期`, `昨天`, `明天`, `今年`, or `明年`. Relative dates become meaningless the moment the record is read a week later and actively mislead future analysis. If the source only provides a vague timeframe, keep the highest-confidence absolute form available (e.g., `YYYY-MM`, `YYYY年Qn`) and flag the precision gap rather than inventing a fake specific date.
- If the source only provides an imprecise date, keep the highest-confidence absolute form available, such as `YYYY-MM-DD`, `YYYY-MM`, `YYYY年Qn`, or `YYYY年M月`, and call out any missing precision before writing.
- Do not mix public news into meeting notes, and do not mix meeting notes into `最新资讯`.
- Store full meeting notes as Feishu docs and keep only the document link in tables. Treat those docs as cold memory that should be loaded only when needed.
- Unless the user says otherwise, store meeting-note cold-memory docs in the dedicated Feishu folder `OlBCfU7IKl2oSbd09lXckKJlnTc`.
- For meeting-note handling, do not treat the transcript as self-sufficient if recoverable context exists in Feishu records or customer archive materials.
- For meeting-note handling, default to a live-first attempt. Do not stay on single-file analysis if gateway Stage 1-3 can be executed.
- For meeting-note handling, run the meeting live-first execution gate before formal analysis. Do not output a formal context-recovery result, meeting type, or write ceiling before the gate result is known.
- For meeting-note handling, do not conclude that live lookup is unavailable just because no obvious env var or direct config is visible. Check the repository runtime source layer first.
- For meeting-note handling, determine the meeting type first and let the meeting type define the default write ceiling.
- For meeting-note handling, the scenario should call foundation primitives explicitly. Do not rely on the foundation to assemble a default meeting context bundle.
- For meeting-note handling, do not output `completed`、`partial`、`context-limited` context recovery unless the foundation was actually executed. If the foundation was not executed, mark the run as `not-run`.
- Never store a raw transcript as the formal meeting-note doc. Raw transcripts are noisy, hard to navigate, and miss the interpretation layer entirely — cold memory should contain structured notes that a future reader can act on, not a word-for-word dump. See [references/meeting-note-doc-standard.md](./references/meeting-note-doc-standard.md) for the required structure.
- Do not present inferred business judgment as objective fact.
- Do not treat historical plans, modelled incentives, or draft commercials as actual revenue unless the source clearly says they were signed and paid.
- By default, historical contracts belong in the customer archive doc, not in `合同清单`. Use `合同清单` only for current or still-operational contracts that matter to active tracking such as validity, renewal, collections, or ongoing execution.
- Each customer must have only one canonical customer archive doc. Before creating or linking any archive content, first find the existing archive linked from customer master data and update that doc instead of creating a second archive.
- If the archive link in customer master is empty, invalid, or obviously stale, search the customer-archive folder by `客户ID` and `简称` before creating a new archive doc.
- If one `客户ID` covers multiple brands, product lines, or project tracks, do not add a generic `品牌` field just for that customer. Use a stable text prefix such as `品牌｜主题` in titles, key nodes, notes, and action subjects instead.
- `客户档案` is neither a table dump nor a running log. Its value lies in providing a narrative that explains the customer's full picture, historical arc, and the reasoning behind strategy changes — content a future reader can use to understand the account from scratch without querying every detail table. If it just mirrors what's already in Base fields or appends meeting summaries chronologically, it adds no decision-support value.
- `行动计划` and Feishu Todo are not the same thing. `行动计划` is the structured customer-operating detail table. Todo is the reminder and execution carrier.
- Any new Feishu Todo task must have an explicit, resolvable owner. An ownerless task is effectively dead on arrival — nobody will pick it up and it pollutes the task list. If no responsible person can be resolved with confidence from the input or existing records, surface the missing owner in the change plan and hold the task creation until the user confirms.
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

For a quick overview of all reference files, see [references/INDEX.md](./references/INDEX.md).

- Read [references/entity-extraction-schema.md](./references/entity-extraction-schema.md) before parsing mixed inputs.
- Read [references/master-data-guardrails.md](./references/master-data-guardrails.md) before changing customer master data.
- Read [references/update-routing.md](./references/update-routing.md) before deciding where each extracted item belongs.
- Read [references/money-and-contract-rules.md](./references/money-and-contract-rules.md) whenever money, contracts, renewal terms, collections, or estimated value appear.
- Read [references/customer-archive-rules.md](./references/customer-archive-rules.md) before updating the customer archive doc.
- Read [references/task-patterns.md](./references/task-patterns.md) for common workflows such as meeting prep, post-meeting updates, and archive refreshes.
- Read [references/workbench-information-architecture.md](./references/workbench-information-architecture.md) whenever the task touches how the workbench should be interpreted, routed, or updated.
- Read [references/actual-field-mapping.md](./references/actual-field-mapping.md) whenever the task touches real Base fields or table-specific write behavior.
- Read [references/schema-compatibility.md](./references/schema-compatibility.md) whenever the task may be affected by renamed fields, added fields, deleted fields, option changes, or other schema drift.
- Read [references/live-schema-preflight.md](./references/live-schema-preflight.md) whenever the task is preparing a Base write path, a Todo write path, or a runtime/tool contract.
- Read [references/feishu-runtime-sources.md](./references/feishu-runtime-sources.md) whenever the task needs to know where the current live Feishu resource hints come from.
- Read [references/feishu-workbench-gateway.md](./references/feishu-workbench-gateway.md) whenever the task needs to access Feishu workbench context or prepare a write plan.
- Read [references/meeting-context-recovery.md](./references/meeting-context-recovery.md) whenever the task involves a meeting note, transcript, or post-meeting update.
- Read [references/meeting-live-first-policy.md](./references/meeting-live-first-policy.md) whenever the task involves a meeting note, transcript, or post-meeting update.
- Read [references/meeting-type-classification.md](./references/meeting-type-classification.md) whenever the task involves interpreting a meeting and deciding write scope.
- Read [references/meeting-note-doc-standard.md](./references/meeting-note-doc-standard.md) whenever the task may create a meeting-note cold-memory doc.
- Read [references/meeting-output-standard.md](./references/meeting-output-standard.md) whenever the task is preparing the final user-facing output for a meeting note, transcript, or post-meeting update.

## Output Pattern

Default to this shape:

1. Meeting framing and context recovery
2. Confirmed facts and judgment
3. Structured summary
4. Recommendation-mode updates
5. Open questions or blocked items
6. Only after user confirmation: write results and return a change summary

For proposed updates, include:

- Resolved customer and `客户ID`
- Whether context recovery was completed or the run stayed in `context-limited` fallback mode
- Meeting type and resulting write ceiling
- Auditable context-recovery sources
- Extracted entities
- Target objects to update
- Create vs update decision for each object
- Facts vs judgment
- Normalized absolute dates and any date precision gaps
- Any protected fields that were intentionally left unchanged
- Any schema drift, alias fallback, or unresolved live-field mismatch
- Use Chinese section titles and Chinese structured-summary labels by default for meeting outputs
- Let recommendation-mode updates be driven by actual extracted entities, not by a fixed object list

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
