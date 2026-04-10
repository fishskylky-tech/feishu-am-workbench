---
name: Schema drift
about: Report a Feishu Base or task-schema change that may break the skill
title: "[Schema drift] "
labels: schema
assignees: ""
---

## Drift type

- [ ] Field renamed
- [ ] Field deleted
- [ ] Field added
- [ ] Select option changed
- [ ] Table changed
- [ ] Task custom field changed
- [ ] Other

## Where it happened

- Base / tasklist:
- Table:
- Field:

## Old state

Describe the old field or option behavior.

## New state

Describe the new field or option behavior.

## Current skill impact

What fails, becomes ambiguous, or needs fallback?

## Safe expected behavior

Should the skill:

- [ ] auto-match via alias
- [ ] stay in recommendation mode
- [ ] require explicit user confirmation
- [ ] update cached mapping only
