# Phase 14 Context

Phase 14 uses the shared scene runtime contract on a second workflow: customer recent status.

The phase must prove that the runtime seam is reusable for a read-heavy AM workflow without pushing business-specific logic back into the foundation layer.

Required outcome:

- explicit `customer-recent-status` scene dispatch
- structured `facts`, `judgments`, `open_questions`, and `recommendations`
- reuse of gateway + targeted read + fallback visibility + write ceiling semantics