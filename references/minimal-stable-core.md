# Minimal Stable Core

Use this file when changing the skill, config shape, or runtime integration.

Its purpose is to reduce avoidable rework.

The rule is simple:

- keep the core contract small
- keep the extension surface flexible
- do not hard-code runtime details into the stable layer

## What belongs to the stable core

These should change rarely and only with strong justification:

- workbench layer model
  - `客户主数据`
  - detail tables
  - archive doc
  - Todo
- customer resolution through `客户主数据`
- extraction first, write later
- absolute-date rule
- customer archive uniqueness
- historical-contract vs active-contract routing
- protected-field policy
- Todo owner requirement
- semantic dedupe for Todo
- live schema preflight before write
- no-write fallback when resolution is unsafe

These are operating-model decisions, not implementation details.

## What belongs to the stable interface

These should stay stable enough for future runtimes to implement against:

- workspace config as the environment boundary
- semantic slots as the field boundary
- preflight report as the write-safety boundary
- drift classes as the schema-change boundary

Stable interface does not mean frozen forever.
It means changes here should be explicit, versioned, and infrequent.

## What belongs to the extension surface

These are expected to evolve without being treated as core breakage:

- exact config file shape beyond the required minimum
- additional tables
- additional semantic slots
- alias dictionaries
- option synonym dictionaries
- richer preflight output
- runtime-specific caching
- runtime-specific API wrappers
- doc templates
- report layouts
- new analysis cards or operating views

These should be additive by default.

## Required minimum config

Any valid workspace config should be able to answer these questions:

- which Base app to use
- which table maps to each required workbench layer
- which folder holds archive docs
- which folder holds meeting-note docs
- which tasklist to use
- which semantic slots map to which live fields
- which fields are protected or guarded
- which enum fields are strict

If a config cannot answer these, it is incomplete.

## Required minimum semantic slots

Do not casually rename or remove these slots:

- `customer_master.customer_id`
- `customer_master.customer_short_name`
- `customer_master.archive_link`
- `customer_master.last_contact_at`
- `customer_master.next_action_summary`
- `action_plan.customer_id`
- `action_plan.subject`
- `action_plan.owner`

Other slots may evolve more freely.

## Required minimum preflight outputs

Any runtime implementation should produce at least:

- target object
- intended semantic slot
- resolved live field
- resolved live field type
- status
- drift items
- alias fallbacks
- blocked reason

Without these outputs, schema compatibility becomes opaque.

## Change policy

When changing the stable core:

1. explain why the old contract is insufficient
2. explain why the new contract is more stable, not just more detailed
3. update config template if the required minimum changed
4. update preflight contract if write safety changed
5. record the change in `CHANGELOG.md`

## Heuristic

If a proposed change mostly helps one runtime, one person, or one current schema snapshot, it probably belongs in the extension surface, not the stable core.
