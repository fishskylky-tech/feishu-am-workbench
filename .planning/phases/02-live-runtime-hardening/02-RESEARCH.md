# Phase 2: Live Runtime Hardening - Research

**Date:** 2026-04-15
**Phase:** 2-Live Runtime Hardening
**Question:** What do we need to know to plan this phase well?

## Scope Read

Phase 2 must stabilize startup truth for live operation: private configuration loading, runtime resource resolution, capability diagnostics, and deterministic customer lookup. The newly locked decision is that live resource truth cannot come from checked-in repo documents; it must come from private runtime input in the current process environment, with local `.env` allowed only as a convenience loader.

## Current State

### Runtime source loading
- `runtime/env_loader.py` already gives the right precedence baseline: explicit process env wins over `.env`.
- `runtime/runtime_sources.py` currently violates the selected boundary. It reads live hints from `SKILL.md`, `references/update-routing.md`, `references/workbench-information-architecture.md`, `references/actual-field-mapping.md`, and `references/live-resource-links.example.md`.
- The current `RuntimeSources.source_files` payload also advertises repo documents as the active source set, which will make diagnostics look more trustworthy than they should.

### Resource resolution and diagnostics
- `runtime/resource_resolver.py` already models required keys (`base_token`, `customer_archive_folder`, `meeting_notes_folder`, `todo_tasklist_guid`) and exposes `resolved` / `partial` / `unresolved` plus missing and unconfirmed keys.
- `runtime/diagnostics.py` already renders missing resources and capability check details. This means fail-closed startup can be implemented without inventing a second reporting surface.
- The main gap is semantic: today missing env can still be masked by repo-derived hints, so the diagnostic path is not yet fail-closed.

### Customer resolution
- `runtime/customer_resolver.py` already behaves deterministically for the current rule set: exact short name or customer ID wins, a single remaining candidate resolves, otherwise the result is `ambiguous`.
- Phase 2 likely needs more regression coverage here than major algorithm change, unless later discussion explicitly tightens ambiguity behavior.

## Risks

1. If repo fallback removal is incomplete, runtime may still appear live-capable from stale checked-in docs.
2. If `.env` semantics are not documented carefully, the code may implement the right behavior while docs still claim two equal truth sources.
3. If diagnostics remain phrased around generic “hint sources,” users may not understand that missing env is now a hard block.
4. If Phase 2 tries to redesign customer matching at the same time, scope will widen beyond the decisions actually locked in discuss-phase.

## Recommended Implementation Shape

### 1. Fail closed at the source-loader boundary
- Restrict `RuntimeSourceLoader` to env-backed hints only.
- Keep optional `.env` loading outside the source-of-truth contract: it hydrates env, then the loader reads env.
- Preserve `ResourceHint.source_file` using `env:FEISHU_AM_*` values so diagnostics stay actionable.

### 2. Make diagnostics explicit about blocked live startup
- When required env-backed hints are absent, resource resolution should remain `partial` or `unresolved`, but capability reporting and diagnostic text should make clear that live execution is blocked.
- Remove repo-file names from source summaries once they are no longer real inputs.

### 3. Prefer regression tests over broad refactors
- Add unit tests for `RuntimeSourceLoader` proving repo docs cannot satisfy live resource keys.
- Extend smoke or diagnostics tests to prove missing env yields a blocked/degraded report with explicit missing keys.
- Add/extend customer resolution tests only for deterministic edge cases already implied by current success criteria.

## Planning Guidance

- Treat runtime source hardening as the primary code change.
- Treat diagnostics wording and requirements/doc alignment as follow-through work, not separate architecture.
- Keep customer resolution work narrow unless implementation review discovers a direct Phase 2 gap.

## Open But Non-Blocking

- Exact terminology for `available` vs `degraded` vs `blocked` can be refined during implementation.
- The remaining discuss-phase gray areas can stay under agent discretion as long as they do not contradict the locked source boundary.

---
*Research status: ready for planning*