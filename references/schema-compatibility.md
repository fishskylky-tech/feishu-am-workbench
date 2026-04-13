---
title: Schema Compatibility
load_triggers:
  - skill_stage: [preflight, schema-check]
  - condition: schema drift detected or field mapping needed
load_priority: medium
estimated_tokens: 896
dependencies: [live-schema-preflight, actual-field-mapping]
tier: L3-scenario-write
---

# Schema Compatibility

Use this file when the Feishu Base schema may have changed since the cached mapping was last reviewed.

The goal is not to freeze the Base forever. The goal is to keep the skill safe and usable as the Base evolves.

## Design principle

The skill should store stable operating rules, not a permanently fixed schema snapshot.

Use this order of truth:

1. Live schema discovery
2. Narrow semantic alias matching
3. Cached mapping files
4. No-write fallback

If these layers disagree, prefer safety over convenience.

## What should stay stable in the skill

These belong in the skill and should change rarely:

- Workbench layer definitions
  - master snapshot
  - detail tables
  - archive
  - Todo
- Protected-field policy
- Customer archive uniqueness
- Absolute-date rule
- Historical-contract routing rule
- Meeting-note cold-memory rule
- Todo owner and semantic-dedupe rule

These are business rules, not schema snapshots.

## What should be discovered live

Before writing into Base, discover live:

- table existence
- field existence
- field type
- single-select and multi-select options
- whether a field is still writable in the intended way

Before writing into Feishu Todo at scale, confirm live:

- tasklist still exists
- custom field still exists
- select-type custom field options still exist
- owner can still be resolved to a valid member

This avoids hard failures when the user:

- adds a new option
- renames a field
- deletes an old field
- adds a new table
- retires an old table
- changes a task custom field
- retires a task priority option

## Alias matching

Alias matching is allowed only as a compatibility fallback.

Good uses:

- `备注信息` -> `动态备注`
- `上次沟通` -> `上次沟通（停用）`
- a future rename like `最近接触时间` -> `上次接触日期`

Bad uses:

- mapping one strategy field into another just because both sound similar
- writing into a free-text field because the intended select field disappeared
- redirecting a protected field write into an unprotected field

If the match is not narrow and semantically clear, stop and surface the drift.

## Select option resolution

For `select` and `multi_select` fields:

1. Read live options first.
2. Normalize the candidate value.
3. Try exact match.
4. Try configured synonym match if the business meaning is identical.
5. If still not found:
   - for strict enums: no-write, ask for confirmation
   - for controlled extension: suggest adding a new option, do not auto-create
   - for text-friendly dimensions: prefer the text field instead of forcing a new option

Do not rely on a fully static option registry.

## Suggested enum policy

### Strict enums

These should almost never auto-expand:

- `行动计划.完成状态_单选`
- `行动计划.行动类型_单选`
- `客户主数据.26年策略方向`
- `客户主数据.续费风险`
- similar operating-posture fields

### Controlled extension

Fields that may evolve but still need governance:

- source-like labels
- phase-like labels
- non-core classification fields

For these, the skill may recommend adding a value, but should not silently create one.

## Schema drift behavior

If live schema drift is detected:

- continue only if the write target can still be resolved safely
- record the drift in the change plan
- if resolution is unsafe, do not write

Drift should not be silent.

## Cached mapping maintenance

The cached mapping files are still useful:

- they speed up reasoning
- they document current platform intent
- they make reviews easier

But they are not the only truth.

Update cached mappings when:

- a real field rename is confirmed
- a table role changes
- a high-use select field gets new options that matter to routing or normalization
- a task custom field guid or option set changes

Do not require a mapping-file edit for every small option tweak if live discovery already handles it.

## Practical write rule

When writing:

1. Resolve customer and `客户ID`
2. Resolve target layer
3. Resolve live table and field
4. Resolve live option if needed
5. Apply protection rules
6. Apply idempotency rules
7. Write only if every step is safe

If any step is unsafe, stop at recommendation mode.
