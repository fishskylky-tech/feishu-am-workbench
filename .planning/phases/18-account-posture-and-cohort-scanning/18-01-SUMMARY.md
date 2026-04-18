# Phase 18 Plan 01 Summary: STAT-01 Four-Lens Account Posture Output

## Plan Overview

**Plan:** 18-01
**Phase:** 18-account-posture-and-cohort-scanning
**Status:** Complete
**Requirement:** STAT-01

## Objective

STAT-01: Upgrade `run_customer_recent_status_scene()` to produce four-lens account-posture output (risk, opportunity, relationship, project_progress) as labeled sub-items within the judgments field. Each lens draws from relevant EvidenceContainer sources per D-10.

## What Was Built

### 1. LensAttribution Type and build_lens_attributions (expert_analysis_helper.py)

**Commit:** `4843af9`

- Added `LensLabel = Literal["risk", "opportunity", "relationship", "project_progress"]`
- Added `LensAttribution` dataclass with fields: `lens: LensLabel`, `source_names: list[EvidenceSourceName]`, `conclusions: list[str]`, `confidence: float = 1.0`
- Added `LENS_SOURCE_MAP` mapping each lens to its relevant source names:
  - `risk` -> `["customer_master", "contact_records", "action_plan"]`
  - `opportunity` -> `["customer_master", "meeting_notes", "action_plan"]`
  - `relationship` -> `["contact_records", "meeting_notes"]`
  - `project_progress` -> `["action_plan", "meeting_notes", "customer_archive"]`
- Added `build_lens_attributions(container, lens_results)` function that creates per-lens `LensAttribution` objects from keyword extraction results

### 2. Four-Lens Derivation and Rendering (scene_runtime.py)

**Commit:** `d7f075c`

- Added `_STAT_RISK_KEYWORDS`, `_STAT_OPPORTUNITY_KEYWORDS`, `_STAT_RELATIONSHIP_KEYWORDS`, `_STAT_PROJECT_PROGRESS_KEYWORDS` keyword sets
- Added `_derive_account_posture_lenses(evidence_container)` function: extracts 1-3 keyword conclusions per lens from relevant sources using `LENS_SOURCE_MAP`, capped at 3 per lens
- Added `_render_four_lens_judgments(lens_results)` function: emits labeled judgment strings in format `"{label}: {conclusion1}; {conclusion2}"` per D-01
- Modified `run_customer_recent_status_scene()`:
  - Calls `_derive_account_posture_lenses()` on the evidence container after existing judgment logic
  - Appends four-lens judgments to the existing judgments list (additive, not replacing)
  - Adds `lens_attributions` to `scene_payload` for per-lens source traceability per D-10
  - Existing fallback/recommendation logic unchanged

### 3. STAT-01 Test Suite (test_scene_runtime.py)

**Commit:** `3ab9874`

- Added `TestStat01FourLensOutput` with 7 test methods covering:
  - Function existence
  - Four-key return shape
  - Keyword extraction per LENS_SOURCE_MAP
  - Labeled judgment string emission
  - Empty-lens skip behavior
  - 3-conclusion cap
  - None container handling
- Added `TestStat01LensAttribution` with 1 test method covering `build_lens_attributions` output shape and source name mapping

## Verification

| Check | Result |
|-------|--------|
| `pytest tests/test_scene_runtime.py -x -q` | 29 passed |
| `pytest tests/test_scene_runtime.py::TestStat01FourLensOutput -x -q` | 8 passed |
| `pytest tests/test_scene_runtime.py::TestStat01LensAttribution -x -q` | 1 passed |
| Manual import verification | PASS |

## Success Criteria Status

| Criterion | Status |
|-----------|--------|
| Four-lens output (risk/opportunity/relationship/project_progress) appears as labeled sub-items in judgments field | Met |
| Each lens produces 1-3 conclusions (keyword-based) | Met |
| Lens attributions stored in `payload["lens_attributions"]` traceable to EvidenceContainer sources | Met |
| Existing fallback/recommendation logic unchanged | Met |
| SceneResult contract unchanged (all existing fields preserved) | Met |

## Commits

| Commit | Description |
|--------|-------------|
| `4843af9` | feat(phase-18): add LensAttribution type and build_lens_attributions for STAT-01 |
| `d7f075c` | feat(phase-18): add four-lens account posture output to run_customer_recent_status_scene |
| `3ab9874` | test(phase-18): add STAT-01 four-lens tests to test_scene_runtime.py |

## Files Modified

| File | Change |
|------|--------|
| `runtime/expert_analysis_helper.py` | +38 lines: LensLabel, LensAttribution, LENS_SOURCE_MAP, build_lens_attributions |
| `runtime/scene_runtime.py` | +86 lines, -1: four-lens keyword sets, _derive_account_posture_lenses, _render_four_lens_judgments, integrated into run_customer_recent_status_scene |
| `tests/test_scene_runtime.py` | +124 lines: TestStat01FourLensOutput (7 tests), TestStat01LensAttribution (1 test) |
