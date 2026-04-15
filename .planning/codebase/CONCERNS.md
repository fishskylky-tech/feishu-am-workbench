# Codebase Map: Concerns

## Highest-Value Risks

1. Personal-workspace coupling remains high.
2. Expanded Base tables are modeled but not yet fully operationalized.
3. Meeting and archive routing still relies partly on naming conventions and minimal heuristics.
4. The project had strong product/docs intent but no GSD execution skeleton before this initialization.

## Verified Gaps

- Archive folder contains at least one duplicate customer archive doc.
- Meeting-note retrieval is still lightweight and not full content-aware.
- Todo custom-field handling partly depends on validated snapshots rather than full live discovery.
- Multi-AM portability is still mostly architectural intent, not a completed onboarding workflow.

## Operational Concerns

- A private repo plus local env setup lowers accidental leakage risk, but also hides reproducibility problems.
- The repo mixes strategic roadmap, active implementation, and standards-alignment work; without explicit phase management, priorities can drift.
- GitHub issues/discussions/projects show active ideation, but not yet a GSD phase mapping rooted in current brownfield reality.

## What To Protect During Future Changes

- live-first gate for meeting flows
- recommendation-only default on uncertain writes
- protected-field handling in customer master
- minimal semantic contract instead of full-field mirroring
- real-case validation discipline