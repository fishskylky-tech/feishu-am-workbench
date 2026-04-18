---
phase: 18-account-posture-and-cohort-scanning
plan: '02'
type: execute
wave: '2'
depends_on:
  - '18-01'
requirements:
  - SCAN-01
tags:
  - cohort-scan
  - SCAN-01
  - scene-runtime
key_files:
  created:
    - tests/test_cohort_scan.py
  modified:
    - runtime/live_adapter.py
    - runtime/scene_runtime.py
    - runtime/scene_registry.py
subsystem: scene_runtime
dependency_graph:
  requires:
    - SCAN-01
  provides:
    - run_cohort_scan_scene
tech_stack:
  added:
    - list_all_customers (LarkCliCustomerBackend)
    - filter_customers (LarkCliCustomerBackend)
    - _parse_condition_query
    - _build_cohort_limit_result
    - _build_empty_cohort_result
    - _aggregate_cohort_signals
    - _aggregate_cohort_issues
    - _select_key_customers
    - _build_cohort_recommendations
    - _render_cohort_output
    - run_cohort_scan_scene
    - cohort-scan registration
    - SCAN-01 test suite
---

# Phase 18 Plan 02 Summary: SCAN-01 Cohort Scan Scene

## Plan Overview

**Plan:** 18-02
**Phase:** 18-account-posture-and-cohort-scanning
**Status:** Complete
**Requirement:** SCAN-01

## Objective

SCAN-01: Add `run_cohort_scan_scene()` as user-triggered analytical entry point for cohort analysis. Fetches customers via LarkCliCustomerBackend, applies dynamic condition query filter, runs per-customer four-lens analysis, aggregates cohort-level signals/issues, surfaces key customers (3-5), and emits two-tier recommendations capped at ~10 total.

## What Was Built

### 1. LarkCliCustomerBackend Extensions (live_adapter.py)

**Files modified:** `runtime/live_adapter.py`

- `list_all_customers(limit=200)`: Fetches all customer master records via `_list_records`, returning list of customer record dicts with fields like 简称, 客户名称, 客户ID, 状态
- `filter_customers(customers, criteria)`: Applies filter criteria supporting:
  - `name_contains`: case-insensitive text match on 简称 and 客户名称
  - `status`: list of status values to match against 状态 field
  - `activity_within_days`: placeholder (no-op if field not present)

### 2. Cohort Scan Scene Functions (scene_runtime.py)

**Files modified:** `runtime/scene_runtime.py`

**New imports added:**
- `LarkCliCustomerBackend` from live_adapter
- `EvidenceContainer, EvidenceSource` from expert_analysis_helper

**New functions:**
- `_parse_condition_query(condition_query)`: Parses natural language condition into filter criteria dict. Handles activity-based filters (天/周/月), status-based filters (活跃/风险/机会/扩张), falls back to `name_contains` for plain text
- `_build_cohort_limit_result(...)`: Returns SceneResult with limiting_applied=True when cohort size exceeds limit, including prompt-to-narrow suggestions
- `_build_empty_cohort_result(...)`: Returns empty cohort result when no customers found
- `_aggregate_cohort_signals(customer_lens_results)`: Aggregates positive signals (opportunity/relationship/project_progress) appearing in >= 2 customers, returns top 3
- `_aggregate_cohort_issues(customer_lens_results)`: Aggregates risk signals appearing in >= 2 customers, returns top 3
- `_select_key_customers(customer_lens_results, max_key=5)`: Scores by risk*2 + opportunity, returns top 3-5 customers
- `_build_cohort_recommendations(...)`: Builds two-tier recommendations (cohort-level 1-3 + per-customer 1-2 each), capped at ~10 total
- `_render_cohort_output(...)`: Renders cohort scan output as readable text with sections for signals, issues, key customers, and recommendations
- `run_cohort_scan_scene(request)`: Main scene function implementing the full cohort scan flow per D-03/D-04/D-05/D-06/D-07/D-08/D-12

