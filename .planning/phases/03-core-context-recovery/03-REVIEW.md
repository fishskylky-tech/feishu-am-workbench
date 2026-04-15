---
phase: "03"
depth: standard
scope_source: summaries-key_files
scope_files:
  - runtime/models.py
  - runtime/semantic_registry.py
  - evals/meeting_output_bridge.py
  - runtime/live_adapter.py
  - tests/test_meeting_output_bridge.py
findings_count: 2
status: findings
---

# Phase 3 Code Review

## Findings

### High

1. `runtime/live_adapter.py:666-667` fabricates customer evidence onto every Drive candidate before ranking, which makes the fallback scorer trust documents more than the raw data justifies.

`_discover_drive_candidates()` writes the requested `customer_id` and `short_name` directly into every returned candidate object, and `_rank_drive_candidates()` in `evals/meeting_output_bridge.py` then awards +20/+10 for exact customer matches. Because those fields were injected by the adapter rather than discovered from Drive metadata, every surviving fallback candidate is treated as customer-confirmed evidence. In the single-candidate path, `_resolve_archive_context()` upgrades that result to `客户档案候选` with normal write ceiling, so a loosely matched title inside the folder can be treated as high-confidence recovery. This violates the recommendation-first safety boundary the phase was supposed to preserve.

Affected references:
- `runtime/live_adapter.py:635-669`
- `evals/meeting_output_bridge.py:319-341`
- `evals/meeting_output_bridge.py:380-398`

Recommended fix:
- Stop stamping `customer_id` / `short_name` onto raw Drive candidates unless that metadata actually comes from the Drive payload.
- Score customer affinity only from observable evidence such as title/path fields or future structured metadata.
- Add a regression proving that a single fuzzy title hit without explicit customer evidence remains recommendation-only.

### Medium

2. `evals/meeting_output_bridge.py:264-273` accepts multiple top-ranked meeting-note fallback candidates as a successful recovery instead of surfacing them as uncertainty.

When contact-log-derived notes are absent, `_discover_meeting_note_candidates()` returns every top-scored candidate from `_rank_drive_candidates()`. `recover_live_context()` then unconditionally appends `会议纪要候选` and renders all returned entries into `key_context`, but it never records a candidate conflict or downgrades `write_ceiling`. Archive conflicts already go through `candidate_conflicts`; meeting-note conflicts do not. The result is asymmetric behavior: duplicate archive candidates lower trust, while duplicate meeting-note candidates still look like a successful fallback path.

Affected references:
- `evals/meeting_output_bridge.py:264-273`
- `evals/meeting_output_bridge.py:347-363`
- `evals/meeting_output_bridge.py:380-398`

Recommended fix:
- Make meeting-note fallback return structured conflict information, not just rendered strings.
- If more than one top candidate survives, add an open question / candidate conflict entry and force `recommendation-only`, matching the archive path.
- Add a regression where two same-score meeting-note candidates keep the scene in a downgraded audit state.

## Scope Notes

- Review scope was derived from Phase 3 summary artifacts because the current SUMMARY frontmatter uses `key_files` rather than `key_files.created` / `key_files.modified`; relying on the workflow's git-diff fallback here would have mixed in unrelated working-tree changes.
- No additional security or code-quality findings were identified in `runtime/models.py` or `runtime/semantic_registry.py` beyond the two fallback-path issues above.

## Residual Risk

- The new audit frame is directionally correct, but as long as fallback evidence is partially synthesized and meeting-note conflicts are not first-class, the scene can still overstate context confidence in edge cases.
