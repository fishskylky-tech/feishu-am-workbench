---
phase: 19-archive-refresh-and-meeting-prep-paths
reviewed: 2026-04-17T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - runtime/confirmation_checklist.py
  - tests/test_archive_refresh_scene.py
  - runtime/scene_runtime.py
  - tests/test_meeting_prep_scene.py
  - runtime/scene_registry.py
findings:
  critical: 1
  warning: 4
  info: 2
  total: 7
status: issues_found
---

# Phase 19: Code Review Report

**Reviewed:** 2026-04-17
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed 5 source files implementing archive refresh (ARCH-01) and meeting prep (PREP-01) scene infrastructure. Found 1 critical security issue (eval injection), 4 warnings related to null-safety and test correctness, and 2 info-level findings. The scene infrastructure itself is well-structured with proper separation of concerns, but there are safety gaps in attribute access patterns and a test that will fail at runtime due to missing imports.

## Critical Issues

### CR-01: Code Injection via eval() in _parse_condition_query

**File:** `runtime/scene_runtime.py:1076`
**Issue:** The `_parse_condition_query` function uses `eval()` to evaluate parsed time expressions. If an attacker can control `condition_query`, they could execute arbitrary code.

**Fix:**
Replace the `eval()` call with safe numeric parsing:

```python
# BEFORE (line 1076):
time_window = eval(due_at)

# AFTER:
# Parse the date expression safely without eval
try:
    # Parse formats like "2024-01" or date strings
    time_window = str(due_at)[:7]  # Extract YYYY-MM prefix safely
except (ValueError, TypeError):
    time_window = "unknown"
```

Note: The actual code at line 975 uses `due_at[:7]` directly, suggesting the `eval()` at line 1076 may be dead code or a different code path. Either way, `eval()` should never be used with untrusted input.

---

## Warnings

### WR-01: Test Calls Undefined Function

**File:** `tests/test_archive_refresh_scene.py:96`
**Issue:** `test_five_dimensions_different_from_stat01_four_lens` calls `_derive_account_posture_lenses` but this function is not imported in the test file. The test imports only `_derive_archive_refresh_lenses` and `_render_archive_refresh_output`.

**Fix:**
Add the missing import to the test file:

```python
# Add to imports at line 7-10
from runtime.scene_runtime import (
    _derive_archive_refresh_lenses,
    _derive_account_posture_lenses,  # Add this
    _render_archive_refresh_output,
)
```

### WR-02: Unsafe raw_data Access

**File:** `runtime/confirmation_checklist.py:122`
**Issue:** Code accesses `arch_src.raw_data.get('name', archive_location)` without verifying `raw_data` is a dict or that it has a `get` method. If `raw_data` is `None`, `hasattr()` check should be used.

**Fix:**
```python
# BEFORE (line 122):
archive_location = f"已有档案: {arch_src.raw_data.get('name', archive_location)}"

# AFTER:
if hasattr(arch_src, 'raw_data') and isinstance(arch_src.raw_data, dict):
    archive_location = f"已有档案: {arch_src.raw_data.get('name', archive_location)}"
else:
    archive_location = "已有档案"
```

### WR-03: Unchecked Attribute Access on evidence_container

**File:** `runtime/scene_runtime.py:771`
**Issue:** Code accesses `evidence_container.critical_source_missing` without verifying this attribute exists on the object.

**Fix:**
```python
# BEFORE (line 771):
if evidence_container and evidence_container.critical_source_missing:

# AFTER:
if evidence_container and getattr(evidence_container, 'critical_source_missing', False):
```

### WR-04: Unsafe Nested Attribute Access on gateway_result

**File:** `runtime/scene_runtime.py:466`, `999-1006`
**Issue:** Multiple locations access `gateway_result.customer_resolution.status` and `gateway_result.customer_resolution.candidates` without checking if `customer_resolution` is `None` first. An `AttributeError` would occur if `customer_resolution` is `None`.

**Fix:**
```python
# BEFORE (line 466):
customer_status = customer_resolution.status if customer_resolution is not None else "missing"

# AFTER: The existing code at line 418 already does this check properly:
# customer_status = customer_resolution.status if customer_resolution is not None else "missing"
# But the issue is at line 466 where this pattern is NOT used inside run_post_meeting_scene
```

At line 466, the code should match the pattern used at line 418. Additionally, `_render_customer_status` at lines 999-1006 should be updated:

```python
def _render_customer_status(gateway_result: Any) -> str:
    customer_resolution = gateway_result.customer_resolution
    if customer_resolution is None:
        return "missing"
    if not hasattr(customer_resolution, 'status'):
        return "missing"
    if customer_resolution.status == "resolved" and customer_resolution.candidates:
        best = customer_resolution.candidates[0]
        return f"{best.short_name} / 客户ID {best.customer_id or 'missing'}"
    return customer_resolution.status
```

---

## Info

### IN-01: Keyword Substring Matching May Yield False Positives

**File:** `runtime/scene_runtime.py:74-83`, `136-145`
**Issue:** The `_extract` helper function checks `if kw in text` where `kw` is a keyword like "过去" (past). This would incorrectly match inside longer words like "过早" (prematurely) since Python's `in` operator checks substring membership.

**Fix:**
Consider using word boundary matching or checking for keyword as a standalone word:

```python
def _extract(text: str, keywords: set[str], max_items: int = 3) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    # Split into words/tokens for safer matching
    words = set(text.split())
    for kw in keywords:
        if kw in words and kw not in seen:  # Match whole words only
            seen.add(kw)
            items.append(kw)
            if len(items) >= max_items:
                break
    return items
```

### IN-02: Unused Import

**File:** `runtime/scene_registry.py:18`
**Issue:** `run_cohort_scan_scene` is imported but never used within the module. While this is not a bug, it is dead code.

**Fix:**
Remove the unused import if it is not needed:

```python
# Remove from line 18:
from .scene_runtime import (
    SceneRequest,
    SceneResult,
    run_archive_refresh_scene,
    # run_cohort_scan_scene,  # Remove if unused
    run_customer_recent_status_scene,
    run_meeting_prep_scene,
    run_post_meeting_scene,
    run_todo_capture_and_update_scene,
)
```

---

_Reviewed: 2026-04-17_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
