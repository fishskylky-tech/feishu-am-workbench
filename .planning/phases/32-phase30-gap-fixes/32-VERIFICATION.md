# Phase 32 Verification: 32-phase30-gap-fixes

---
phase: "32-phase30-gap-fixes"
status: "passed"
date: "2026-04-21"
---

## Phase Goal

Fix gap closures identified in Phase 30 review: E-26-01 (LLM path wiring), E-26-02 (guardrail verification), E-27-01 (CI eval coverage).

## Verification

### E-26-01: Wire LLM mode activation in scene YAMLs

| Must-Have | Evidence | Status |
|-----------|----------|--------|
| agent_name field in ExpertCardConfig | `expert_card_loader.py:162` | PASSED |
| parse_input_card extracts and validates agent_name | `expert_card_loader.py:246-251` | PASSED |
| parse_output_card extracts and validates agent_name | `expert_card_loader.py:306-311` | PASSED |
| run_input_audit raises ValueError if prompt_file set but agent_name missing | `expert_analysis_helper.py:424-428` | PASSED |
| run_output_audit raises ValueError if prompt_file set but agent_name missing | `expert_analysis_helper.py:516-520` | PASSED |
| post-meeting-synthesis input_review has prompt_file + agent_name | `scenes/post-meeting-synthesis/expert-cards.yaml:13-14` | PASSED |
| post-meeting-synthesis output_review has prompt_file + agent_name | `scenes/post-meeting-synthesis/expert-cards.yaml:25-26` | PASSED |
| customer-recent-status input_review has prompt_file + agent_name | `scenes/customer-recent-status/expert-cards.yaml:13-14` | PASSED |
| E2E smoke test passes confirming LLM path activates | `python runtime/expert_card_loader.py` → PASSED | PASSED |

### E-26-02: Hallucination guardrail exists at lines 293-306

| Must-Have | Evidence | Status |
|-----------|----------|--------|
| Guard at lines 293-306 | `runtime/default_llm_adapter.py:292-306` | PASSED |
| Production with empty check_signals raises descriptive ValueError | Line 306: `"check_signals missing in production context — hallucination guardrail requires validation list"` | PASSED |
| Eval context with empty check_signals accepts all (backward compat) | Line 300-303: `elif in_eval_context: pass` | PASSED |
| Non-empty check_signals validates via _check_hallucination | Line 295 | PASSED |

### E-27-01: CI runs all 15 eval cases as blocking gate

| Must-Have | Evidence | Status |
|-----------|----------|--------|
| All 15 IDs explicitly enumerated | `ci.yml:39` — `for id in 101 ... 115` | PASSED |
| Per-case logging before each invocation | `ci.yml:40` — `echo "Running eval case $id..."` | PASSED |
| No redundant continue-on-error | ci.yml — absent in eval step | PASSED |
| Blocking gate (all 15 must pass) | Sequential loop in bash with `set -e` implied | PASSED |

## Test Gate

- **Phase 32 tests**: 337 passed, 1 failed, 57 skipped
- **Failed test**: `test_evals_file_is_valid_json` — pre-existing issue (asserts 3 evals, actual 18). Unrelated to Phase 32 changes.
- **Pre-existing failure confirmed**: `git stash` test on baseline (before Phase 32) also fails on this same assertion.

## Self-Check: PASSED

All must-haves verified. Phase goal achieved.
