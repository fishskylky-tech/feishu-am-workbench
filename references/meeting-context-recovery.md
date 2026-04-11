# Meeting Context Recovery

Use this file before interpreting a meeting note, transcript, or post-meeting summary.

Also apply [meeting-live-first-policy.md](/Users/liaoky/.codex/skills/feishu-am-workbench/references/meeting-live-first-policy.md).

The default rule is:

- do not treat a meeting file as self-sufficient if recoverable context exists elsewhere

For real post-meeting handling, the skill should first recover enough background to answer:

- why this meeting happened
- what account thread it belongs to
- whether this is follow-up, escalation, review, planning, or decision confirmation

Only if no reliable background can be found should the skill fall back to single-file analysis.

## Minimum recovery order

Before deep interpretation, try to read in this order:

1. `客户主数据`
   - resolve `客户ID`
   - read current snapshot and archive link
2. recent `客户联系记录`
   - especially the last 2 to 5 relevant records
3. recent `行动计划`
   - open items, overdue items, and recently completed items
4. customer archive doc
   - current judgment
   - recent communication thread
   - known blockers and opportunities
5. related meeting-note docs
   - if the current meeting appears to continue a prior thread

This is not an excuse to read everything every time.
Read the minimum needed to restore context.

## Questions context recovery must answer

Before routing updates, the skill should try to determine:

- what was the trigger for this meeting
- what outcome the parties were seeking
- whether this is:
  - stage review
  - working session
  - alignment / clarification
  - decision meeting
  - delivery issue handling
  - retrospective
- whether the current discussion continues an existing action thread
- whether the proposed actions are new or just progress on existing items

## Recovery log

When context recovery is used, the output should make the recovery auditable.

At minimum, record:

- `上下文恢复状态`
  - completed / partial / context-limited
- `已使用资料`
  - which records, docs, or local files were actually read
- `关键补充背景`
  - which important facts came from recovered context rather than the meeting file itself
- `未找到但应存在的资料`
  - records or docs that should ideally exist but were not found

Do not hide context recovery behind a vague sentence such as “结合历史资料”.
The user should be able to tell what was actually used.

## Fallback behavior

If the skill cannot recover enough background:

- continue with extraction
- mark the case as `context-limited`
- lower confidence on account judgment
- avoid strong master-data updates
- prefer recommendation mode

`context-limited` is allowed only after the scenario actually attempted live foundation calls.
It must not be used when the scenario simply stayed on a single-file analysis path without calling the foundation.

If the foundation was not called, record the case as:

- `上下文恢复状态`: `not-run`
- reason: foundation not executed

## Validation rule

A meeting-note scenario should not be marked as “real workflow validated” unless:

- the customer was resolved from live source of truth, or
- the validation explicitly states it was only a single-file fallback run

## Technical interface

This file defines recovery requirements, not a default runtime bundle.

For meeting scenarios, the caller should explicitly invoke foundation capabilities in this order:

1. resolve customer from live `客户主数据`
2. query only the needed Base rows by `客户ID`
3. read archive doc only if master data or the meeting thread points to it
4. read related meeting-note docs only if the current note appears to continue a prior thread

The caller must perform step 1 before it can claim:

- `上下文恢复状态: completed`
- `上下文恢复状态: partial`
- `上下文恢复状态: context-limited`

If step 1 was not executed, the scenario must stay in:

- `上下文恢复状态: not-run`

The foundation should only return raw query results or raw document content.
It should not silently assemble a default context package for the meeting scenario.

If the scenario needs auditable recovery output, the scenario layer should build that output itself from:

- the raw customer resolution result
- the raw Base query results it actually requested
- the raw documents it actually read
