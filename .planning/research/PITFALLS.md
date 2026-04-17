# Research: Pitfalls

## Highest-Risk Failures

1. Scene code bypasses gateway, preflight, guard, or writer boundaries.
2. Live-first degrades into local-first or prompt-first execution.
3. Recommendation-first output is confused with confirmed execution.
4. Root skill absorbs scene-specific business logic again.
5. Core runtime becomes tied to one host's tooling or message format.
6. Schema drift causes silent misreads or miswrites.
7. Scenes are split by tables instead of workflow intent.
8. Admin/bootstrap logic leaks into daily scene execution.

## Prevention

- Make all scene writes flow through the existing shared execution shell
- Require explicit live status, fallback reason, and write ceiling in scene results
- Keep host-specific behavior outside core runtime and scene contracts
- Enforce semantic-slot plus live-schema preflight before writes
- Freeze first-wave scene boundaries before implementation starts
- Add per-scene regression cases for happy path, fallback, unresolved customer, and schema issues

## Suggested Early Handling

- Phase 1: freeze execution boundaries and first-wave scene boundaries
- Phase 2: land the shared execution shell and scene runtime contract
- Phase 3: add validation, fallback, and drift coverage
- Phase 4: separate admin/bootstrap and tighten portability and diagnostics
