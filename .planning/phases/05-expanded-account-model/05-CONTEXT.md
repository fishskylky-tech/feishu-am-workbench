# Phase 5: Expanded Account Model - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning and execution
**Mode:** Autonomous

<domain>
## Phase Boundary

Phase 5 extends the current customer context loop with the smallest useful set of broader account-model reads: contracts, key people, and competitor structures. The goal is not schema mirroring. The goal is to make these tables available through targeted reads that stay grounded in the resolved customer and remain subordinate to the existing live-first, recommendation-first workflow.

</domain>

<decisions>
## Decisions

- **D-01:** Keep the semantic contract narrow. Only summarize a few high-signal fields from 合同清单, 客户关键人地图, 竞品基础信息表, and 竞品交锋记录.
- **D-02:** Attach new reads to the existing context recovery path instead of creating a parallel scene or free-form table browser.
- **D-03:** Preserve current write rules. Phase 5 is read/use expansion only and must not widen write scope.
- **D-04:** Prefer bridge-first competitor recovery: read 竞品交锋记录 by customer first, then enrich with 竞品基础信息表 only when competitor IDs are present.

### Claude's Discretion

- Choose concise summary lines that are useful in meeting and post-meeting outputs.
- Add only regression coverage needed to keep the new read paths stable.

</decisions>

<code_context>
## Existing Code Insights

- `evals/meeting_output_bridge.py` already owns the customer-context recovery path and is the correct place to add targeted expanded-account reads.
- `runtime/semantic_registry.py` already contains narrow table profiles for the expansion tables, so Phase 5 should use those existing contracts rather than redefining them.
- `tests/test_meeting_output_bridge.py` already pins context-recovery behavior and is the right regression surface for this phase.

</code_context>

<specifics>
## Specific Ideas

- Contracts should surface status, expiry, and count shape rather than full contract dumps.
- Key people should surface a short relationship map summary.
- Competitor context should prioritize active encounter records and enrich names or strengths only when a stable competitor ID can link to the dimension table.

</specifics>

<deferred>
## Deferred Ideas

- Full-table schema mirroring
- Deep historical contract analytics
- Automated competitor writeback or strategy updates

</deferred>
