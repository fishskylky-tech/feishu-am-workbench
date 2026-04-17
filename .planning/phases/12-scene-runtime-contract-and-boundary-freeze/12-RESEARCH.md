# Phase 12 Research: Scene Runtime Contract And Boundary Freeze

**Date:** 2026-04-16
**Mode:** Planning from existing milestone research
**Context note:** No phase-specific 12-CONTEXT.md exists, so this research uses ROADMAP, REQUIREMENTS, v1.1 milestone research, and shipped v1.0 architecture/runtime seams.

## Phase Goal

Define the runtime/operator contract for scenes, freeze first-wave scene boundaries, and prevent boundary regressions before implementation fans out.

## Phase Requirements

- SCENE-01
- SCENE-02
- SCENE-03
- SAFE-01

## Reused Evidence

### Milestone Research
- `.planning/research/SUMMARY.md`
- `.planning/research/ARCHITECTURE.md`
- `.planning/research/FEATURES.md`
- `.planning/research/PITFALLS.md`

### Prior Phase Outputs
- `.planning/phases/07-skill-architecture-scene-expansion/07-01-SUMMARY.md`
- `.planning/phases/11-closeout-cleanup-for-planning-alignment-and-live-write-opera/11-01-SUMMARY.md`

### Current Runtime Seams
- `runtime/__main__.py`
- `runtime/gateway.py`
- `runtime/models.py`
- `evals/meeting_output_bridge.py`
- `references/scene-skill-architecture.md`

## Main Conclusions

1. No new framework or service layer is needed. The current Python runtime, gateway, and writer surfaces are already the right substrate.
2. Phase 12 should extract an explicit scene execution contract before converting more workflows into scene runtimes.
3. The existing `meeting-write-loop` operator path is the canonical migration source, but it should not remain the long-term contract shape.
4. Scene routing must move into an explicit registry/router seam so `runtime/__main__.py` stops accumulating scene-specific orchestration.
5. First-wave boundaries are already architecturally decided in Phase 7 and should now be frozen as executable implementation constraints: `post-meeting-synthesis`, `customer-recent-status`, `archive-refresh`, `todo-capture-and-update`.

## Non-Negotiable Boundaries

- Foundation stays thin; `runtime/gateway.py` must remain the live-access and safety boundary.
- Scene logic decides what live context to hydrate; the gateway must not auto-assemble a full business bundle.
- Writes remain recommendation-first and must continue through schema preflight, write guard, and the existing writer surface.
- Scene contracts must stay host-agnostic and avoid host-specific formatting or routing assumptions.
- Admin/bootstrap behavior remains out of daily scene execution.

## Recommended Implementation Shape

### Shared Runtime Contract
Create a dedicated runtime scene contract module that defines:
- scene request/input envelope
- scene result envelope
- explicit fallback reason field
- explicit write ceiling field
- scene payload/artifact field separated from rendering text

Prefer extending existing runtime models and bridge outputs rather than duplicating gateway or write result shapes.

### Scene Registry And Routing
Introduce an explicit scene registry/router that:
- maps stable scene names to implementations
- rejects unknown scene names deterministically
- keeps `runtime/__main__.py` as a thin CLI/operator shell
- allows the post-meeting operator to become one scene implementation instead of a one-off path

### Boundary Freeze Artifacts
Lock the first wave in docs/tests so later phases cannot silently:
- split scenes by raw table
- bypass gateway/preflight/guard/writer
- mix bootstrap/admin work into daily scenes
- widen write ceilings beyond current guarded behavior

## Risks To Prevent Early

1. Reusing `evals/meeting_output_bridge.py` as permanent production architecture instead of extracting a stable runtime contract.
2. Letting `runtime/__main__.py` grow into a new monolith that hardcodes scene-specific flows.
3. Introducing a second write path while adding scene routing.
4. Turning scenes into table-based modules instead of workflow-based modules.
5. Encoding host-specific message layout into the core scene result contract.

## Planning Implications

### Plan Split
Use two plans:
1. Runtime contract + explicit scene routing seam
2. Boundary freeze docs + validation locks

### Why This Split
- Plan 1 carries the hardest technical constraint: introducing a stable contract and router without breaking the existing operator surface.
- Plan 2 locks the first-wave boundaries and non-bypass rules so later scene implementations have clear guard rails.

## Out Of Scope For Phase 12

- Converting all first-wave scenes into executable implementations
- Building archive-refresh or todo-follow-on logic
- Full scenario-level regression coverage for every future scene
- Bootstrap/admin operator work

## Confidence

High. The architecture direction was already fixed in Phase 7 and the operator seam was already stabilized in Phase 11; Phase 12 mainly needs to turn that contract into an executable runtime foundation.
