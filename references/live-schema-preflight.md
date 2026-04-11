# Live Schema Preflight

Use this file when the skill or a future runtime is preparing an actual write into Feishu Base or Feishu Todo.

The goal of preflight is simple:

- resolve the live write target
- prove the write is still safe
- surface drift before any mutation happens

This is the operational contract for the schema-compatibility rules in the skill.

## Inputs

Preflight should receive:

- workspace config, if present
- the intended target object
  - Base table or Todo tasklist
- the intended semantic field slots
- the candidate values to write
- the relevant customer context
  - especially `客户ID`

The semantic field slot is the stable unit, not the raw field name.

Examples:

- `customer_master.last_contact_at`
- `customer_master.strategy_direction`
- `action_plan.completion_status`
- `todo.priority`

## Resolution order

Resolve targets in this order:

1. live table or tasklist existence
2. live field or custom-field existence
3. live field type
4. semantic slot mapping from workspace config
5. narrow alias fallback
6. cached mapping fallback
7. no-write fallback

Do not skip directly from an intended semantic slot to a guessed raw field name.

## Required checks

Before a write is allowed, preflight must confirm:

- target table still exists
- target field still exists
- field type is compatible with the intended payload
- `select` and `multi_select` options still support the intended value
- protected or guarded fields are still governed by the same policy tier
- Todo owner and tasklist references are still valid

## Type compatibility

Treat these as compatible only when the business meaning is preserved:

- `date` <- `date`
- `datetime` <- `datetime`
- `text` <- `text`
- `single_select` <- option id or exact live option label
- `multi_select` <- a set of exact live option labels or ids
- `url` <- link-like string

Treat these as blocked by default:

- `single_select` -> `text`
- `multi_select` -> `text`
- guarded strategy field -> unrelated free-text field
- user field -> plain text field, unless the workspace config explicitly allows that fallback

## Alias fallback rule

Alias fallback is allowed only when:

- the semantic slot remains the same
- the live field type remains compatible
- the alias is narrow enough that a human reviewer would make the same match

Alias fallback should be recorded explicitly in the change plan.

## Option resolution rule

For `single_select` and `multi_select`:

1. fetch live options
2. normalize the candidate value
3. try exact label match
4. try configured synonym match
5. if still unresolved:
   - strict enum: block write
   - controlled extension: recommend a new option, do not auto-create
   - text-friendly field family: move to the paired text slot if one exists and the routing rules allow it

## Drift classes

Preflight should classify drift rather than returning one undifferentiated failure.

Recommended classes:

- `table_missing`
- `field_missing`
- `field_renamed_alias_resolved`
- `field_type_changed_blocked`
- `option_missing_blocked`
- `option_synonym_resolved`
- `protected_field_policy_changed`
- `todo_custom_field_missing`
- `owner_unresolved`

## Output contract

Preflight should produce a structured report with:

- target object
- intended semantic slot
- resolved live table or tasklist id
- resolved live field or custom-field id
- resolved live field name
- resolved live field type
- candidate value
- option resolution result, if any
- drift items
- alias fallbacks used
- blocked status
- human-readable reason

Recommended status values:

- `safe`
- `safe_with_drift`
- `blocked`

## Write gate

Only allow the downstream write when every touched field returns:

- `safe`, or
- `safe_with_drift` with a fully resolved live target

If any touched field is `blocked`, the whole write for that object stays in recommendation mode.

## Review surface

The user-facing change plan should surface:

- which semantic slots were resolved normally
- which ones used alias fallback
- which ones were blocked
- which strict enums failed option resolution
- which protected fields were intentionally left unchanged

This makes schema drift visible instead of silent.
