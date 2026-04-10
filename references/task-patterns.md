# Task Patterns

Use these patterns as defaults.

## Meeting prep

Input may be a customer name, meeting date, agenda, or a short note from the user.

Output should include:

- Current account status
- Recent key events
- Important contacts
- Risks and opportunities
- Suggested questions
- Suggested target outcome for the meeting
- Any records that look stale in Feishu

## Post-meeting update

Input may be a meeting note, transcript, or user summary.

Output should include:

- Structured extraction bundle
- Analysis and account judgment
- Proposed changes across all affected objects
- Explicit `客户联系记录` mapping when applicable:
  - `记录标题`
  - `联系人员`
  - `联系人`
  - `联系日期`
  - `沟通要点`
  - `关键进展`
  - `待办事项`
  - `客户顾虑/风险`
  - `会议纪要文档`
- Whether a meeting-note cold-memory doc should be created
- Todo decision for each action item:
  - create task
  - create subtask
  - update existing task
  - keep only in `行动计划`
- Absolute dates only, with any missing precision explicitly called out
- Open questions
- Wait for confirmation before writing

## Archive refresh

Use when the user provides a customer folder or asks for a deeper customer profile refresh.

Process:

1. Read the existing archive
2. If the archive link in customer master is blank, invalid, or stale, search the archive folder by `客户ID` and `简称` before creating a new archive
3. Read the relevant local historical materials
4. Compare against customer master and related tables
5. Propose archive updates and related table updates together

If the customer contains multiple brands or tracks under one `客户ID`:

6. Keep one canonical archive doc, but split analysis into brand or project sub-tracks inside the archive
7. Use `品牌｜主题` text prefixes in any related tables instead of proposing a new generic `品牌` field

When refreshing the archive, explicitly test for these mismatches:

- The platform says the customer is stable, but materials show recent org change
- The relationship is healthy, but system performance or environment issues are blocking usage
- The account is marked as low-touch, but the actual delivery scope is deep and ongoing

## Minimal archive bootstrap

Use when a customer has no archive doc link yet.

Process:

1. Build a minimal archive with basic information, current judgment, key contacts, and current actions
2. Backfill the archive link into customer master
3. Expand the archive later when deeper materials are available

## Public update synthesis

Use when the user asks for recent customer news or market context.

Process:

1. Gather public sources
2. Separate public facts from AM judgment
3. Draft `最新资讯`
4. Suggest any linked strategy updates
5. Wait for confirmation before writing

## Constraint diagnosis

Use when a customer appears stalled despite a good relationship.

Process:

1. Separate relationship quality from execution reality
2. Check whether the blocker is organizational, technical, commercial, or competitive
3. Update the account judgment so the user does not confuse a blocked account with a low-value account

## Todo creation guardrail

Use whenever the skill is about to create a Feishu Todo item.

Process:

1. Resolve the responsible person first
2. If no clear owner exists, do not create the task yet
3. For the `神策` tasklist, also resolve:
   - `客户` custom field when the task is customer-related
   - `优先级` custom field
4. Search existing tasks for semantic near-duplicates, not just exact title matches
5. If an existing task already covers the same core job:
   - update the existing task when the new input mainly adds scope, timing, or clarity
   - create a subtask when the new input is one execution step under an existing broader task
6. Only create a new top-level task when there is no strong semantic overlap
