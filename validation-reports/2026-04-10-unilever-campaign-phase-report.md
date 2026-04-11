# Validation Report

## Case

- Date: `2026-04-10`
- Scenario: post-meeting update
- Customer mention: `联合利华`
- Source file: `tests/fixtures/transcripts/20260410-联合利华 Campaign活动分析优化-阶段汇报.txt`
- Validation goal: check whether the current skill can safely handle a mixed transcript containing scope clarification, delivery discussion, open questions, and tentative optimization directions

## Result

Status: `DONE_WITH_CONCERNS`

Overall judgment:

- This validation run only covered the `single-file fallback` path, not the full real workflow.
- The current skill can support this case at the level of:
  - structured extraction
  - account-side meeting summary
  - proposed updates in recommendation mode
- It should not directly write strategy-heavy fields or auto-create Todo items from this transcript alone

This means the current version is usable for analysis, but still needs tighter rules for exploratory meeting transcripts.

## Structured extraction bundle

### Top level

- `customer_mentions`
  - `联合利华`
- `context_recovery`
  - status: `not_run`
  - mode: `context-limited`
  - note: this validation did not read live `客户主数据`、最近 `客户联系记录`、`行动计划`、客户档案或历史会议资料
- `resolved_customer`
  - `company_name`: `联合利华`
  - `short_name`: `联合利华`
  - `status`: `missing`
  - `confidence`: `medium`
  - note: no live `客户ID` was resolved during this validation run
- `meeting_type`
  - dominant_type: `stage_review`
  - write_ceiling:
    - `客户联系记录`: allowed
    - meeting-note doc: allowed
    - `行动计划`: recommendation mode
    - `客户主数据`: no-write
    - Todo: no-write unless owner is explicit
- `input_types`
  - `meeting_note`

### Contacts

- `杨意`
  - organization: `神策`
  - role: internal presenter
- `赵杰`
  - organization: `联合利华`
  - role: customer-side participant
- `王奇`
  - organization: `触脉`
  - role: third-party participant
- `廖凯余`
  - organization: `神策`
  - role: internal participant

### Progress updates

- `2026-04-10` 进行了 Campaign 活动分析优化的阶段汇报
- 当前分析方向主要包括：
  - 识别关键转化和流失节点
  - 分析不同渠道和私域路径对转化的影响
  - 输出 Campaign 优化路径
- 当前可分析的画像维度主要集中在：
  - 访问深度
  - 访问时长
  - 访问间隔
  - 内容偏好
  - 是否关注微信
  - 招募来源
  - 激活来源
  - 是否参与过其他活动
  - 是否在其他活动中完成过 FPO

### Risks

- 画像分析结果如何真正应用到投放优化，当前路径不够清晰
- `招募来源` 和 `激活来源` 的业务口径未明确
- 当前用户属性可用度有限，很多静态属性缺失
- 私域渠道的分析价值与业务 KPI 价值之间存在争议
- 当前讨论中有很多探索性假设，还没有沉淀成成熟结论

### Opportunities

- 基于行为与内容偏好做差异化分群和触达
- 识别适合二次触达的人群、节点和内容
- 将阶段性行为和 FPO 转化结果建立关联
- 在 Campaign 长周期中设计更细化的运营策略

### Schedule items

- Campaign 第一阶段已在 `2026-04` 开始
- Campaign 在 `2026-08` 或 `2026-09` 存在一波高峰
  - precision gap: transcript only says `八九月份`
- 第二阶段在 `2026年下半年` 至 `2026年末` 还有一波高峰
  - precision gap: exact month not confirmed

### Communication record

- Date: `2026-04-10`
- Participants:
  - internal: `杨意`, `廖凯余`
  - customer-side: `赵杰`
  - partner-side: `王奇`
- Channel: meeting
- Summary:
  - 神策汇报了 Campaign 活动分析优化的阶段性思路和预计产出
  - 客户和合作方重点追问画像分析的可落地应用方式、渠道分析的业务价值，以及是否能真正支持投放优化
- Decisions:
  - no final business decision confirmed
  - more clarification is needed before converting the discussion into mature strategy updates

### Todos

These are recommendation-mode only. They should not become Todo automatically from this transcript alone.

