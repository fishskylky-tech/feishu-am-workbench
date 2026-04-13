---
title: Workbench Information Architecture
load_triggers:
  - condition: interpreting workbench layer relationships
  - skill_stage: [architecture-planning, refactoring]
load_priority: low
estimated_tokens: 770
dependencies: []
tier: L3-on-demand
---

# Workbench Information Architecture

This file defines how the Feishu account management workbench is meant to work.

## Primary source of information

- The user's direct input is the primary information source.
- Local files, public updates, and existing Feishu records are supporting sources.

## Layer 1: Customer master snapshot

- Table: `客户主数据`
- Purpose:
  - One row per customer
  - Customer key and basic identity
  - Stable goals and actuals
  - Stable operating posture
  - Latest contact or action summary
  - Link to the canonical customer archive

### Important interpretation

- This table is not for detailed history.
- This table is not for full meeting logs.
- This table is not for rapidly changing tactical noise.
- `上次接触时间` and `下次行动计划` should reflect only the latest useful snapshot item.

## Layer 2: Detail tables

These tables hang off `客户主数据.客户ID` as the foreign key for customer detail.

- `合同清单`
  - Current and actively managed contracts, renewals, collections, or execution-relevant commercial records
- `行动计划`
  - Structured customer-operating actions
- `客户关键人地图`
  - Contact-by-contact map of current and historical people
- `客户联系记录`
  - Structured communication records
- `竞品交锋记录`
  - Many-to-many bridge between customers and competitors

### Important interpretation

- These are the right place for repeatable detail updates.
- These tables are the factual detail layer that should be deduped and kept structured.
- The current Base does not yet contain a separate `客户联系计划` table. Until that changes, use `客户联系记录` as the actual communication-detail table.

## Layer 3: Competitor dimension

- `竞品` is its own master-data layer.
- `竞品交锋记录` is the cross table linking competitors to customers.
- Competitor facts should not be collapsed into customer master unless they change the customer's operating posture.

## Layer 4: Customer archive

- Location: Feishu docs folder `fld_customer_archive_example`
- Purpose:
  - Explain the customer's full picture
  - Capture the key “前世今生”
  - Summarize important detail-table information
  - Record meaningful public updates
  - Provide the basis for later strategy changes in `客户主数据`

### Important interpretation

- The archive is not a table-format document.
- The archive is not a raw event stream.
- The archive is not a meeting transcript dump.
- Each customer must have one canonical archive doc.

## Layer 5: Meeting-note cold memory

- Location: Feishu docs folder `fld_meeting_notes_example`
- Purpose:
  - Store long meeting records and transcripts
  - Keep those records lazy-loaded

### Important interpretation

- Full meeting notes belong here, not in Base long-text fields.
- Other tables should link to these docs rather than duplicate the full text.

## Layer 6: Todo execution

- Carrier: Feishu Todo list
- Purpose:
  - Remind and drive execution
  - Cover both customer-operating work and other daily tasks

### Important interpretation

- Todo is not the same as `行动计划`.
- `行动计划` is the structured operating record.
- Todo is the reminder and execution carrier.
- Todo should always have a responsible person.
- Todo dedupe should be semantic: avoid creating parallel tasks that represent the same core piece of work under slightly different wording.
- When several smaller execution steps belong to one broader customer-operating theme, prefer one parent task plus subtasks instead of many overlapping top-level tasks.

## Closed loop

The intended loop is:

1. User input and materials update the detail layer
2. Detail-layer signals are synthesized into the customer archive
3. The customer archive becomes the basis for any strategy update in `客户主数据`
4. Todo supports execution and reminders

This loop should guide every routing and write-back decision in the skill.
