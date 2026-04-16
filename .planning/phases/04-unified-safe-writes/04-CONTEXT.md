# Phase 4: Unified Safe Writes - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 strengthens the current write path so meeting and post-meeting scenes can produce trustworthy write candidates, run mandatory preflight and guard checks, and execute a narrow confirmed write surface safely. The phase should harden the existing Todo-centered mutation path first, while also defining a very small, explicit boundary for when low-risk customer-master fact updates may become write-ready. It must not broaden into generic uncontrolled Base mutation.

</domain>

<decisions>
## Implementation Decisions

### Candidate normalization and extraction granularity
- **D-01:** Meeting scenes should prefer fewer, clearer Todo candidates rather than splitting every sentence-level action into a separate task.
- **D-02:** Candidate merging is allowed only within the same meeting and the same action theme. Cross-meeting automatic merging is out of scope for this phase.
- **D-03:** Even when candidates are merged for user-facing output, each normalized candidate must still carry explicit `operation`, `match_basis`, `source_context`, and `target_object` fields.
- **D-04:** `source_context` should continue to preserve scenario identity and customer grounding, including at minimum the scene type and `customer_id` when known.

### Duplicate Todo handling
- **D-05:** When semantic dedupe finds an existing Todo, the default path should be to update the existing task rather than create a new one.
- **D-06:** If the new candidate looks like an execution detail under an already broader parent task, the system may recommend creating a subtask instead of updating the parent.
- **D-07:** Subtask creation must remain behind explicit confirmation. It must not execute automatically just because the dedupe heuristic prefers the subtask path.

### Write ceiling and confirmed write scope
- **D-08:** Phase 4 should fully harden confirmed Todo create and update as the primary real write surface.
- **D-09:** Outside Todo, the phase may define a narrowly scoped direct-write path for low-risk customer-master fact fields, but only when the field set is explicit, small, and operational rather than judgment-heavy.
- **D-10:** The minimum safe standard for any write-ready path is unchanged: schema preflight and write guard are mandatory before a write can be executed.

### Customer-master risk policy
- **D-11:** High-risk customer-master updates remain recommendation-only by default.
- **D-12:** “Low-risk” customer-master fields should be limited to operational fact fields with low ambiguity, such as recent follow-up time, next follow-up date, or a clearly grounded current owner.
- **D-13:** Semi-judgment fields such as stage, strategic status, or other interpretation-heavy labels should not be promoted into the low-risk direct-write path in this phase.

### Write result presentation
- **D-14:** The writer contract must still return a full normalized result envelope internally, including preflight outcome, guard outcome, dedupe decision, blocked reasons, and remote metadata.
- **D-15:** Default user-facing output should be concise and natural-language-first rather than exposing the full structured envelope every time.
- **D-16:** Full structured write details should remain available for debug, validation, or inspection paths even when the default presentation is concise.

### the agent's Discretion
- The exact merge heuristic for deciding when two same-meeting action items are “the same theme” is discretionary as long as it stays auditable and conservative.
- The exact debug surface for exposing the full normalized write result is discretionary, as long as validation and downstream tooling can still inspect the structured fields.
- The exact enumerated low-risk customer-master field set is discretionary during planning, but it must stay minimal, fact-like, and explicitly separated from protected or interpretation-heavy fields.

</decisions>

<specifics>
## Specific Ideas

- The preferred user experience is: fewer duplicate-looking follow-up tasks, clearer confirmed-write behavior, and concise default writeback feedback.
- Same-meeting actions on the same topic should usually collapse into a smaller number of better Todo candidates.
- Natural-language writeback summaries are preferred for default output, but deep structured details must remain inspectable for testing and debugging.
- The intended risk posture is not “Todo only forever”; it is “Todo first, then only a tiny set of operational fact updates if the live safety checks are strong enough.”

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase definition and prior constraints
- `.planning/ROADMAP.md` — Phase 4 goal, requirements, and success criteria for Unified Safe Writes
- `.planning/REQUIREMENTS.md` — `MEET-03`, `WRITE-01`, `WRITE-02`, and `WRITE-03` define the required outcomes for this phase
- `.planning/PROJECT.md` — project-level live-first, recommendation-first, and brownfield constraints
- `.planning/STATE.md` — current milestone state and handoff into Phase 4
- `.planning/phases/03-core-context-recovery/03-CONTEXT.md` — carry-forward rules for confidence-sensitive writes and auditable scene output

### Write safety contracts
- `references/live-schema-preflight.md` — canonical write-time live schema validation contract
- `references/feishu-workbench-gateway.md` — gateway stage ordering, write guard expectations, and unified writer contract
- `ARCHITECTURE.md` — current architecture rules for preflight, write guard, output, and writeback layering

### Runtime and scene surfaces in scope
- `runtime/gateway.py` — current orchestration boundary for preflight and guard collection
- `runtime/schema_preflight.py` — current live schema resolution and drift/blocking behavior
- `runtime/write_guard.py` — current final write gate and protected-field behavior
- `runtime/todo_writer.py` — current normalized Todo create, update, dedupe, and subtask recommendation path
- `evals/meeting_output_bridge.py` — current meeting-scene Todo candidate generation and confirmed write bridge
- `tests/test_meeting_output_bridge.py` — current regression surface for candidate shape and write execution routing
- `archive/validation-reports/2026-04-12-unified-todo-writer-live-validation.md` — live validation evidence for create, duplicate-update, and confirmed-subtask boundaries

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `runtime/todo_writer.py` already implements normalized create, update, duplicate detection, and explicit-confirm subtask behavior that Phase 4 can harden instead of replacing.
- `runtime/schema_preflight.py` already provides field existence, type compatibility, option validation, owner validation, and drift reporting needed for mandatory preflight.
- `runtime/write_guard.py` already centralizes final allow/block evaluation, including protected fields and owner requirements.
- `evals/meeting_output_bridge.py` already emits meeting-scene Todo candidates and routes confirmed writes into the unified Todo writer.

### Established Patterns
- The repo keeps runtime foundation thin: scenes produce candidates, the gateway evaluates safety, and writers execute normalized mutations.
- Live-first and recommendation-first remain non-negotiable. Any broadened write-ready path must still be explicitly grounded in live checks.
- Validation artifacts are treated as part of the operating contract, so Phase 4 should preserve inspectable results even if default user output becomes more concise.

### Integration Points
- Candidate normalization changes will likely land first in `evals/meeting_output_bridge.py` and the associated tests.
- Mandatory preflight and guard enforcement must stay wired through `runtime/gateway.py` and object writers rather than being left to scene-specific conventions.
- Any low-risk customer-master write path must align with the same preflight/guard contract and must not bypass the unified write architecture.

</code_context>

<deferred>
## Deferred Ideas

- Cross-meeting automatic merge of action items is deferred; this phase only allows same-meeting same-theme consolidation.
- Broad customer-master mutation support is deferred; only a tiny explicitly enumerated low-risk fact path may be considered here.
- Showing the full structured result envelope in normal user output is deferred; default output stays natural-language-first.

</deferred>

---
*Phase: 04-unified-safe-writes*
*Context gathered: 2026-04-16*