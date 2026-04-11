# Meeting Type Classification

Use this file after context recovery and before routing updates from a meeting input.

The purpose is to avoid treating every meeting as if it had the same write authority.

## Required meeting types

At minimum, classify each meeting into one of:

- `stage_review`
- `working_session`
- `alignment_clarification`
- `decision_confirmation`
- `delivery_issue_handling`
- `retrospective`
- `unknown`

## Type definitions

### `stage_review`

Typical signals:

- phased progress report
- exploratory findings
- early recommendations
- many open questions
- stakeholder challenge without final decision

Default write ceiling:

- allow `客户联系记录`
- allow meeting-note cold-memory doc
- allow recommendation-mode `行动计划`
- block direct `客户主数据` strategy-field updates
- block automatic Todo creation unless owner and execution commitment are explicit

### `working_session`

Typical signals:

- detailed problem solving
- tactical design or analysis
- active back-and-forth on implementation or optimization

Default write ceiling:

- allow `客户联系记录`
- allow meeting-note cold-memory doc
- allow `行动计划` candidates
- Todo still requires explicit owner
- master-data updates only if the session clearly changes current account posture

### `alignment_clarification`

Typical signals:

- definitions, scope, metric, or role clarification
- disagreement on terms or expected outcomes
- no final commitment yet

Default write ceiling:

- allow `客户联系记录`
- allow recommendation-mode follow-up items
- block strong strategy updates
- block automatic Todo creation unless ownership is explicit

### `decision_confirmation`

Typical signals:

- explicit agreement
- accepted plan or next step
- confirmed owner, scope, or timeline

Default write ceiling:

- allow `客户联系记录`
- allow `行动计划`
- allow Todo when owner and dedupe are clear
- allow carefully scoped master-data update if the decision actually changes operating posture

### `delivery_issue_handling`

Typical signals:

- blockers
- incident-like issues
- usage, environment, system, or delivery problems

Default write ceiling:

- allow `客户联系记录`
- allow `行动计划`
- allow Todo with explicit owner
- master-data update only if the issue changes account risk or posture meaningfully

### `retrospective`

Typical signals:

- post-period review
- what worked / what failed
- lessons, not immediate execution

Default write ceiling:

- allow `客户联系记录`
- allow archive synthesis
- action items only if explicitly agreed
- block casual master-data strategy churn

### `unknown`

If type is uncertain:

- prefer the stricter ceiling
- recommendation mode by default

## Classification rule

If multiple types appear in one meeting:

- choose the dominant type for write ceiling
- record secondary types in notes

## Participant rule

Meeting outputs should distinguish:

- internal participants
- customer-side participants
- partner-side participants

Default mapping:

- `联系人员`
  - internal participants
- `联系人`
  - customer-side participants
- partner-side participants
  - keep in note context unless there is a separate reason to update contact map or collaboration notes
