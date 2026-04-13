---
title: Feishu Workbench Gateway
load_triggers:
  - task_type: [meeting-prep, post-meeting, account-analysis, archive-refresh, writeback-plan]
  - condition: accessing any Feishu workbench resource
load_priority: critical
estimated_tokens: 1004
dependencies: []
tier: L3-always
---

# Feishu Workbench Gateway

Use this file when a scenario needs to touch Feishu workbench resources.

For meeting inputs, also apply [meeting-live-first-policy.md](./meeting-live-first-policy.md).

This is the skill-internal gateway workflow.
It is a reusable operating pattern for this skill's own scenarios, not a separate product or shared platform.

## What the gateway does

The gateway is an execution gate for foundation calls.
It is not a default context assembler.

The gateway unifies these responsibilities:

1. resolve the resource source
2. resolve the customer and `客户ID`
3. run targeted live reads only when the scenario explicitly requests them
4. run live safety checks before write planning
5. hand confirmed write candidates to the unified writer surface

Any scenario that needs Feishu context should go through this gateway rather than improvising its own read path.

For meeting inputs, this gateway acts as a mandatory execution gate before formal analysis.

## Gateway stages

### Stage 1: Resource Source Resolution

Read:

- [feishu-runtime-sources.md](./feishu-runtime-sources.md)
- [actual-field-mapping.md](./actual-field-mapping.md)
- [workbench-information-architecture.md](./workbench-information-architecture.md)

Do not treat "no obvious env/config was found" as a completed Stage 1 result.
Stage 1 is complete only after this repository source layer has been checked.

Determine:

- where the current customer master hint comes from
- where the archive folder hint comes from
- where the meeting-note folder hint comes from
- where the Todo tasklist hint comes from

Output:

- `resource_source_status`
  - resolved / partial / unresolved
- `resource_hints_used`

### Stage 2: Customer Resolution

Resolve one customer from live source of truth:

- `客户主数据`

Minimum result:

- `客户ID`
- customer short name
- archive link if present

If ambiguous:

- stop write planning
- ask for clarification or remain in recommendation mode

### Stage 3: Targeted Reads

After customer resolution, the scenario may explicitly request only the raw data it needs in this order:

1. `客户主数据`
2. recent `客户联系记录`
3. recent `行动计划`
4. customer archive
5. related meeting-note docs when needed

The gateway should stop as soon as the scenario has enough raw inputs.
Do not read everything by default.
Do not package the result into a default meeting context bundle.

Output:

- `context_recovery_status`
  - completed / partial / context-limited / not-run
- `context_sources_used`
- `key_recovered_context`
- `missing_expected_sources`

`context-limited` is valid only if the gateway actually attempted the relevant live reads.
If the scenario skipped the gateway, use `not-run`.

### Stage 4: Write-Surface Resolution

If the scenario may propose writes, determine:

- which objects are candidates for update
- which layer each object belongs to
- which semantic fields are likely involved

Examples:

- `客户联系记录`
- `行动计划`
- `客户档案`
- `客户主数据`
- Todo

This stage is still planning, not mutation.

The scenario layer should also attach:

- `operation`
- `match_basis`
- `source_context`
- `target_object`

These fields are part of the shared write-candidate contract, not Todo-only details.

### Stage 5: Live Schema Preflight

Before any write suggestion becomes write-ready:

- run the checks in [live-schema-preflight.md](./live-schema-preflight.md)

Output:

- `safe`
- `safe_with_drift`
- `blocked`

And also:

- resolved field names
- drift items
- alias fallbacks
- blocked reasons

### Stage 6: Write Guard

Apply:

- protected-field policy
- write ceiling by meeting type
- idempotency
- Todo owner rule
- Todo semantic dedupe

If anything remains unsafe:

- keep recommendation mode
- do not escalate to write mode

### Stage 7: Unified Writer Execution

After explicit user confirmation:

- pass the confirmed write candidate to the object-specific writer
- do not let the scenario call Feishu mutation commands directly

Writer responsibilities:

- execute create or update
- apply object-level dedupe
- return a normalized write result

Current first-class writer:

- Todo writer

## Which scenarios must call the gateway

These scenarios should use the gateway by default:

- meeting-prep
- post-meeting
- account-analysis when Feishu records matter
- archive-refresh
- any writeback planning

## Which scenarios may skip parts of the gateway

These may skip deeper stages:

- local-only brainstorming with no Feishu dependency
- single-file fallback analysis when the user explicitly accepts `context-limited` mode

Even then, the output should state that the gateway was partially skipped or not run.

## Output contract

When the gateway is used, the final scenario output should make these items visible:

- `资源解析状态`
- `客户解析结果`
- `上下文恢复状态`
- `已使用飞书资料`
- `写入候选对象`
- `统一写回结果`
- `schema preflight 结果`
- `blocked / drift`

If the gateway was not executed, the output should say so explicitly instead of presenting a synthetic recovery result.

Do not hide gateway behavior behind vague phrases such as:

- “已结合飞书信息”
- “已结合历史资料”

The user should be able to tell what was actually resolved and used.
