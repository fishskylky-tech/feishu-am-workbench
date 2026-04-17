# Phase 12: Scene Runtime Contract And Boundary Freeze - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 12 defines the shared runtime contract for scene execution, the routing seam that keeps the root entry thin, and the frozen first-wave scene boundaries that later implementation phases must respect.

This phase does not add new scene capabilities, does not widen write power, and does not create a second execution path for writes.

</domain>

<decisions>
## Implementation Decisions

### Shared result shape
- **D-01:** Every scene should return a standard, business-readable result shape rather than only a final answer string.
- **D-02:** The standard result should be the "standard" level of detail: it must consistently show the scene being run, whether the customer was resolved, whether context was sufficient, what sources were used, what is fact vs judgment, what remains open, what next-step recommendations exist, and whether the result is recommendation-only or safe to proceed further.
- **D-03:** Scene-specific additions are allowed, but they must sit on top of the shared result shape rather than replacing it.

### Scene entry experience
- **D-04:** The primary mental model should be stable scene names, not a growing list of one-off operator commands.
- **D-05:** Existing operator-style entrypoints may be kept temporarily for compatibility, but they should be treated as compatibility wrappers around scene execution rather than the long-term contract.
- **D-06:** Phase 12 should make the scene-oriented entry shape the canonical direction for later phases.

### Missing-context and write-limit explanation
- **D-07:** When a scene cannot fully proceed, it should explain the reason in business-readable language first.
- **D-08:** The visibility level should be "business explanation plus one layer deeper": results should distinguish whether the limit came from missing context, customer ambiguity, permission limits, live validation failure, or safety/risk rules.
- **D-09:** The shared contract should avoid host-specific presentation details; it should carry reusable reason categories and clear user-facing meaning rather than CLI-only phrasing.

### Boundary freeze strength
- **D-10:** Phase 12 should freeze boundaries at a medium strength, not just the minimal red lines.
- **D-11:** The freeze should lock the first-wave scene list, the priority grouping, the workflow-first split rule, the non-bypass shared safety boundary, and the rule that deferred scenes do not silently move into the first wave.
- **D-12:** The freeze should stay short of over-specifying every later implementation detail; later phases still keep discretion on the exact internals as long as they stay inside the locked boundaries.

### Carry-forward decisions from prior phases
- **D-13:** The root/main entry remains thin and must not absorb scene-specific business logic.
- **D-14:** Scene boundaries are defined by AM workflows, not by raw Feishu tables.
- **D-15:** The first locked scene wave remains `post-meeting-synthesis`, `customer-recent-status`, `archive-refresh`, and `todo-capture-and-update`, with `post-meeting-synthesis` and `customer-recent-status` as the first priority group.
- **D-16:** Gateway, schema preflight, write guard, and writer remain the non-bypass shared safety boundary.
- **D-17:** Admin/bootstrap behavior remains outside daily scene execution.
- **D-18:** Phase 12 must promote the existing meeting write-loop path instead of inventing a second write path.

### the agent's Discretion
- Exact field names for the shared scene contract, as long as they clearly carry the locked meanings above.
- Exact compatibility strategy for legacy operator commands, as long as scene-oriented entry remains the canonical direction.
- Exact textual wording for the boundary-freeze docs and validation assertions, as long as they lock the medium-strength rules above.

</decisions>

<specifics>
## Specific Ideas

- The user wants the output contract to feel understandable in business terms, not like an internal debug object.
- The result should be rich enough that later scenes feel like one family of workflows rather than unrelated tools.
- "Why it cannot proceed" should stay clear to a human reviewer without forcing the core contract to mirror one host's UI or CLI wording.
- The phase should lock enough boundary rules to stop later drift, but should not prematurely hard-code every implementation detail of Phases 13-15.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase definition and milestone constraints
- `.planning/ROADMAP.md` — Phase 12 goal, success criteria, and plan slots for the scene runtime contract and boundary freeze.
- `.planning/REQUIREMENTS.md` — SCENE-01, SCENE-02, SCENE-03, and SAFE-01 requirements that this phase must satisfy.
- `.planning/STATE.md` — current milestone position and resume notes for Phase 12.
- `.planning/phases/12-scene-runtime-contract-and-boundary-freeze/12-RESEARCH.md` — phase-specific research conclusions, non-negotiable boundaries, and recommended split.

### Prior locked architecture decisions
- `.planning/phases/07-skill-architecture-scene-expansion/07-CONTEXT.md` — locked scene-wave, workflow-first boundary, thin-main-skill, and admin/bootstrap separation decisions.
- `.planning/phases/11-closeout-cleanup-for-planning-alignment-and-live-write-opera/11-CONTEXT.md` — locked rule to promote the verified meeting write-loop instead of creating a second write path.
- `references/scene-skill-architecture.md` — canonical first-wave scene list, priority grouping, and workflow-shaped scene boundary rules.

### Runtime and safety boundaries
- `.planning/research/PITFALLS.md` — milestone-level failure modes that the shared scene contract and boundary freeze must prevent.
- `runtime/__main__.py` — current operator surface that must become thinner rather than growing scene-specific logic.
- `runtime/models.py` — current shared runtime data shapes that the scene contract should extend rather than duplicate.
- `runtime/gateway.py` — existing live-first orchestration boundary that scenes must reuse instead of bypassing.
- `evals/meeting_output_bridge.py` — current executable meeting flow that serves as the migration source for the first canonical scene runtime.

### Codebase conventions
- `.planning/codebase/ARCHITECTURE.md` — thin foundation, live-first orchestration, and scene-level hydration responsibility.
- `.planning/codebase/CONVENTIONS.md` — recommendation-first, live-first, and facts-vs-judgment conventions that scene results must preserve.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `runtime/models.py` already provides shared runtime result shapes that can anchor a scene contract instead of starting from scratch.
- `runtime/__main__.py` already contains a working operator seam, so Phase 12 can redirect that seam instead of replacing the whole entrypoint model.
- `evals/meeting_output_bridge.py` already expresses the current meeting workflow in executable form and can be wrapped as the first scene migration source.
- `tests/test_validation_assets.py` already guards contract/document drift and is the natural place to lock boundary-freeze wording.

### Established Patterns
- The repo consistently treats live systems as truth and keeps cached or inferred material secondary.
- Writes remain recommendation-first and must go through schema preflight, guard, and writer checks.
- The foundation stays thin while scene/workflow layers decide what context to hydrate and how to interpret it.
- Facts, judgments, and action proposals are expected to stay distinct in user-facing outputs.

### Integration Points
- The shared scene result contract should connect the current root/runtime entrypoint to later scene implementations without forcing host-specific formatting.
- The scene router should sit between `runtime/__main__.py` and scene implementations so future scenes do not expand the root entry surface one command at a time.
- Boundary-freeze docs and validation checks should align planning artifacts, architecture references, and runtime guidance before Phase 13 starts building on them.

</code_context>

<deferred>
## Deferred Ideas

- No additional scene candidates were added during this discussion.
- Exact implementation details for later scene internals remain deferred to planning and execution phases.

</deferred>

---
*Phase: 12-scene-runtime-contract-and-boundary-freeze*
*Context gathered: 2026-04-17*
