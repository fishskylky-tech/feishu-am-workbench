# AI-SPEC.md — Phase 26 Supplement: Expert Review Runtime Integration

> **Note:** Retrospective AI-SPEC supplement. Phase 26 implemented LLM runtime integration
> but did not produce AI-SPEC.md. Documents the actual implementation decisions.

**Phase:** 26 — Expert Review Runtime Integration
**System Type:** Conversational / Extraction — LLM-based expert review
**Generated:** 2026-04-21 (retrospective)
**Addresses:** E-26-01, E-26-02, E-26-03 from 30-GAP-REPORT.md

---

## 1. System Classification

**System Type:** Conversational — Structured expert review with pass/fail/flag/block outputs

**Description:**
Scene runtime extends expert card audit layer to use LLM-based review. When `prompt_file` is set on an ExpertCardConfig, the runtime invokes the LLM using agency-agents prompt templates. On LLM failure, falls back to keyword-based audit. This enables gradual migration from keyword to AI mode.

**Critical Failure Modes:**
1. Hallucinated signals — LLM invents signals not in evidence (HIGH)
2. Fallback loop — LLM fails keyword LLM fails keyword (MEDIUM)
3. Parse failure — LLM response does not match PASS/FLAG/BLOCK format (MEDIUM)
4. API key exposure — logging or error messages leak credentials (HIGH — security)
5. LLM mode never activated — scene expert-cards.yaml lacks prompt_file field (CRITICAL)

---

## 1b. Domain Context

**Industry Vertical:** B2B SaaB customer success management

**User Population:** Internal AI system (scene runtime) consuming expert review

**Stakes Level:** Medium — Expert review is advisory; human reviews output before write actions

**Output Consequence:** Expert findings determine whether scene output is blocked, flagged, or approved for writing to Feishu

### What Domain Experts Evaluate Against

| Dimension | Good | Bad | Stakes |
|-----------|------|-----|--------|
| Signal accuracy | PASS: signal matches evidence | BLOCK: fabricated signal | HIGH |
| Missing signal detection | FLAG: signal absent | PASS: missing signal not flagged | HIGH |
| Professional judgment | FLAG: unprofessional recommendation | PASS: properly hedged | MEDIUM |

---

## 2. Framework Decision

**Selected Framework:** DefaultLLMExpertAgent (Direct OpenAI/Anthropic API)

**Version:** N/A — API-based

**Rationale:**
D-01 from Phase 26: "Direct OpenAI/Anthropic API call, not 4-platform adapter architecture." Single adapter with env-var provider selection. Platform adapters (openclaw, hermes, claude_code, codex) deferred to future phase.

**Alternatives Considered:**

| Framework | Ruled Out Because |
|-----------|------------------|
| 4-platform adapter (AA-01-PLAN.md) | Deferred — D-04 in Phase 26 explicitly defers this |
| Platform-specific SDKs | Not needed for direct API access |

---

## Actual Runtime Path: Why LLM Mode Never Executed

> **CRITICAL GAP (E-26-01):** The DefaultLLMExpertAgent code exists and is functional, but it is NEVER INVOKED because expert-cards.yaml configs do not provide the activation signal.

### Activation Chain (Why LLM is Dead Code)

```
1. Scene loads expert-cards.yaml
   No `prompt_file` field present
2. ExpertCardConfig.prompt_file = None (default)
   expert_analysis_helper.py line ~50
3. run_input_audit() checks: if input_card.prompt_file:
   Condition is FALSE (prompt_file is None)
   LLM branch skipped entirely
4. Falls through to _keyword_audit()
   Only keyword matching executes
5. DefaultLLMExpertAgent is never instantiated
   LLM code path is unreachable
```

### Current State of Scene YAMLs

| Scene | Has prompt_file? | Has agent_name? | Has orchestration? | LLM Mode? |
|-------|-----------------|----------------|-------------------|-----------|
| post-meeting-synthesis | NO | NO | NO | NEVER ACTIVE |
| customer-recent-status | NO | NO | NO | NEVER ACTIVE |

### To Enable LLM Mode

Each expert card in scene expert-cards.yaml needs:

```yaml
- expert_name: sales-account-strategist
  review_type: input
  check_signals: [expansion_plan, timeline, risk_factors]
  output_field: account_review
  block_on_flags: true
  agent_name: sales-account-strategist      # ADD THIS
  prompt_file: sales-account-strategist.md  # ADD THIS
  orchestration: sequential                  # ADD THIS (sequential or council)
```

### Evidence Table

| Source File | Actual Behavior | Design Reference | Severity | Reproducibility |
|-------------|-----------------|------------------|----------|-----------------|
| `scenes/post-meeting-synthesis/expert-cards.yaml` | No prompt_file/agent_name/orchestration | Phase 26 D-02: "prompt_file activates LLM mode" | CRITICAL | `grep prompt_file scenes/post-meeting-synthesis/expert-cards.yaml` returns nothing |
| `scenes/customer-recent-status/expert-cards.yaml` | No prompt_file/agent_name/orchestration | Phase 26 D-02: "prompt_file activates LLM mode" | CRITICAL | `grep prompt_file scenes/customer-recent-status/expert-cards.yaml` returns nothing |
| `runtime/expert_analysis_helper.py` | `if input_card.prompt_file:` always False | Phase 26 D-02 design intent | CRITICAL | Line ~50: condition never true in production |

---

## 4. Implementation Guidance

