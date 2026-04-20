# AI-SPEC.md — Phase 24 Supplement: Agency-Agents Integration Design

> **Note:** Retrospective AI-SPEC supplement. Phase 24 produced AA-01-PLAN.md
> (1,359 lines) but did not go through `gsd-ai-integration-phase`. This document
> captures the AI design decisions that should have been locked.

**Phase:** 24 — Agency-Agents Integration Design
**System Type:** Multi-Agent Orchestration (Simplified to Direct LLM in Phase 26)
**Generated:** 2026-04-21 (retrospective)
**Addresses:** E-24-01, E-24-02, E-24-03, E-24-04 from 30-GAP-REPORT.md

---

## 1. System Classification

**System Type:** Multi-Agent / Conversational — Expert Review

**Description:**
Four expert agents (sales-account-strategist, customer-service, sales-proposal-strategist, sales-data-extraction-agent) provide structured review of sales meeting inputs and outputs. Agents are invoked via scene runtime with sequential or council-style orchestration.

**Intended Architecture (AA-01-PLAN.md):**
- 4-platform adapter architecture: openclaw, hermes, claude_code, codex
- agents/platform-adapters/ directory with per-platform adapters
- ExpertAgent ABC with platform-specific implementations
- Council-style multi-expert orchestration with context slicing

**Actual Implementation (Phase 26 simplification):**
- Single DefaultLLMExpertAgent using OpenAI/Anthropic API via LLM_PROVIDER env var
- No platform-adapters/ directory
- ExpertAgent ABC exists but only one implementation
- Council orchestration never implemented

**Critical Failure Modes:**
1. Hallucinated signals in expert review findings (fabricated evidence references)
2. Invalid agent name injection via expert-cards.yaml (security boundary violation)
3. Cascade failure when LLM API is unavailable (no circuit breaker in Phase 24 design)
4. Context window inflation in council mode (unbounded evidence passing)
5. Migration failure: keyword-to-AI transition causes inconsistent behavior

---

## 1b. Domain Context

**Industry Vertical:** B2B SaaS customer success management

**User Population:** Sales representatives and customer success managers using Feishu (Lark) workbench

**Stakes Level:** Medium — Expert review informs customer strategy but final decisions remain human-controlled

**Output Consequence:** Expert findings feed into SceneResult.payload and determine write ceiling (normal vs. recommendation-only)

### What Domain Experts Evaluate Against

| Dimension | Good | Bad | Stakes | Source |
|-----------|------|-----|--------|--------|
| Signal accuracy | Finding references only evidence-provided signals | Fabricated signals not in check_signals | HIGH — incorrect blocks | Phase 27 eval cases 111-115 |
| Review completeness | All check_signals addressed | Missing signals not flagged | MEDIUM — incomplete audits | Phase 27 eval cases 106-110 |
| Fallback reliability | Graceful degradation to keyword mode | Silent failures or blocking | HIGH — availability | Phase 26 D-06 |

---

## 2. Framework Decision

**Selected Framework:** Direct OpenAI/Anthropic API (simplified from AA-01-PLAN.md 4-platform design)

**Version:** N/A — API-based, not library-based

**Rationale:**
Phase 26 D-01 chose Direct API over 4-platform adapter architecture. Rationale: "Simpler for single-user skill, supports multi-platform subagent creation via compatible interface." This was a deliberate tradeoff documented in Phase 26 CONTEXT.md.

**Alternatives Considered:**

| Framework | Ruled Out Because |
|-----------|------------------|
| 4-platform adapters (AA-01-PLAN.md design) | Deferred — premature complexity for Phase 26 |
| LangChain/LlamaIndex agent frameworks | Overkill for single-user skill; not needed |
| CrewAI / autogen | Not evaluated at Phase 24/26 time |

**Vendor Lock-In Accepted:** Partial — LLM_PROVIDER env var allows OpenAI to Anthropic switch, but both are OpenAI-compatible APIs.

**Root Cause of Deviation:**
Phase 26 explicitly chose Direct API over AA-01-PLAN.md's 4-platform adapter. The gap between design (AA-01-PLAN.md) and implementation (DefaultLLMExpertAgent) is a documented decision, not an oversight.

---

## 4. Implementation Guidance

**Model Configuration:**
- OpenAI: `gpt-4o`, temperature 0.3, max tokens 1024
- Anthropic: `claude-sonnet-4-20250514`, max tokens 1024
- Provider selection via `LLM_PROVIDER` env var (default: openai)

