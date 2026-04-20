# AI-SPEC.md — Phase 27 Supplement: Expert Review Eval Infrastructure

> **Note:** Retrospective AI-SPEC supplement. Phase 27 built eval infrastructure
> but did not produce AI-SPEC.md.

**Phase:** 27 — Expert Review Eval Infrastructure
**System Type:** Extraction — LLM expert review evaluation
**Generated:** 2026-04-21 (retrospective)
**Addresses:** E-27-01, E-27-02, E-27-03 from 30-GAP-REPORT.md

---

## 1. System Classification

**System Type:** Extraction — Structured evaluation of LLM expert review outputs

**Description:**
Eval infrastructure validates that LLM-based expert review produces accurate signal detection. Reference dataset (evals/evals.json) contains 15 labeled cases (ids 101-115) covering normal accuracy, missing signal detection, and hallucination detection. Eval runner (evals/runner.py) runs pattern-based assertions against LLM outputs.

**Critical Failure Modes:**
1. Eval dataset too small — 15 cases insufficient to catch all failure modes (MEDIUM)
2. Pattern-based assertions miss semantic errors — regex cannot detect meaning errors (HIGH)
3. Hallucination detection only in eval context — production with empty check_signals fails (MEDIUM)
4. CI partial coverage — only 3 of 15 cases run in CI (HIGH)

---

## 1b. Domain Context

**Industry Vertical:** B2B SaaB customer success (same as Phase 24/26)

**User Population:** Internal AI system consuming expert review evaluation

**Stakes Level:** Medium — eval failures mean expert review may produce wrong signals

**Output Consequence:** Eval failures in CI block deployment

### What Domain Experts Evaluate Against

| Dimension | Good | Bad | Stakes |
|-----------|------|-----|--------|
| Normal accuracy | PASS for evidence-present signals | Missed detections | HIGH |
| Missing signal | FLAG for absent signals | False negatives | HIGH |
| Hallucination detection | BLOCK for fabricated signals | False positives | HIGH |

---

## 2. Framework Decision

**Selected Framework:** Pattern-based assertion runner (custom)

**Version:** N/A — custom implementation in evals/runner.py

**Rationale:**
Phase 27 built a lightweight pattern-matching eval runner rather than using a full LLM-judge-based evaluation framework. Pattern matching is deterministic and fast but cannot detect semantic errors.

**Alternatives Considered:**

| Framework | Ruled Out Because |
|-----------|------------------|
| LLM-judge-based evaluation | Overkill for deterministic pattern matching |
| RAGAS or Braintrust | Designed for RAG; not applicable to signal detection |

---

## Eval Dataset Structure

The reference dataset in `evals/evals.json` contains 15 labeled cases:

| Case IDs | Category | Coverage |
|----------|----------|----------|
| 101-105 | Normal accuracy | Evidence-present signals should PASS |
| 106-110 | Missing signal detection | Absent signals should FLAG |
| 111-115 | Hallucination detection | Fabricated signals should BLOCK |

Each case structure:
```json
{
  "id": 101,
  "name": "expert-review-sales-account",
  "scenario": "LLM expert review accuracy",
  "evidence": {"customer_master": ["..."], "recent_meetings": [...]},
  "check_signals": ["expansion_plan", "timeline"],
  "expected_findings": ["PASS: expansion_plan", "FLAG: timeline missing concrete date"],
  "prompt_file": "sales-account-strategist.md"
}
```

---

## CI Coverage Strategy (HIGH — E-27-01)

> **Status:** NOT FULLY ADDRESSED — Only 3 of 15 eval cases run in CI

### Current CI Configuration

ci.yml runs ONLY 3 of 15 eval cases:

| Case ID | Category | Rationale for Selection |
|---------|----------|------------------------|
| 101 | Normal-1 | Representative of baseline accuracy — clean evidence with expected PASS |
| 106 | Missing-signal-1 | Representative of missing signal detection — one absent signal should FLAG |
| 111 | Fabricated-signal-1 | Representative of hallucination detection — one fabricated signal should BLOCK |

### Gap Analysis: Why This Is HIGH Severity

**Missing 12 Cases and Risk:**
| Case IDs | Category | Risk If Not Run in CI |
|----------|----------|----------------------|
| 102-105 | Normal-2 through Normal-5 | Edge case regressions (subtle signals, multiple signals) NOT caught |
| 107-110 | Missing-signal-2 through Missing-signal-5 | Edge cases (partially present, multiple missing) NOT validated |
| 112-115 | Fabricated-signal-2 through Fabricated-signal-5 | Edge cases (subtle fabrications, multiple fabricated) NOT validated |

**Impact:**
- 80% of eval cases never run in PR validation
- Regressions in edge cases (cases 102-105, 107-110, 112-115) are NOT caught
- False confidence: CI passing does not mean "all 15 cases pass"

### CI Coverage Strategy Options