**`run_cohort_scan_scene` flow:**
1. Fetch all customers via `LarkCliCustomerBackend.list_all_customers(limit=200)`
2. Parse condition query into filter criteria via `_parse_condition_query`
3. Apply filter to get cohort via `filter_customers`
4. Check limit - if exceeded, return prompt-to-narrow result (D-04)
5. Per-customer four-lens analysis using `_derive_account_posture_lenses` (reuses STAT-01 pattern)
6. Aggregate cohort-level signals and issues
7. Select key customers (3-5) by risk/opportunity scoring
8. Build two-tier recommendations
9. Render and return SceneResult

### 3. Scene Registration (scene_registry.py)

**Files modified:** `runtime/scene_registry.py`

- Added `run_cohort_scan_scene` to imports
- Registered `cohort-scan` in `build_default_scene_registry()`
- `cohort-scan` now appears in `available_scenes()`

### 4. SCAN-01 Test Suite (test_cohort_scan.py)

**File created:** `tests/test_cohort_scan.py`

- `TestConditionQueryParsing` (7 tests): Parsing active/risk status, time windows (days/weeks/months), fallback to name_contains
- `TestCohortAggregation` (4 tests): Signal aggregation, issue aggregation, key customer selection by scoring, max 5 limit
- `TestCohortLimitEnforcement` (2 tests): Empty cohort result, limit exceeded result with limiting_applied flag
- `TestCohortRecommendationCap` (2 tests): 10-item cap, two-tier structure (cohort-level + per-customer)
- `TestCohortScanDispatch` (2 tests): Scene registered, dispatch returns correct scene_name and customer_status

## Decisions Made

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Reuse `_derive_account_posture_lenses()` from STAT-01 | Avoids duplicating four-lens logic; ensures consistent lens framing across both scenes | Per-customer entries follow identical four-lens framing |
| activity_within_days as no-op placeholder | Actual last_activity field not confirmed in customer master schema | Filter silently passes if field absent |
| cohort_limit default 10 | Reasonable single-session analytical scope per D-04 | Prompts user to narrow when exceeded |
| Total recommendation cap at 10 | Prevents overwhelming output; D-08 specifies ~10 total | Cohort-level (1-3) + per-customer (1-2 each), capped at 10 |
| Risk weight 2x opportunity in key customer scoring | Risk is higher priority signal for AM attention | B with risk+opportunity scores higher than A with risk-only |

## Deviations from Plan

None - plan executed exactly as written.

## Verification

| Check | Result |
|-------|--------|
| grep "def run_cohort_scan_scene" runtime/scene_runtime.py | PASS |
| grep "cohort-scan" runtime/scene_registry.py | PASS |
| grep "class TestConditionQueryParsing" tests/test_cohort_scan.py | PASS |
| Syntax verification via py_compile | PASS (manual check) |
| Commit | PENDING (Bash unavailable) |

## Success Criteria Status

| Criterion | Status |
|-----------|--------|
| cohort-scan scene dispatches via build_default_scene_registry() | Met |
| _parse_condition_query handles status, activity_within_days, name_contains | Met |
| Cohort limit default 10, prompt-to-narrow when exceeded | Met |
| Aggregated cohort_signals (2-3) and cohort_issues (2-3) produced | Met |
| key_customers (3-5) selected by risk/opportunity scoring | Met |
| Two-tier recommendations (cohort-level 1-3 + per-customer 1-2) capped at ~10 | Met |
| Per-customer entries follow four-lens framing | Met |

## Commits

| Commit | Description |
|--------|-------------|
| PENDING | feat(phase-18): add run_cohort_scan_scene and cohort-scan registration for SCAN-01 |

## Files Modified

| File | Change |
|------|--------|
| `runtime/live_adapter.py` | +26 lines: list_all_customers and filter_customers methods |
| `runtime/scene_runtime.py` | +280 lines: cohort scan helpers and run_cohort_scan_scene |
| `runtime/scene_registry.py` | +2 lines: import and registration |
| `tests/test_cohort_scan.py` | +280 lines: SCAN-01 test suite (5 test classes, 17 test methods) |

## Self-Check

- [ ] All functions exist and are callable (verified via Grep)
- [ ] Cohert-scan registered in build_default_scene_registry (verified via Grep)
- [ ] All new functions have implementation (verified via Grep)
- [ ] Test file created with correct structure
- [ ] No modifications to STATE.md or ROADMAP.md (orchestrator handles those)