- Clarify the business definition of `招募来源` and `激活来源`
- Define how portrait findings can be applied to paid media or second-touch decisions
- Validate the actual business role of private-domain channels versus paid channels
- Identify which user behaviors are meaningful triggers for second-touch
- Confirm how success will be measured beyond descriptive analysis

## Proposed updates

### `客户联系记录`

Recommended: `create`

Suggested mapping:

- `记录标题`
  - `2026-04-10｜联合利华｜Campaign活动分析优化阶段汇报`
- `联系人员`
  - `杨意；廖凯余`
- `联系人`
  - `赵杰`
- `联系日期`
  - `2026-04-10`
- `沟通要点`
  - 阶段汇报聚焦转化流失分析、渠道影响分析和 Campaign 优化路径
- `关键进展`
  - 明确了当前可分析的行为画像、内容偏好和部分用户属性维度
- `待办事项`
  - 澄清招募/激活口径，验证画像落地投放的可行路径，判断二次触达策略是否成立
- `客户顾虑/风险`
  - 客户侧对画像分析如何转化为投放动作、私域分析对 KPI 的直接价值存在疑问
- `会议纪要文档`
  - should store the meeting-note doc link after a doc is created

### Meeting-note cold-memory doc

Recommended: `create`

Reason:

- the transcript is long
- it includes exploratory reasoning, objections, and open questions
- full content should not be squeezed into Base text fields
- the formal doc should be a structured synthesized note, not the raw transcript

Recommended structure:

- Meeting background
- Participants
- Confirmed facts
- Discussion and analysis
- Open questions
- Recommended next actions
- Source records

Required disclosure:

- `本纪要由 AI 基于会议逐字稿及相关资料整理生成，用于经营沉淀与协作参考。已确认事实、分析判断与待确认项已分开展示；如与原始记录冲突，以原始记录及业务负责人确认结果为准。`

### `行动计划`

Recommended: `create or update in recommendation mode only`

Candidate actions:

- `联合利华｜澄清招募来源与激活来源口径`
- `联合利华｜验证画像分析到投放动作的应用路径`
- `联合利华｜明确二次触达的人群、节点和内容策略`

Concern:

- no confirmed owner was resolved from the transcript alone
- time window is not confirmed

### Feishu Todo

Recommended: `no-write`

Reason:

- no explicit owner can be resolved with confidence
- the action items are still partly exploratory
- semantic dedupe cannot be completed without checking existing tasks

### `客户主数据`

Recommended: `no-write`

Reason:

- the transcript is a stage review, not a mature strategy shift
- there is no resolved `客户ID` in this validation run
- the content contains open questions and challenge points rather than confirmed operating posture changes

## Open questions

- `招募来源` 和 `激活来源` 的业务口径分别是什么
- 画像结果会被用于哪类投放或再触达动作
- 哪些优化建议是客户已经接受的，哪些还只是讨论方向
- `触脉` 在这个项目中的角色是什么，是否应进入联系人或协作备注
- 是否已有对应行动计划或 Todo，避免重复创建

## Validation findings

### Finding 1

The current rules are safe enough to avoid over-writing, but they still need a stronger pattern for `exploratory transcript` cases.

Why this matters:

- this meeting contains many hypotheses, challenges, and open questions
- if the skill treats these as final conclusions, it may over-update `客户主数据` or create premature tasks

Suggested roadmap bucket:

- `M1` stability and edge-case guardrails

### Finding 2

Owner resolution is still a real blocker for turning transcript action items into Todo safely.

Why this matters:

- several next steps are meaningful
- but none of them has a clearly confirmed owner in the transcript
- forcing Todo creation here would violate the current guardrail

Suggested roadmap bucket:

- `M1` safety
- `M2` operating-loop enhancement

### Finding 3

The current rule set should explicitly distinguish `customer-side contact`, `partner-side participant`, and `internal participant` in meeting outputs.

Why this matters:

- this transcript includes customer, vendor, and internal participants at the same time
- a flat participant model can blur who should enter `联系人` versus only stay in notes

Suggested roadmap bucket:

- `M1` routing accuracy

## Final conclusion

This case does not block current use, but it does not yet count as a full real-workflow validation.

But the safe and correct output for the current version is:

- analysis
- explicit `context-limited` marker
- meeting type classification
- structured extraction
- recommendation-mode updates
- no direct strategy-field write
- no automatic Todo creation
