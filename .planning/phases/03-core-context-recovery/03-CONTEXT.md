# Phase 3: Core Context Recovery - Context

**Gathered:** 2026-04-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 makes live customer context recovery dependable for meeting and post-meeting scenes. It should recover the minimum useful customer thread across the 3 core Base tables, customer archive, and related meeting-note docs, while keeping the runtime thin, the scene output auditable, and the write path safety-first.

</domain>

<decisions>
## Implementation Decisions

### Recovery depth and sequencing
- **D-01:** After resource resolution and deterministic customer resolution succeed, Phase 3 should aggressively recover useful context rather than stopping at the cheapest minimum path.
- **D-02:** The default recovery path should always read the 3 core Base surfaces for the resolved customer: `客户主数据`, recent `客户联系记录`, and recent `行动计划`.
- **D-03:** If `archive_link` exists or a high-confidence archive candidate can be located, the scene should continue into the customer archive instead of treating the Base-only snapshot as sufficient.
- **D-04:** If the current meeting appears to continue an existing thread, the scene should also recover related historical meeting-note docs rather than limiting itself to the current transcript.

### Archive and meeting-note routing policy
- **D-05:** Archive and meeting-note routing should prefer explicit links first, but Phase 3 may use proactive fallback search and ranking when links are missing, stale, or inconsistent.
- **D-06:** Proactive fallback may use multiple signals together, including customer ID, customer short name, folder placement, and document metadata, instead of stopping on the first missing explicit link.
- **D-07:** Duplicate, stale, or conflicting archive / meeting-note candidates must be surfaced explicitly in the output as uncertainty; the system must not hide those conflicts behind a single confident-looking summary.

### Auditable output contract
- **D-08:** Meeting and post-meeting scenes should always emit a strong audit frame with fixed fields for `资源状态`, `客户结果`, `上下文恢复状态`, `已使用资料`, `关键补充背景`, `未找到但应存在的资料`, `写入上限`, and `开放问题`.
- **D-09:** `上下文恢复状态` should follow the documented live-first semantics (`not-run`, `completed`, `partial`, `context-limited`) and must state the fallback reason whenever fallback search or limited recovery was used.

### Safety boundary for aggressive recovery
- **D-10:** Aggressive context recovery must not weaken the upstream customer-resolution policy from Phase 2; customer identity still has to be resolved deterministically before deeper reads can claim grounded context.
- **D-11:** When archive or meeting-note context is recovered through fallback search instead of an explicit trusted link, the write ceiling should be decided by confidence, not assumed to be normal by default.
- **D-12:** High-confidence unique matches may keep the normal downstream write path, but ambiguous or conflicting recovery results must downgrade the scene to recommendation-only behavior.

### the agent's Discretion
- The exact ranking heuristic for related archive and meeting-note candidates is discretionary as long as it stays auditable and customer-scoped.
- The exact recent-record window for `客户联系记录` and `行动计划` is discretionary as long as it is small, relevant, and explainable.
- The exact confidence thresholds that map fallback recovery to normal write path vs recommendation-only may be chosen during planning, but the thresholds must be explicit and testable.

</decisions>

<specifics>
## Specific Ideas

- Prefer richer customer-thread recovery over conservative early stop once the customer has been resolved.
- Allow active fallback routing for archive and historical meeting-note discovery, but never hide source conflicts.
- Keep the final scene output strongly auditable instead of reducing it to a vague “结合历史资料”.
- Treat fallback-found context as confidence-sensitive for write decisions.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase definition and project constraints
- `.planning/ROADMAP.md` — Phase 3 goal, requirement mapping, and success criteria for Core Context Recovery
- `.planning/REQUIREMENTS.md` — `LIVE-04`, `WORK-01`, `WORK-03`, `MEET-01`, and `MEET-02` define the required outcomes for this phase
- `.planning/PROJECT.md` — project-level constraints around live-first behavior, thin runtime boundaries, and guarded writes
- `.planning/STATE.md` — current project handoff that moves focus from completed Phase 2 into Phase 3

### Scenario and information-model rules
- `references/meeting-live-first-policy.md` — required gateway order, fallback conditions, and status semantics for meeting scenes
- `references/meeting-context-recovery.md` — minimum recovery order, auditable recovery log, and fallback rules for meeting context recovery
- `references/workbench-information-architecture.md` — how `客户主数据`, detail tables, archive, meeting notes, and Todo are meant to relate
- `references/customer-archive-rules.md` — canonical archive uniqueness and archive content rules that affect archive routing and conflict handling
- `references/meeting-note-doc-standard.md` — constraints on how formal meeting-note docs should be treated and referenced

### Runtime and eval surfaces in scope
- `runtime/gateway.py` — current gateway orchestration boundary and the rule that scene context should not be silently assembled in the foundation layer
- `runtime/live_adapter.py` — current live query substrate for customer master and targeted Base reads
- `runtime/semantic_registry.py` — minimal semantic contract for `客户主数据`, `客户联系记录`, and `行动计划`
- `runtime/models.py` — current typed structures for customer resolution, resource status, and write-ceiling-adjacent runtime results
- `evals/meeting_output_bridge.py` — current starter implementation for context recovery and auditable meeting output, likely the main Phase 3 integration surface
- `tests/test_meeting_output_bridge.py` — existing regression entrypoint for context recovery and meeting output behavior

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `runtime/gateway.py` already enforces the Stage 1 / Stage 2 boundary for resources and customer resolution before any write-safety logic runs.
- `runtime/live_adapter.py` already provides customer-master lookup and generic Base record listing, which gives Phase 3 a live-read substrate without inventing a new adapter layer.
- `runtime/semantic_registry.py` already keeps the 3 core Base tables on a minimal semantic contract, including `archive_link` and `meeting_note_doc` slots that Phase 3 can build on.
- `evals/meeting_output_bridge.py` already contains a starter `recover_live_context` flow and an auditable text output format, but it is still shallow compared with the desired Phase 3 behavior.

### Established Patterns
- The runtime is intentionally thin: it resolves, probes, and protects; scene layers decide what to read and how to present recovered context.
- Semantic contracts are intentionally smaller than the live schema, so Phase 3 should extend targeted reads without drifting into full-table mirroring.
- Meeting work is live-first and safety-first; fallback is allowed only with explicit status and reduced certainty.

### Integration Points
- Phase 3 will likely extend `evals/meeting_output_bridge.py` and related scene-facing recovery code before widening the core gateway itself.
- Any new targeted reads should stay aligned with `runtime/live_adapter.py`, `runtime/semantic_registry.py`, and the current typed models in `runtime/models.py`.
- Regression coverage should extend from `tests/test_meeting_output_bridge.py` and related runtime smoke tests so aggressive recovery does not regress deterministic safety behavior.

</code_context>

<deferred>
## Deferred Ideas

None — this discussion stayed within the Phase 3 boundary.

</deferred>

---
*Phase: 03-core-context-recovery*
*Context gathered: 2026-04-15*