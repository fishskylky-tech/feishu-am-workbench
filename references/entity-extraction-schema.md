# Entity Extraction Schema

Use this schema before any routing or write-back. One input can populate many slots.

## Required top-level fields

- `customer_mentions`
  - Raw names seen in the input
- `resolved_customer`
  - `customer_id`
  - `company_name`
  - `short_name`
  - `confidence`
  - `status`: `resolved`, `ambiguous`, or `missing`
  - `sub_tracks`
    - Optional brand, business-line, or project-track labels that still roll up to the same `客户ID`
- `input_types`
  - Any of: `user_note`, `meeting_note`, `historical_material`, `public_news`, `contract_material`, `feishu_record`

## Extractable entities

- `contacts`
  - Name
  - Role or title
  - Current vs historical
  - Influence or buying role if clear
  - Source note
- `org_changes`
  - Joined, left, role changed, team changed
  - Re-org, business unit merge, management restructuring, unclear ownership
- `competitors`
  - Competitor name
  - Context
  - Strength or risk signal
- `contracts`
  - Contract type
  - Sub-track or brand prefix when relevant
  - Start date
  - End date
  - Amount
  - Currency
  - Amount type
  - Paid amount
  - Unpaid amount
  - Evidence
- `risks`
  - Description
  - Category
  - Severity
  - Evidence
  - Suggested categories:
    - relationship
    - organization
    - system_availability
    - delivery
    - commercial_timing
    - competitor
- `opportunities`
  - Description
  - Sub-track or brand prefix when relevant
  - Scope
  - Stage
  - Evidence
- `progress_updates`
  - Milestones, blockers, decisions, dependencies
  - Sub-track or brand prefix when relevant
  - Include system bottlenecks, environment constraints, and support escalations when they materially affect account progress
- `todos`
  - Action
  - Owner
  - Due date
  - Why it matters
- `schedule_items`
  - Meeting dates
  - Follow-up dates
  - Launch dates
  - Renewal dates
  - Date precision
    - exact day
    - year-month
    - year-quarter
    - year only
- `public_updates`
  - Title
  - Source
  - Link
  - Publish date
  - Event date if different
  - Summary
- `communication_records`
  - Date
  - Participants
  - Channel
  - Summary
  - Decisions
- `account_judgment`
  - Renewal risk
  - Expansion chance
  - Recommended strategy
  - Recommended next actions
  - Constraint type
    - relationship good but org blocked
    - relationship good but system blocked
    - relationship and execution both healthy

## Extraction rules

- Extract first, route second.
- Keep uncertain items with a confidence note instead of dropping them silently.
- If an input contains both facts and judgments, separate them.
- A date in natural language such as "tomorrow" should be normalized to an absolute date when the context is clear.
- Never keep relative date language in the final structured output or write-back plan.
- If the source only supports partial precision, keep that absolute precision explicitly, for example:
  - `2026-04-10`
  - `2026-04`
  - `2026年第二季度`
  - `2026年4月`
- If the date is too vague to normalize with confidence, stop and ask the user to confirm before writing.
- If customer matching is ambiguous, extraction can continue, but write-back must stop.
