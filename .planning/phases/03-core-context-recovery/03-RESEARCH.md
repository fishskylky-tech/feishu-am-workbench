# Phase 3: Core Context Recovery - Research

**Date:** 2026-04-15
**Phase:** 3-Core Context Recovery
**Question:** What do we need to know to plan this phase well?

## Scope Read

Phase 3 must make meeting and post-meeting context recovery dependable without turning the gateway into a scene-specific context assembler. The locked decisions require an aggressive but auditable recovery path: always recover the 3 core Base tables after deterministic customer resolution, keep archive and historical meeting-note routing explicit, and make fallback-found context confidence-sensitive for downstream write ceiling.

## Current State

### Scene recovery already exists, but it is shallow
- `evals/meeting_output_bridge.py` already runs the gateway first and then performs scene-level targeted reads, which matches the architectural rule that the foundation should not silently assemble business context.
- The current `recover_live_context()` implementation only reads `客户联系记录` and `行动计划`, copies `archive_link`, and ranks note candidates from contact-log rows. It does not yet model archive recovery, routing conflicts, or explicit write-ceiling reasoning.
- The current text output includes resource status, customer result, context status, used sources, and missing sources, but it does not yet expose a full stable audit contract with open questions and confidence-derived write ceiling.

### The runtime substrate is close to sufficient
- `runtime/live_adapter.py` already provides deterministic customer lookup and generic Base row reads via `LarkCliBaseQueryBackend`.
- The 3 core tables already have a small semantic contract in `runtime/semantic_registry.py`, including `archive_link` on `客户主数据` and `meeting_note_doc` on `客户联系记录`.
- There is no dedicated drive/doc discovery adapter yet. Folder confirmation exists, but archive / meeting-note fallback search still needs a raw-query surface if Phase 3 is going to recover beyond explicit links.

### Existing tests give a good Phase 3 entry point
- `tests/test_meeting_output_bridge.py` already covers minimum Base recovery, related-note ranking from contact logs, and context-limited / partial behavior.
- The current suite is fast and stable under the repo venv, which makes it a good Nyquist sampling surface for this phase.

## Risks

1. If archive or meeting-note fallback search becomes too permissive, the scene may mix another customer's docs into the current thread.
2. If write ceiling is derived implicitly from recovery success, fallback-found context may look safer than it actually is.
3. If the output contract is left as free-form strings, future phases will struggle to verify whether context recovery was really auditable.
4. If Phase 3 pushes context assembly into `runtime/gateway.py`, the project will violate the established thin-runtime boundary.

## Recommended Implementation Shape

### 1. Keep recovery orchestration in the scene layer
- Extend `evals/meeting_output_bridge.py` first, not `runtime/gateway.py`.
- Let the gateway keep doing resource resolution and deterministic customer resolution.
- Introduce typed scene-level recovery results in `runtime/models.py` so the bridge can express `used_sources`, `missing_sources`, `open_questions`, candidate conflicts, and write ceiling without overloading plain strings.

### 2. Preserve the minimal semantic contract
- Reuse the 3 core tables only: `客户主数据`, `客户联系记录`, and `行动计划`.
- If Phase 3 needs new aliases or slot clarifications, adjust `runtime/semantic_registry.py` narrowly rather than expanding to full-schema mirroring.
- Do not broaden writable scope in this phase; the contract is for dependable reads and auditable interpretation.

### 3. Add constrained raw discovery for archive and meeting-note routing
- Explicit links remain the primary route.
- Fallback discovery should be folder-scoped and customer-scoped, using a small set of signals: customer ID, short name, doc title, folder placement, and known meeting-note links from Base rows.
- The adapter should return raw candidates plus the evidence used to rank them. The scene should decide whether a unique candidate is safe enough to use or whether the case must stay ambiguous.

### 4. Make write ceiling explicit and confidence-aware
- Treat explicit links and single high-confidence fallback candidates differently from multi-candidate or conflicting cases.
- Phase 3 should introduce an explicit write-ceiling field in the scene output, with recommendation-only fallback whenever recovery evidence is conflicting or incomplete.
- This keeps the phase aligned with the project-wide safety-first rule while still allowing richer context restoration.

## Planning Guidance

- Split the phase into a contract-first plan and a routing/output plan.
- Use sequential waves because `evals/meeting_output_bridge.py` and `tests/test_meeting_output_bridge.py` will be shared hotspots.
- Prefer targeted regression expansion over broad refactors or new dependencies.
- Keep any new Drive / Docs helper thin and evidence-oriented; do not hide ranking logic inside the adapter.

## Validation Architecture

### Quick feedback surface
- Use `./.venv/bin/python -m unittest tests.test_meeting_output_bridge -q` after each task commit.
- This command is already green and fast enough for per-task feedback.

### Full phase surface
- Use `./.venv/bin/python -m unittest tests.test_env_loader tests.test_runtime_smoke tests.test_meeting_output_bridge -q` after each wave.
- This keeps Phase 2 hardening guarantees alive while Phase 3 widens scene-level recovery.

### Required regression additions
- Explicit gateway-first tests for meeting/post-meeting output construction.
- Fallback archive / meeting-note discovery tests covering unique match, duplicate/conflict, and no-safe-match outcomes.
- Write-ceiling downgrade tests proving fallback ambiguity or conflict yields recommendation-only behavior.

## Open But Non-Blocking

- The exact confidence thresholds can be chosen during planning as long as they are explicit and testable.
- The exact output wording may evolve during implementation, but the audit fields themselves should stay fixed.

---
*Research status: ready for planning*