**Entry Point Pattern:**
```python
# expert_analysis_helper.py — run_input_audit() / run_output_audit()
if input_card.prompt_file:
    # LLM mode (NEVER REACHED — prompt_file not set in any scene YAML)
    prompt = build_input_review_prompt(input_card, container)
    result = asyncio.run(invoke_llm_expert(input_card, prompt))
else:
    # Keyword mode (fallback) — ALWAYS executes
    result = _keyword_audit(...)
```

**Key Abstractions:**

| Concept | What It Is | When You Use It |
|---------|-----------|-----------------|
| ExpertCardConfig | Dataclass with expert review config including prompt_file | When loading scene expert-cards.yaml |
| DefaultLLMExpertAgent | LLM adapter with OpenAI/Anthropic support | When invoking LLM-based review (UNREACHABLE) |
| build_input_review_prompt | Template renderer replacing {evidence}, {check_signals} | Before LLM invocation |
| _check_hallucination | Signal-vs-check_signals validation | After LLM response parsing |

---

## 4b. AI Systems Best Practices

**Structured Outputs:**
- Expected format: line-by-line with `PASS:`, `FLAG:`, `BLOCK:` prefixes
- No JSON — relies on LLM following format instructions in prompt template
- Risk: format deviations cause parse failure to fallback to keyword mode

**Prompt Engineering:**
- Agency-agents prompt files are used as base templates
- Runtime adds evidence via {evidence} placeholder
- Runtime adds check_signals via {check_signals} placeholder
- No few-shot examples — relies on prompt instructions only

**Hallucination Guardrail (PRODUCTION BUG — E-26-02):**
```python
# runtime/default_llm_adapter.py line ~306
def _check_hallucination(self, findings: list[str], check_signals: list[str]) -> None:
    if not check_signals:  # THIS GUARD IS MISSING
        raise ValueError("check_signals cannot be empty")  # Raised when called with []
```

**Impact:** Production scenes calling expert review with empty check_signals will raise ValueError instead of gracefully handling the empty case.

**Fix Recommendation (Immediate):**
```python
def _check_hallucination(self, findings: list[str], check_signals: list[str]) -> None:
    if not check_signals:
        return  # No signals to check — nothing to hallucinate
    # ... existing validation
```

**Cost Budget:**
- OpenAI gpt-4o: ~$0.01-0.02 per review call (1,024 max tokens)
- Anthropic claude-sonnet: ~$0.003-0.008 per review call (1,024 max tokens)
- No caching implemented — each review is a fresh call

---

## 5. Evaluation Strategy

### Dimensions

| Dimension | Rubric | Measurement | Priority |
|-----------|--------|-------------|----------|
| Signal accuracy | PASS only for evidence-matched signals | Eval cases 101-115 | Critical |
| Fallback reliability | LLM failure keyword mode, no hang | Manual error injection | High |
| Parse robustness | Malformed response fallback | Eval runner | Medium |
| API key safety | No key in logs/errors | Code review | High |

### Eval Tooling

**Primary Tool:** `evals/runner.py`

**Reference Dataset:** 15 labeled cases in `evals/evals.json` (ids 101-115)

**CI Integration:** Partial — 3 cases run (101, 106, 111); all 15 should run

---

## 6. Guardrails

### Online (Real-Time)

| Guardrail | Trigger | Intervention |
|-----------|---------|--------------|
| Hallucination check | Signal not in check_signals | BLOCK: blocked=True, block_reason (BUG: raises ValueError on empty check_signals) |
| API key startup check | Missing env var | EnvironmentError at import |
| LLM error classification | Timeout/auth/rate limit/parse/empty | Fall back to keyword mode |
| Prompt file existence | FileNotFoundError | Fail-open, skip LLM mode |

### Offline (Flywheel)

| Metric | Sampling | Action |
|--------|----------|--------|
| Fallback rate | All LLM failures | Alert if >10% |
| Parse failure rate | Malformed responses | Alert if >5% |

---

## 7. Production Monitoring

**Tracing Tool:** None

**Key Metrics:**
- LLM invocation count per scene
- Fallback count (keyword mode activations)
- Block rate (hallucination detections)

**Implementation Status:** PARTIAL — metrics logged at DEBUG level, no centralized collection

---

## Security & Compliance

**Prompt Injection:**
- Risk: Malicious prompt_file path traversal or attacker-controlled prompt file
- Mitigation: prompt_file existence check before use (FileNotFoundError -> fail-open)
- Status: PARTIAL — no path traversal validation

**Sensitive Data Handling:**
- Evidence data (customer meetings) sent to LLM API
- No data retention controls documented
- Status: Unmitigated — user must trust LLM provider

**Log Sanitization:**
- Finding signals logged at DEBUG level
- No redaction of customer PII from logs
- Status: Unmitigated

**Failure Degradation:**
- LLM failure -> keyword mode (D-06)
- No max-fallback-count limit (E-26-03)
- Risk: infinite fallback loop if keyword mode also fails
- Status: MEDIUM risk — CircuitBreaker tracks failures but no fallback count

---

## Checklist

- [x] System type classified (Conversational / Extraction)
- [x] Critical failure modes identified (5 modes)
- [x] Actual runtime path documented (why LLM is dead code)
- [x] Evidence table with 3 gap entries (E-26-01)
- [x] Hallucination guardrail production bug documented (E-26-02)
- [x] Fix recommendation provided for production bug
- [x] Framework decision documented (Direct API)
- [x] Implementation guidance (entry point pattern)
- [x] AI systems best practices
- [x] Evaluation dimensions defined (4 dimensions)
- [x] Guardrails defined (online + offline)
- [x] Production monitoring (PARTIAL)
- [x] Security & compliance (4 areas, 3 unmitigated)
