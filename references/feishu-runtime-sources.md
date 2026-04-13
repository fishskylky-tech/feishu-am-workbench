# Feishu Runtime Sources

Use this file when the skill needs to access the current live Feishu workbench environment.

This file exists to solve a practical problem:

- the current skill already depends on real Feishu resources
- those resources are not yet cleanly centralized
- the skill still needs a stable way to know where to look right now

This is a runtime source inventory for the current personal environment.
It is not a future-facing multi-user configuration model.

## Purpose

Before attempting:

- customer context recovery
- customer resolution
- meeting-note doc lookup
- archive lookup
- Todo lookup
- Base write planning

the skill should first determine which resource source it is using.

## Source priority

Use this order:

1. Environment variables (`FEISHU_AM_*`)
2. Current example resource hints in the skill repository
3. Cached mapping in `references/actual-field-mapping.md`
4. Stable architecture rules in `references/workbench-information-architecture.md`
5. No-write / context-limited fallback

Do not assume a separate private config exists.
Real tokens should be provided by environment variables, not committed files.

Before declaring runtime sources unavailable, the skill must first read:

- `references/feishu-runtime-sources.md`
- `references/live-resource-links.example.md` when present
- `references/actual-field-mapping.md`
- `references/workbench-information-architecture.md`

## Current known runtime sources

### Base tables and fields

Current source:

- [actual-field-mapping.md](./actual-field-mapping.md)

Use this file to understand:

- current table set
- current field names
- current Todo custom field guids
- known current option snapshots

Treat it as:

- the current runtime hint layer
- not the final truth

### Customer archive folder

Current source:

- [workbench-information-architecture.md](./workbench-information-architecture.md)

Current known folder:

- `fld_customer_archive_example`

### Meeting-note cold-memory folder

Current sources:

- [SKILL.md](../SKILL.md)
- [update-routing.md](./update-routing.md)
- [workbench-information-architecture.md](./workbench-information-architecture.md)

Current known folder:

- `fld_meeting_notes_example`

### Todo tasklist and custom fields

Current source:

- [actual-field-mapping.md](./actual-field-mapping.md)

Current known resources:

- `tasklist_guid`: `00000000-0000-4000-8000-000000000001`
- `客户` custom field guid: `a7009aff-7d85-4378-82c9-1584873f469d`
- `优先级` custom field guid: `f7587037-8ad1-443c-b350-f6600e0ccadd`

## Runtime expectations

When the skill uses these current runtime sources, it should explicitly state:

- which source file supplied the resource hint
- whether the object was then confirmed live
- whether the result stayed in `context-limited` or `recommendation-only` mode

## Failure handling

If the skill cannot determine a required resource from the current runtime sources:

- do not invent a replacement
- do not silently switch to a guessed object
- mark the run as one of:
  - `resource-unresolved`
  - `context-limited`
  - `write-blocked`

Do not say "no direct workbench config is available" unless this repository source layer was actually checked first.

## Near-term rule

Until a real private runtime source exists, this file and the referenced runtime hint files are the operational source layer for the current personal workflow.
