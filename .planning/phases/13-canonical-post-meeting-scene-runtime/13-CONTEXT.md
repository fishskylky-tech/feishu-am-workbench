# Phase 13 Context

Phase 13 closes SCENE-04 on top of the shared scene runtime seam introduced in Phase 12.

Key facts:

- the current `post-meeting-synthesis` runtime path already routes through `SceneRequest` -> registry -> shared result contract
- `meeting-write-loop` is now a compatibility wrapper instead of the long-term contract
- Todo candidate generation and confirmed writes still reuse the existing gateway, preflight, guard, and writer boundaries

Execution focus for this phase:

- treat the current code as the canonical post-meeting runtime if it already satisfies SCENE-04
- add only the minimum artifacts, validation references, and documentation needed to make that closure explicit