**Option A — Immediate (Recommended): Run All 15 in CI**
```yaml
# In .github/workflows/ci.yml
- name: Run all eval cases
  run: python -m evals.runner --eval-id 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115
```
Pros: Simple, comprehensive, catches all edge cases
Cons: CI time increases (~4x from 3 to 15 cases)

**Option B — Near-term: Two-Tier CI**
```yaml
# PR gate: 3 representative cases (current)
- name: Run representative eval cases
  run: python -m evals.runner --eval-id 101 106 111

# Nightly regression: all 15 cases
- name: Run full eval regression
  run: python -m evals.runner --eval-id 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115
  if: github.event_name == 'schedule'
```
Pros: Fast PR validation, comprehensive nightly coverage
Cons: Edge case regressions may not block PR

**Option C — Accept Current: Document as Design Decision**
- Only valid if 3 cases are proven statistically representative of all 15
- No evidence provided that 3-case sample is sufficient
- Not recommended without statistical validation

### Recommended Immediate Action
Update ci.yml to run all 15 cases. If CI time is a concern, implement Option B (two-tier).

---

## Hallucination Guardrail Eval-Context-Only Bug (E-27-02)

> **Related to E-26-02:** This is the same bug seen from the eval infrastructure perspective

The hallucination guardrail (`_check_hallucination()`) only runs when:
1. `check_signals` is non-empty (eval cases always provide this)
2. The LLM code path is actually executed (but LLM mode is never activated — E-26-01)

**Impact on Eval:**
- All 15 eval cases have non-empty check_signals
- Eval infrastructure never catches the empty-check_signals production bug
- The bug only manifests in production when a scene calls expert review with empty check_signals

**Fix Required:** Fix in Phase 26 (E-26-02) adds empty-check_signals guard to `_check_hallucination()`

---

## 5. Evaluation Strategy

### Dimensions

| Dimension | Rubric | Measurement | Priority |
|-----------|--------|-------------|----------|
| Normal case accuracy (101-105) | All expected PASS actual PASS | Code: pattern match | Critical |
| Missing signal detection (106-110) | All expected FLAG actual FLAG | Code: pattern match | Critical |
| Hallucination detection (111-115) | All expected BLOCK actual BLOCK | Code: pattern match | Critical |
| Fallback reliability | LLM failure keyword mode | Manual only | High |
| CI coverage | All 15 cases run in CI | Audit ci.yml | High |

### Eval Tooling

**Primary Tool:** `evals/runner.py`

**Reference Dataset:** 15 labeled cases in `evals/evals.json` (ids 101-115)

**CI Integration:** Partial — 3 cases run (101, 106, 111); should be all 15

---

## 6. Guardrails

### Online (Real-Time)

| Guardrail | Trigger | Intervention |
|-----------|---------|--------------|
| Hallucination guardrail | Finding not in check_signals | BLOCK: blocked=True (BUG: ValueError on empty check_signals) |

### Offline (Flywheel)

| Metric | Sampling | Action |
|--------|----------|--------|
| Eval pass rate | All 15 cases per CI run | Block if any fail |
| Case 101-105 fail rate | Per CI run | Alert if >0% |
| Case 106-110 fail rate | Per CI run | Alert if >10% |
| Case 111-115 fail rate | Per CI run | Alert if >0% |

---

## 7. Production Monitoring

**Tracing Tool:** None

**Gap:** No production observability for expert review quality. Eval infrastructure only runs in CI.

---

## Security & Compliance

**Eval Dataset Security:**
- eval cases contain synthetic evidence (not real customer data)
- No sensitive data in eval dataset
- Status: ACCEPTABLE — synthetic data used

**CI Pipeline Security:**
- eval runner executed in CI environment
- LLM API calls made from CI runners
- API keys must be available in CI env
- Status: STANDARD — same security model as production

**Log Sanitization:**
- Eval outputs logged at INFO level in CI
- No customer PII in eval evidence (synthetic)
- Status: ACCEPTABLE — synthetic evidence only

**Failure Degradation:**
- If eval fails, CI job fails (correct behavior)
- No graceful degradation for eval failures
- Status: APPROPRIATE — eval failures should block deployment

---

## Checklist

- [x] System type classified (Extraction / Evaluation)
- [x] Critical failure modes identified (4 modes)
- [x] Domain context documented
- [x] Framework decision documented (pattern-based runner)
- [x] Eval dataset structure documented (15 cases, 3 categories)
- [x] CI coverage strategy documented (E-27-01)
- [x] CI coverage rationale (why 3 cases selected)
- [x] CI coverage options (A: all 15, B: two-tier, C: accept)
- [x] Hallucination guardrail eval-context-only bug documented (E-27-02)
- [x] Evaluation dimensions (5 dimensions)
- [x] Guardrails defined (online + offline)
- [x] Production monitoring gap noted
- [x] Security & compliance (4 areas)
- [x] Phase 27 eval infrastructure coverage confirmed (evals/runner.py, evals/evals.json, ci.yml)
