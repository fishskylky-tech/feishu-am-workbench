# Phase 27 Plan 02: Add Hallucination Guardrail Summary

## One-liner

Hallucination guardrail in `_parse_result()` that BLOCKs entire result if any LLM finding references a signal not in `check_signals` list.

## Commits

| Hash | Message |
|------|---------|
| f9eee36 | feat(27-02): add hallucination guardrail to _parse_result() |
| f5a0a63 | test(27-02): add 8 hallucination guardrail tests |

## Tasks Completed

### Task 1: Implement hallucination guardrail in _parse_result()

**Files modified:** `runtime/default_llm_adapter.py`

- Added `_check_hallucination()` helper method that validates findings against `check_signals`
- Modified `_parse_result()` to accept `context` dict and `in_eval_context` flag
- Case-insensitive, whitespace-tolerant signal name comparison
- Hyphenated and multi-word signal names supported via `r'^(PASS|FLAG|BLOCK):\s*([^\n]+)'` pattern
- Single fabricated signal → BLOCKs entire result (per review MEDIUM fix)
- Production (`in_eval_context=False`): missing `check_signals` raises `ValueError` (NOT silent accept-all)
- Eval context (`in_eval_context=True`): backward-compatible accept-all fallback

### Task 2: Add hallucination guardrail tests

**Files modified:** `tests/test_default_llm_adapter.py`

Added 8 test cases covering:
- BLOCK fabricated signal detection
- PASS when all signals valid
- Eval context fallback behavior
- Production requires check_signals
- Case-insensitive signal matching
- Hyphenated signal names
- Multi-word signal names
- Mixed valid + fabricated signals

## Acceptance Criteria

- [x] `_parse_result()` accepts `context` parameter with `check_signals` list
- [x] Fabricated signals trigger `blocked=True` and `passed=False`
- [x] Valid signals pass normally
- [x] Hyphenated signal names handled correctly
- [x] Multi-word signal names handled correctly
- [x] Case-insensitive comparison
- [x] Eval context fallback: no check_signals + `in_eval_context=True` -> accept all
- [x] Production: no check_signals + `in_eval_context=False` -> raises ValueError
- [x] All 8 hallucination tests pass
- [x] All 22 tests in test_default_llm_adapter.py pass

## Deviations from Plan

None - plan executed exactly as written.

## Threat Surface

| Flag | File | Description |
|------|------|-------------|
| N/A | runtime/default_llm_adapter.py | Guardrail adds validation at LLM->Application trust boundary |

## Self-Check: PASSED

- Implementation: FOUND
- Tests: 22/22 pass
- Commits: f9eee36, f5a0a63 verified
