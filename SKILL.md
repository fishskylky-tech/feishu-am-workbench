---
name: feishu-am-workbench
version: 0.2.11
author: fishskylky-tech
description: >
  Personal AM workflow skill for Feishu-based account management. Use this skill whenever the user
  mentions: 飞书工作台, 客户档案, 会议纪要, 行动计划, 客户主数据, 合同, 联系记录, 竞品, Todo, 客户更新, 会前准备, 会后总结,
  account analysis, meeting prep, post-meeting synthesis, or wants to write back to Feishu Base, Docs, or Todo.
  Also trigger when the user pastes a meeting transcript, shares a customer file, or asks questions like
  "这个客户最近怎样", "帮我整理一下今天的会议", "更新一下飞书上的行动计划", "帮我准备一下明天的拜访". When in doubt, use this skill.
tags: [feishu, account-management, am-workflow, chinese, crm, pipeline]
repository: https://github.com/fishskylky-tech/feishu-am-workbench
compatibility: requires lark-cli in PATH; Python 3.10+ for runtime/ modules; personal Feishu token configured in environment
load_strategy: progressive
tier:
  L1: frontmatter + core_workflow
  L2: main body
  L3: references/*.md (on-demand)
triggers:
  keywords: [飞书工作台, 客户档案, 会议纪要, 行动计划, Todo, 客户更新]
  patterns: [meeting prep, post-meeting, account analysis, customer update]
  file_types: [transcript, meeting notes, customer materials]
---

# Feishu AM Workbench

## Overview

Use this skill for a personal AM workflow built around Feishu Base, docs, and Todo. It turns mixed inputs into a structured account view, proposes updates across the workbench, and only writes after explicit user confirmation.

## Runtime Prerequisites

This skill has an optional local runtime layer (`runtime/`) for live Feishu access, schema preflight, and write guard. To use live features:

- `lark-cli` must be in PATH and authenticated with a valid Feishu token
- Python 3.10+ required for `runtime/` modules
- Personal runtime hints should come from environment variables first; fallback examples are in `references/live-resource-links.example.md`

Run `python3 -m runtime <skill-path>` before first use. If the runtime is unavailable, stay in recommendation mode.

### Generating actual-field-mapping.md

The `references/actual-field-mapping.md` file contains a cached snapshot of the live Feishu schema. It must follow specific format requirements for `runtime/runtime_sources.py` to parse it correctly. See the "Format Requirements" section in that file for details.

To generate or update this file:

1. **List tasklists**: `lark-cli task tasklists list`
2. **Get tasklist details**: `lark-cli task tasklists get --params '{"tasklist_guid": "<guid>"}'`
3. **Get sample tasks**: `lark-cli task tasks list --params '{"tasklist_guid": "<guid>", "limit": 5}'`
4. **List Base tables**: `lark-cli base +table-list --base-token <token>`
5. **Get field schema**: `lark-cli base +field-list --base-token <token> --table-id <table>`
6. **Get field details** (for select options): `lark-cli base +field-get --base-token <token> --table-id <table> --field-id <field>`

**Important**: `lark-cli base +field-list` may return empty `options` arrays for `select` and `multi_select` fields. Use `+field-get` for each field individually to retrieve option values and GUIDs.

Follow the format requirements documented in `actual-field-mapping.md` when updating the file to ensure the runtime can parse it correctly.

The workbench is layered:

- `客户主数据`: index and snapshot layer
- Detail tables: `合同清单` / `行动计划` / `客户关键人地图` / `客户联系记录` / `竞品交锋记录`
- `客户档案`: narrative archive and decision-support layer
- Feishu Todo: reminder and execution layer

## Use This Skill When

- The user wants account analysis from local files, Feishu records, notes, or public information.
- The user wants meeting prep, post-meeting synthesis, or customer strategy suggestions.
- The user wants to update customer archives, master data, action plans, contact maps, contract records, or Todo.
- The input mixes several dimensions at once, such as contacts, competitors, contracts, risks, opportunities, schedules, and action items.

## Core Workflow

1. Identify the customer intent and candidate customer names from the input.
2. Resolve one `客户ID` from `客户主数据` before planning any write.
3. If the task touches Feishu workbench data, use the Feishu workbench gateway first. See [references/feishu-workbench-gateway.md](./references/feishu-workbench-gateway.md).
4. For meeting notes or transcripts, run the live-first gate before formal analysis. See [references/meeting-context-recovery.md](./references/meeting-context-recovery.md) and [references/meeting-live-first-policy.md](./references/meeting-live-first-policy.md).
5. Classify the meeting type before deciding write scope. See [references/meeting-type-classification.md](./references/meeting-type-classification.md).
6. Extract all relevant entities before routing anything. Do not write while still extracting.
7. Read only the minimum extra context needed from local files, Feishu workbench objects, and public sources if requested.
8. Before any write plan, run live schema preflight for every Base table and field you may touch.
9. Separate facts from judgment. Use [references/fact-grading.md](./references/fact-grading.md).
10. Produce two outputs:
   - Account analysis and recommendations
   - A structured change plan listing each target object, whether it is a create or update, and the key fields involved
11. Wait for explicit confirmation before any Feishu write.
12. After confirmation, write structured tables first, archive and meeting-note docs second, and Todo last.
13. Report success, partial failure, schema drift, or blocked status clearly.

## Hard Rules

- Always use `客户主数据` as the source of truth for `客户ID`. Downstream routing and archive lookup depend on one stable customer identifier.
- If customer matching is ambiguous, stop and ask for clarification before writing. Wrong customer resolution is worse than a blocked write.
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
- All date output and write-back must use absolute time expressions — never relative ones like `近期`, `昨天`, `明天`, `今年`, or `明年`. If the source is vague, keep the highest-confidence absolute form available and flag the precision gap.
- Do not mix public news into meeting notes, and do not mix meeting notes into `最新资讯`.
- Store full meeting notes as Feishu docs and keep only the document link in tables. Treat those docs as cold memory that should be loaded only when needed.
- Unless the user says otherwise, store meeting-note cold-memory docs in the dedicated Feishu folder `fld_meeting_notes_example`.
- For meeting-note handling, do not treat the transcript as self-sufficient if recoverable context exists in Feishu records or customer archive materials.
- For meeting-note handling, default to a live-first attempt. Do not stay on single-file analysis if gateway Stage 1-3 can run.
- For meeting-note handling, run the meeting live-first execution gate before formal analysis. Do not output a formal context-recovery result, meeting type, or write ceiling before the gate result is known.
- For meeting-note handling, do not conclude that live lookup is unavailable just because no obvious env var or direct config is visible. Check the repository runtime source layer first.
- For meeting-note handling, determine the meeting type first and let the meeting type define the default write ceiling.
- For meeting-note handling, the scenario should call foundation primitives explicitly. Do not rely on the foundation to assemble a default meeting context bundle.
- For meeting-note handling, do not output `completed`、`partial`、`context-limited` context recovery unless the foundation was actually executed. If the foundation was not executed, mark the run as `not-run`.
- Never store a raw transcript as the formal meeting-note doc. Cold memory should contain structured notes a future reader can act on. See [references/meeting-note-doc-standard.md](./references/meeting-note-doc-standard.md).
- Do not present inferred business judgment as objective fact.
- Do not treat historical plans, modelled incentives, or draft commercials as actual revenue unless the source clearly says they were signed and paid.
- By default, historical contracts belong in the customer archive doc, not in `合同清单`. Use `合同清单` only for current or still-operational contracts that matter to active tracking such as validity, renewal, collections, or ongoing execution.
- Each customer must have only one canonical customer archive doc. Before creating or linking any archive content, first find the existing archive linked from customer master data and update that doc instead of creating a second archive.
- If the archive link in customer master is empty, invalid, or obviously stale, search the customer-archive folder by `客户ID` and `简称` before creating a new archive doc.
- If one `客户ID` covers multiple brands, product lines, or project tracks, do not add a generic `品牌` field just for that customer. Use a stable text prefix such as `品牌｜主题` in titles, key nodes, notes, and action subjects instead.
- `客户档案` is neither a table dump nor a running log. It should explain the customer's full picture, historical arc, and the reasoning behind strategy changes.
- `行动计划` and Feishu Todo are not the same thing. `行动计划` is the structured customer-operating detail table. Todo is the reminder and execution carrier.
- Any new Feishu Todo task must have an explicit, resolvable owner. If no owner can be resolved with confidence, surface that gap and hold task creation.
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
- Risks and opportunities
- Key progress, blockers, and Todos
- Schedules and milestone dates
- Public updates, communication records, and account judgment

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
- Use Chinese section titles and structured-summary labels by default for meeting outputs
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