**Core Pattern:**
- Prompt template from `agents/{prompt_file}.md` + placeholder replacement
- Placeholders: `{evidence}`, `{check_signals}`, `{recommendations}`, `{expert_name}`
- Response parsing: line-by-line PASS/FLAG/BLOCK format

---

## 4b. AI Systems Best Practices

**Structured Outputs:**
- Expected format: line-by-line with `PASS:`, `FLAG:`, `BLOCK:` prefixes
- No JSON — relies on LLM following format instructions in prompt template
- Risk: format deviations cause parse failure to fallback to keyword mode

**Hallucination Guardrail:**
- Implemented in `default_llm_adapter._check_hallucination()`
- Validates finding signals against check_signals list
- Case-insensitive comparison
- WARNING: Production with empty check_signals raises ValueError (see E-26-02)

**Async-First:**
- All LLM invocations are async via `asyncio.wait_for()` with configurable timeout
- Default 30s for API call, 120s per agent in batch

---

## 5. Evaluation Strategy

### Dimensions

| Dimension | Rubric | Measurement | Priority |
|-----------|--------|-------------|----------|
| Signal accuracy | All PASS/FLAG/BLOCK references match check_signals | Eval cases 111-115 (fabricated signals) | Critical |
| Missing signal detection | All absent signals flagged | Eval cases 106-110 (missing signals) | High |
| Normal case accuracy | Clean evidence all PASS | Eval cases 101-105 | High |
| Fallback reliability | LLM failure keyword mode, no hang | Manual testing + error injection | Medium |

### Eval Tooling

**Primary Tool:** `evals/runner.py` — pattern-based assertion runner

**Reference Dataset:** 15 labeled cases in `evals/evals.json` (ids 101-115)

**CI Integration:** Partial — only 3 of 15 expert-review eval cases run in CI (ids 101, 106, 111)

---

## 6. Guardrails

### Online (Real-Time)

| Guardrail | Trigger | Intervention |
|-----------|---------|--------------|
| Hallucination detection | Finding signal not in check_signals | BLOCK: set blocked=True, block_reason=fabricated_signal |
| API key validation | Missing OPENAI_API_KEY or ANTHROPIC_API_KEY | EnvironmentError at startup |
| LLM failure | Any LLMError (timeout, auth, rate limit, parse) | Fall back to keyword mode |

### Offline (Flywheel)

| Metric | Sampling | Action |
|--------|----------|--------|
| False positive rate (fabricated signals) | All eval case 111-115 runs | Alert if >0% |
| False negative rate (missing signals) | All eval case 106-110 runs | Alert if >20% |

---

## 7. Production Monitoring

**Tracing Tool:** None — no observability tooling integrated

**Key Metrics:**
- LLM invocation latency (P50, P95): logged via `logger.debug()` in default_llm_adapter.py
- Fallback rate (keyword mode activations): logged on LLM failure
- Block rate (hallucination detections): logged on fabricated signal detection

**Implementation Status:** PARTIAL — metrics logged at DEBUG level, no centralized collection

---

## Security & Compliance

**Prompt Injection:**
- Risk: Malicious actor crafts expert-cards.yaml with prompt_file pointing to attacker-controlled prompt
- Mitigation: prompt_file validated against allowlist in expert_card_loader.py
- Status: No allowlist implemented — HIGH risk (see E-24-03)

**Sensitive Data Handling:**
- Expert review receives customer meeting data (evidence)
- LLM API call sends evidence to OpenAI/Anthropic
- No data retention policy documented for LLM provider
- Status: Unmitigated — user must trust LLM provider data policy

**Log Sanitization:**
- Finding signals logged at DEBUG level for debugging
- No redaction of customer-specific content from logs
- Status: Unmitigated — logs may contain PII

**Failure Degradation:**
- LLM failure → fallback to keyword mode (see D-06)
- No max-fallback-count limit — potential infinite loop
- Status: MEDIUM risk (see E-26-03)

---

## Checklist

- [x] System type classified (Multi-Agent / Expert Review)
- [x] Critical failure modes identified (5 modes)
- [x] Domain context researched (B2B SaaS customer success)
- [x] Framework decision documented (Direct API, simplified from 4-platform)
- [x] Intended vs actual architecture documented
- [x] Implementation guidance captured (prompt template pattern)
- [x] AI systems best practices (hallucination guardrail, async, fallback)
- [x] Evaluation dimensions defined (4 dimensions)
- [x] Guardrails defined (online + offline)
- [x] Production monitoring section present (PARTIAL — metrics logged, not collected)
- [x] Security & compliance section (4 areas, 3 unmitigated)
