# Base Integration Model

This file defines how `feishu-am-workbench` should integrate Feishu Base tables going forward.

Its purpose is to avoid two bad extremes:

- no constraints, which leads to noisy reads and unsafe writes
- full field mirroring inside the skill, which creates high token cost and high maintenance cost

## Core principle

Do not model every live field in the skill.

Instead, use three layers:

1. live schema layer
2. minimal semantic contract
3. scenario routing layer

The live schema remains the runtime truth.
The semantic contract stays intentionally small.
Scenarios operate on semantic actions, not raw field names.

## Layer 1: Live Schema Layer

Runtime should discover live Base structure at execution time:

- table existence
- field existence
- field type
- select / multi-select options

This layer should not be copied into prompt context by default.
It exists to support:

- read normalization
- write safety
- drift detection

Reference snapshots such as
[actual-field-mapping.md](./actual-field-mapping.md)
remain compatibility caches, not the source of truth.

## Layer 2: Minimal Semantic Contract

The skill should maintain only the small set of fields that matter for:

- customer resolution
- context recovery
- write planning
- dedupe
- protected / guarded policy

For each integrated table, define a **table profile**, not a full field mirror.

Each table profile should contain only:

- `table_name`
- `table_role`
  - `snapshot` / `detail` / `dimension` / `bridge`
- `entity_key`
- `dedupe_key`
- `default_read_slots`
- `write_slots`
- `protected_slots`
- `strict_enum_slots`

Everything else stays in the live schema layer and is read-through only.

## Layer 3: Scenario Routing Layer

Scenarios should not reason from raw field names.

They should operate on semantic actions such as:

- update latest contact snapshot
- create action plan item
- append contact record
- update key person insight
- record competitor encounter

The runtime translates those actions into:

- target table
- semantic slots
- live field resolution

## Read model

Do not read whole tables by default.

Build a lean context bundle per scenario:

- only the tables relevant to that scenario
- only the current customer's relevant records
- only the slots needed for reasoning
- compact drift / blocked summaries when needed

This keeps token cost under control.

## Write model

Every field should fall into one of four categories:

- `required_lookup`
- `safe_update`
- `guarded_update`
- `read_only_for_match`

Any live field not present in the semantic contract is:

- readable when needed
- not writeable by default
- not part of prompt-time free generation

This prevents the model from inventing writes just because it sees extra live fields.

## How to add a new Base table

When a new table is integrated, do not copy all fields into the skill.

Follow this order:

1. define the table profile
2. define the minimum semantic slots used by current scenarios
3. define dedupe and guarded rules
4. keep all remaining fields in live discovery only

If a field is not used for:

- reasoning
- routing
- dedupe
- protection
- writing

it should not enter the semantic registry.

## Current recommendation for expansion order

Add tables in this order:

1. `客户关键人地图`
2. `合同清单`
3. `竞品交锋记录`
4. `竞品基础信息表`

Reason:

- the first two are closer to daily AM work
- the last two are better handled after the detail-layer pattern is stable

## Design rule for maintenance cost

Schema changes should not force a skill change unless they affect:

- a semantic slot already in use
- a protected / guarded field
- a strict enum in use
- a dedupe key
- a required lookup key

Everything else should be absorbed by live schema discovery.

That is the main mechanism that keeps maintenance cost low.
