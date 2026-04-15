---
title: Feishu Runtime Sources
load_triggers:
  - condition: runtime needs to discover resource hints
  - skill_stage: [resource-resolution]
load_priority: medium
estimated_tokens: 571
dependencies: [feishu-workbench-gateway]
tier: L3-on-demand
---

# Feishu Runtime Sources

Use this file when the skill needs to understand the current live Feishu workbench runtime contract.

This file defines one rule for the current personal environment:

- live runtime truth comes from private runtime input in the current process environment
- local `.env` may be used only to load those same values into the environment
- checked-in repository docs are descriptive only and must not act as live runtime fallback

It is not a future-facing multi-user configuration model.

## Purpose

Before attempting:

- customer context recovery
- customer resolution
- meeting-note doc lookup
- archive lookup
- Todo lookup
- Base write planning

the skill should first determine which private runtime input it is using.

## Source priority

Use this order:

1. Process environment variables (`FEISHU_AM_*`)
2. Optional local `.env` loading only insofar as it hydrates those same environment variables
3. If required values are still missing: stop the live path and report a blocked diagnostic

Do not assume a separate private config exists.
Do not treat checked-in repository docs, examples, cached mappings, or architecture notes as live runtime truth.

## Current known runtime sources

### Base tables and fields

Current live source:

- `FEISHU_AM_WORKBENCH_BASE_URL` and/or dedicated `FEISHU_AM_*` environment variables

Files such as [actual-field-mapping.md](./actual-field-mapping.md) remain useful as operator documentation, but must not populate live runtime hints.

### Customer archive folder

Current live source:

- `FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER`

### Meeting-note cold-memory folder

Current live source:

- `FEISHU_AM_MEETING_NOTES_FOLDER`

### Todo tasklist and custom fields

Current live source:

- `FEISHU_AM_TODO_TASKLIST_GUID`
- `FEISHU_AM_TODO_CUSTOMER_FIELD_GUID` when customer custom field support is needed
- `FEISHU_AM_TODO_PRIORITY_FIELD_GUID` when priority custom field support is needed

Static GUIDs in repository docs are examples only.

## Runtime expectations

When the skill uses these current runtime sources, it should explicitly state:

- which environment variable supplied the resource hint
- whether the object was then confirmed live
- whether the result stayed in `context-limited` or `recommendation-only` mode

## Failure handling

If the skill cannot determine a required resource from the current runtime sources:

- do not invent a replacement
- do not silently switch to a guessed object
- do not fall back to checked-in repo files as truth
- mark the run as one of:
  - `blocked`
  - `context-limited`
  - `write-blocked`

Diagnostic output should default to:

- conclusion
- reason
- next action

## Near-term rule

Until a richer private configuration model exists, the operational rule is simple: private env is authoritative, `.env` is convenience-only, and repo docs are descriptive only.
