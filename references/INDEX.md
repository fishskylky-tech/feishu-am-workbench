# References Index

Quick reference for all 21 documents in this directory. Read SKILL.md for the full "when to read" guidance per file.

| File | One-line summary | When to load |
|------|-----------------|--------------|
| [actual-field-mapping.md](./actual-field-mapping.md) | Cached snapshot of live Base field names, types, and table IDs | Before any Base write that touches specific field names |
| [base-integration-model.md](./base-integration-model.md) | Principles for how tables are integrated: live-first, minimal semantic contract, no full-field mirror | When deciding how to access or extend a Base table |
| [customer-archive-rules.md](./customer-archive-rules.md) | Rules for creating, linking, and updating the customer archive doc — uniqueness, structure, and what belongs there | Before touching any customer archive doc |
| [entity-extraction-schema.md](./entity-extraction-schema.md) | Full schema for the extraction bundle: all extractable entity types and required fields | Before parsing any mixed input (meeting note, customer file, update request) |
| [fact-grading.md](./fact-grading.md) | How to classify facts vs. judgments and assign confidence levels | After extraction, before producing the change plan |
| [feishu-runtime-sources.md](./feishu-runtime-sources.md) | Where the current personal environment's live Feishu resource hints come from (env vars, local files, config) | When the runtime needs to discover Base token, folder tokens, or tasklist guid |
| [feishu-workbench-gateway.md](./feishu-workbench-gateway.md) | Unified gateway for all Feishu workbench access: stages, resource resolution, context hydration, preflight | Whenever the task needs live Feishu data or is preparing a write plan |
| [live-resource-links.example.md](./live-resource-links.example.md) | Example URLs and tokens for local runtime wiring (use env vars for real values) | When the runtime needs concrete entry point examples |
| [live-schema-preflight.md](./live-schema-preflight.md) | Contract for live schema validation: what to check, output format (safe/safe_with_drift/blocked), drift taxonomy | Before any Base or Todo write |
| [master-data-guardrails.md](./master-data-guardrails.md) | Which fields in 客户主数据 are protected, guarded, or freely updatable, and when to update strategy fields | Before changing any field in the customer master table |
| [meeting-context-recovery.md](./meeting-context-recovery.md) | Step-by-step process for recovering historical customer context before interpreting a meeting | At the start of any meeting note, transcript, or post-meeting task |
| [meeting-live-first-policy.md](./meeting-live-first-policy.md) | Policy requiring live Feishu lookup before formal meeting analysis; defines the execution gate and fallback conditions | At the start of any meeting-related task, before analysis begins |
| [meeting-note-doc-standard.md](./meeting-note-doc-standard.md) | Required structure and fidelity rules for meeting-note cold-memory docs | Before creating or updating any meeting-note document in Feishu |
| [meeting-output-standard.md](./meeting-output-standard.md) | Required structure for final user-facing output on meeting tasks: section order, Chinese titles, dynamic update rules | Before finalizing output for any meeting note, transcript, or post-meeting update |
| [meeting-type-classification.md](./meeting-type-classification.md) | Meeting type taxonomy and the default write ceiling for each type | After recovering context, before deciding what to write |
| [minimal-stable-core.md](./minimal-stable-core.md) | Defines which rules and structures should not change across iterations; the invariant core of the skill | When evaluating whether a proposed change breaks backward compatibility |
| [money-and-contract-rules.md](./money-and-contract-rules.md) | Rules for handling amounts, contracts, renewals, collections, and estimated vs. confirmed revenue | Whenever money, contracts, or financial terms appear in the input |
| [schema-compatibility.md](./schema-compatibility.md) | How to handle schema drift: renamed fields, added/deleted fields, option changes, alias resolution order | When the live schema differs from the cached mapping |
| [task-patterns.md](./task-patterns.md) | Common task playbooks: meeting prep, post-meeting update, archive refresh, and their step sequences | When executing a well-known task type end to end |
| [update-routing.md](./update-routing.md) | Decision rules for routing each extracted entity to the correct target (table, doc, or Todo); idempotency rules | Before building the change plan |
| [workbench-information-architecture.md](./workbench-information-architecture.md) | How the workbench layers relate to each other: master data vs. detail tables vs. archive vs. Todo | When the task touches how the workbench should be interpreted or reorganized |
