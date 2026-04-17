# Phase 14 Research

Relevant existing substrate:

- `evals/meeting_output_bridge.py` already provides reusable `recover_live_context()` logic over customer master, contact log, action plan, archive candidates, and meeting-note candidates
- `runtime/live_adapter.py` already exposes thin query primitives and candidate discovery instead of scene-specific orchestration
- the shared scene contract already separates standard fields from scene-specific payloads

Implementation choice:

- keep `customer-recent-status` as a thin scene adapter over `recover_live_context()`
- derive structured judgments and recommendations in the scene layer rather than teaching the foundation a second workflow