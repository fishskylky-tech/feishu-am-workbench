# Update Routing And Idempotency

Route each extracted item to the correct object. Avoid duplicate rows and contradictory updates.

## Routing map

- Customer master snapshot
  - `客户主数据`
  - Use only for current summary, latest contact or action, archive link, and mature operating posture

- Public updates
  - Customer archive doc `最新资讯`
- Communication records
  - `客户联系记录`
  - Customer archive doc `拜访与沟通记录`
  - Meeting-note cold-memory doc, with only the link stored in the table
- Historical cooperation and delivery facts
  - Customer archive doc `合作历史`
- Contacts and org status
  - `客户关键人地图`
  - Customer archive doc `组织架构与关键联系人`
- Risks and opportunities
  - Customer master operating fields
  - Customer archive doc `当前经营判断`
  - Related risk or competitor tables if present
- Competitor master facts
  - Competitor master table when the task is about the competitor itself
- Competitor encounters
  - `竞品交锋记录` when the competitor is discussed in the context of a customer
- Contracts and collections
  - Customer archive doc `合作历史`
  - `合同清单` only when the contract is current, still valid, under renewal, under collection tracking, or otherwise needed for active pipeline management
- Todos and schedules
  - `行动计划`
  - Feishu Todo
  - Customer archive doc `当前待办` when useful

## Cold memory rule

- Full meeting transcripts or long meeting notes should live in Feishu docs, not inside Base long-text fields.
- `客户联系记录` should store only the meeting-note document link plus the concise structured summary needed for day-to-day use.
- Load the meeting-note doc only when deeper backtracking is needed.
- Default meeting-note folder: `OlBCfU7IKl2oSbd09lXckKJlnTc`
- The formal meeting-note doc should be a structured synthesized note, not the raw transcript by default.
- The formal meeting-note doc should include a short AI-generated disclosure and a source-record section.

## Multi-brand naming rule

- If a single `客户ID` contains multiple brands or project tracks, keep the customer unified under that one `客户ID`.
- Do not add a cross-platform `品牌` field just to support one exceptional customer.
- Instead, use a stable text prefix in affected objects:
  - `合同清单.关键节点`
  - `合同清单.备注`
  - `行动计划` title or action text
  - `客户联系记录` subject or summary
  - Meeting-note doc titles
- Preferred format: `品牌｜主题`
  - Example: `Wilson｜项目增购`
  - Example: `始祖鸟｜小程序 Revamp`
  - Example: `Salomon｜埋点需求`

## Layer intent

- `客户主数据`
  - One-row customer index and snapshot
  - Not a detailed running log
- Detail tables
  - Structured facts by dimension
  - Best place for repeatable updates and dedupe rules
- `客户档案`
  - Whole-account narrative and synthesis
  - Basis for strategy interpretation, not a raw event stream
- Feishu Todo
  - Reminder and execution carrier
  - Every new task must have a clear responsible person
  - For the `神策` tasklist, set validated custom fields when applicable:
    - `客户` for customer-related tasks
    - `优先级` for all new tasks

## Idempotency keys

Use these keys to decide update versus create.

- `客户联系记录`
  - `客户ID + 联系日期(if known) + 记录标题`
  - If `联系日期` is missing, fall back to `客户ID + 记录标题`
  - Use `联系人员` for internal participants and `联系人` for customer-side participants
  - Store the cold-memory URL in `会议纪要文档`
- Meeting-note doc
  - `客户ID + 会议日期 + 文档类型`
- `客户关键人地图`
  - `客户ID + 姓名`
  - Prefer `最近联系时间`, `关键诉求`, `备注`, and `动态备注` as the default write targets
  - Treat `上次沟通（停用）` as legacy unless there is a specific reason to maintain it
- `行动计划`
  - `客户ID + 动作主题 + 时间窗口`
  - If the customer has multi-brand tracks, include the brand prefix inside the action theme
- Feishu Todo
  - Use semantic dedupe, not literal dedupe
  - Check for near-duplicates by customer, verb, object, and time window
  - Examples of likely duplicates:
    - `跟进换盘评估` vs `推进换盘方案确认`
    - `补齐渠道追踪权限` vs `梳理渠道追踪权限问题`
  - If a task is the same core job with narrower execution steps, prefer creating or proposing a subtask under the existing parent task
  - If a task is the same core job with newer timing or clearer scope, prefer updating the existing task rather than creating a second one
  - If several sibling tasks point to the same customer and the same operating theme, consider one parent task plus subtasks instead
- `合同清单`
  - `客户ID + 合同开始/签约时间 + 合同类型 + 金额口径`
  - Only apply this key when the contract is eligible for `合同清单` under the active-tracking rule above
- `最新资讯`
  - `客户ID + 来源链接`

If a likely existing row is found, update it instead of creating a duplicate.

## Change plan format

Before writing, produce a change plan with:

- Whether context recovery succeeded or remained `context-limited`
- Meeting type
- Write ceiling applied for this meeting type
- Target object
- Create or update
- Unique key or matching basis
- Key fields to change
- Fact source
- Whether the content is fact or judgment
- Which layer the target belongs to: snapshot, detail, archive, or reminder
- Real target fields to write, using current Base schema rather than generic placeholders
- Whether each field was resolved by:
  - direct live match
  - alias fallback
  - or remained unresolved
- For Todo items specifically:
  - Responsible person
  - Dedupe result: create parent / create subtask / update existing / no-write

## Schema preflight

Before any Base write:

1. Read the live table schema for the target table.
2. Confirm the destination field still exists.
3. Confirm the field type still supports the intended value shape.
4. If the field is `select` or `multi_select`, fetch live options and resolve against those options.
5. If the cached field name is missing, attempt semantic alias matching.
6. If no safe match exists, do not write. Keep the item in recommendation mode and call out the schema drift.

Alias fallback is a compatibility tool, not a default write path.
Prefer direct live matches whenever possible.

## Meeting type write ceiling

When the input is a meeting note or transcript:

- `stage_review`
  - `客户联系记录`: allowed
  - meeting-note doc: allowed
  - `行动计划`: recommendation mode by default
  - `客户主数据`: no-write by default
  - Todo: no-write unless owner and execution commitment are explicit
- `alignment_clarification`
  - `客户联系记录`: allowed
  - meeting-note doc: allowed when useful
  - `行动计划`: recommendation mode by default
  - `客户主数据`: no-write by default
  - Todo: no-write unless owner is explicit
- `decision_confirmation`
  - `客户联系记录`: allowed
  - meeting-note doc: allowed
  - `行动计划`: allowed
  - Todo: allowed after owner resolution and dedupe
  - `客户主数据`: only if the decision clearly changes account posture
- `unknown`
  - apply the stricter ceiling and prefer recommendation mode

## Write ordering

1. Structured tables
2. Customer archive doc and meeting-note docs
3. Feishu Todo

This means:

1. Detail tables and any eligible master-table snapshot fields
2. Customer archive and cold-memory docs
3. Todo reminders

## Partial failure handling

- If a later write fails, return:
  - Completed writes
  - Failed writes
  - Any follow-up needed
- Do not hide partial success.
- Do not invent fallback values just to complete a write.
