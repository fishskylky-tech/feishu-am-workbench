# Phase 17: Post-Meeting And Todo Expert Upgrade - Research

**Researched:** 2026-04-17
**Domain:** Post-meeting synthesis and Todo follow-on with customer-operating judgments
**Confidence:** HIGH

## Summary

Phase 17 upgrades the post-meeting synthesis and Todo follow-on from generic summaries into customer-operating judgments with typed action recommendations. It delivers three requirements: CORE-02 (structured post-meeting sections), TODO-01 (intent classification for Todo candidates), and TODO-02 (expert rationale preceding each candidate). The existing SceneResult contract is preserved unchanged; the phase adds new structured fields to the output artifact and to the WriteExecutionCandidate payload. Todo writes continue routing through the existing unified writer path. ExpertAnalysisHelper remains a thin assembly helper per the Phase 16 boundary.

**Primary recommendation:** Add structured output sections to `build_meeting_output_artifact` for CORE-02; extend `WriteExecutionCandidate` with intent classification and rationale fields for TODO-01/02; update evals.json assertions to verify the new output format.

---

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Output uses structured list format (2-5 bullet points per section)
- **D-02:** Four fixed sections required: 风险 (risks), 机会 (opportunities), 干系人变化 (stakeholder changes), 下一轮推进路径 (next-round advancement path)
- **D-03:** Each section contains named, scannable items rather than dense narrative paragraphs
- **D-04:** "下一轮推进" section may use short sentences rather than bullet lists
- **D-05:** Four fixed intent categories: 风险干预, 扩张推进, 关系维护, 项目进展
- **D-08:** Classification is stored in a structured field, not just human-readable text
- **D-09/D-10:** Expert rationale stored in a structured field with Chinese naming (e.g., 判定理由)
- **D-12:** Todo writes still route through the existing unified writer path
- **D-13:** ExpertAnalysisHelper does assembly/combination only; specific judgment decisions remain at the scene layer
- **D-14:** SceneResult contract unchanged from Phase 12/16

### Claude's Discretion

- Exact bullet count per section (within 2-5 range)
- Exact internal field name for intent classification, as long as structured and traceable
- Exact format of the structured rationale field (paragraph vs. list vs. key-value pairs)
- How to handle cases where a Todo spans multiple intent categories

### Deferred Ideas

- None

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CORE-02 | Post-meeting output with fixed sections for risks, opportunities, stakeholder changes, and next-round advancement path | `build_meeting_output_artifact` needs four new structured sections; evals.json needs updated assertions to verify section presence |
| TODO-01 | Follow-on Todo recommendations classified by intent (风险干预, 扩张推进, 关系维护, 项目进展) | `WriteExecutionCandidate` payload needs structured 意图/intent field; `build_meeting_todo_candidates` needs classification logic |
| TODO-02 | Expert rationale precedes each Todo candidate before write-back | Candidate payload needs structured 判定理由/rationale field; rationale displayed before candidate in output |

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Post-meeting structured sections (CORE-02) | API/Backend | Browser/Client | Scene layer produces structured output; `build_meeting_output_artifact` assembles the artifact |
| Intent classification (TODO-01) | API/Backend | — | Scene layer decides classification; result stored in `WriteExecutionCandidate` payload |
| Expert rationale (TODO-02) | API/Backend | — | Rationale generated at scene layer; stored in candidate payload for downstream traceability |
| Todo write execution | API/Backend | — | `TodoWriter` handles actual writes; unchanged in Phase 17 |
| Eval assertions | Testing/Verification | — | `evals/runner.py` pattern-matching validates output format |

---

## Standard Stack

### Core (No Changes from Phase 16)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python 3.13 | 3.13 | Runtime | Project baseline |
| pytest | 8.x | Unit/integration testing | Project test framework |
| ExpertAnalysisHelper | (existing) | Evidence assembly | Phase 16 foundation, unchanged |
| TodoWriter | (existing) | Todo write execution | Unified writer path, unchanged |
| SceneResult | (existing) | Scene output contract | Frozen from Phase 12/16 |

### Supporting (No New Dependencies)
| Library | Version | Purpose |
|---------|---------|---------|
| evals/runner.py | (existing) | Pattern-matching assertion evaluation |
| evals/evals.json | (existing) | Eval case definitions |

**Installation:** No new packages required.

---

## Architecture Patterns

### System Architecture Diagram

```
Scene Request (post-meeting / todo-follow-on)
        │
        ▼
Scene Runtime (run_post_meeting_scene / run_todo_capture_and_update_scene)
        │
        ▼
Gateway + QueryBackend → recover_live_context()
        │
        ├──► EvidenceContainer (ExpertAnalysisHelper.assemble())
        │
        ├──► build_meeting_output_artifact() ──► [NEW: Four structured sections]
        │          │
        │          └──► output_text with 风险/机会/干系人变化/下一轮推进
        │
        └──► build_meeting_todo_candidates() ──► [NEW: intent + rationale fields]
                   │
                   ▼
            WriteExecutionCandidate (with 意图, 判定理由 in payload)
                   │
                   ▼
            run_confirmed_todo_write() → TodoWriter
```

### Recommended Project Structure
```
evals/
├── meeting_output_bridge.py   # Add four sections to artifact output
├── runner.py                  # (unchanged)
├── evals.json                 # Update assertions for CORE-02/TODO-01/TODO-02

runtime/
├── scene_runtime.py           # WriteExecutionCandidate with intent/rationale
├── expert_analysis_helper.py  # (unchanged - thin assembly only)
├── models.py                  # (add structured fields if needed)
└── todo_writer.py             # (unchanged - unified writer)

tests/
├── test_meeting_output_bridge.py  # Update for new sections and candidate fields
├── test_scene_runtime.py          # Verify new candidate payload shape
└── fixtures/
    └── transcripts/               # (existing test fixtures)
```

### Pattern 1: Structured Section Output (CORE-02)
**What:** Post-meeting output now contains four named, scannable sections with 2-5 bullet points each.
**When to use:** After `recover_live_context()` returns, before building the final artifact.
**Example:**
```python
# In build_meeting_output_artifact(), add structured sections:
if evidence_container is not None:
    sections = _extract_structured_sections(evidence_container, transcript_text)
    lines.append("风险:")
    for item in sections["risks"]:
        lines.append(f"- {item}")
    lines.append("机会:")
    for item in sections["opportunities"]:
        lines.append(f"- {item}")
    lines.append("干系人变化:")
    for item in sections["stakeholder_changes"]:
        lines.append(f"- {item}")
    lines.append("下一轮推进路径:")
    for item in sections["next_round"]:
        lines.append(f"- {item}")
```

### Pattern 2: Intent-Classified Todo Candidate (TODO-01)
**What:** Each WriteExecutionCandidate carries a structured intent field and rationale.
**When to use:** When building Todo candidates from meeting action items or follow-on items.
**Example:**
```python
# In build_meeting_todo_candidates() or _build_action_item_candidates():
candidate.payload["意图"] = _classify_intent(action_item, evidence_container)
candidate.payload["判定理由"] = _generate_rationale(action_item, evidence_container)
```
**Structured field names:** `意图` (intent category), `判定理由` (expert rationale, Chinese)

### Pattern 3: Rationale Preceding Candidate Display (TODO-02)
**What:** Expert rationale is visible before the Todo candidate is proposed for write-back.
**When to use:** When rendering the candidate list for user confirmation.
**Example:**
```python
# In scene result payload serialization:
for candidate in candidates:
    rationale = candidate.payload.get("判定理由", "")
    intent = candidate.payload.get("意图", "")
    print(f"[{intent}] {candidate.payload['summary']}")
    print(f"  判定理由: {rationale}")
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Evidence assembly | Custom source combination logic | ExpertAnalysisHelper.assemble() | Already handles quality ratings, missing-source tracking, write ceiling, and fallback reason |
| Todo write execution | Direct Feishu API calls | TodoWriter + run_confirmed_todo_write() | Unified writer path handles dedupe, preflight, guard, and safety semantics |
| Output format validation | ad-hoc string matching | evals/runner.py evaluate_case() | Pattern-based assertions already defined in evals.json |

**Key insight:** The Phase 16 boundary (ExpertAnalysisHelper = thin assembly) is preserved. Phase 17 adds judgment logic at the scene layer, not in the helper. The helper's `combine_evidence_texts()` and `detect_conflicts()` are available for scene-layer code to use, but scene code decides what evidence means.

---

## Common Pitfalls

### Pitfall 1: Embedding rationale in free-form text instead of structured field
**What goes wrong:** Rationale is readable but not traceable by downstream systems.
**Why it happens:** Storing rationale as a string in `description` is easier than a separate field, but breaks TODO-02's requirement for structured storage.
**How to avoid:** Always store rationale in a dedicated field (e.g., `判定理由`) alongside `意图`. The display layer can concatenate them; the storage layer keeps them separate.
**Warning signs:** Rationale appears only in `description` or `output_text`, not in candidate `payload`.

### Pitfall 2: Modifying SceneResult contract
**What goes wrong:** Adding new top-level fields to SceneResult violates D-14 and breaks scene compatibility.
**Why it happens:** It feels natural to add `risks`, `opportunities`, etc. as top-level SceneResult fields.
**How to avoid:** All new structured data goes into `payload["scene_payload"]` or the candidate's `payload` dict. SceneResult top-level fields (facts, judgments, recommendations, etc.) are frozen.
**Warning signs:** `SceneResult` dataclass is being modified; `STANDARD_SCENE_RESULT_FIELDS` is being updated.

### Pitfall 3: Hardcoding four-section content instead of deriving from evidence
**What goes wrong:** Post-meeting sections are written as static text rather than derived from `EvidenceContainer` and transcript analysis.
**Why it happens:** Copying example bullets is faster than building analysis logic.
**How to avoid:** Scene-layer code should use `evidence_container` sources and `transcript_text` to generate section content. The four-section structure is the format contract; content is derived.
**Warning signs:** Section content does not vary based on which sources are available.

### Pitfall 4: Changing Todo write path instead of extending candidate shape
**What goes wrong:** Creating a parallel write path for "expert" todos instead of using the unified writer.
**Why it happens:** The unified writer is perceived as too restrictive for expert-grade todos.
**How to avoid:** Expert quality is expressed through intent classification and rationale in the candidate payload, not through a different write path. Confirmed writes always go through `run_confirmed_todo_write()`.

---

## Code Examples

### Extending build_meeting_output_artifact for CORE-02
```python
# In evals/meeting_output_bridge.py
def build_meeting_output_artifact(..., evidence_container: EvidenceContainer | None = None) -> dict[str, Any]:
    # ... existing header, sources, key_context, missing_sources ...

    # NEW: Add four structured sections before case-specific body
    if evidence_container is not None and transcript_text:
        sections = _derive_structured_sections(
            evidence_container,
            transcript_text,
            gateway_result,
        )
        lines.append("风险:")
        for item in sections.get("risks", [])[:5]:
            lines.append(f"- {item}")
        lines.append("机会:")
        for item in sections.get("opportunities", [])[:5]:
            lines.append(f"- {item}")
        lines.append("干系人变化:")
        for item in sections.get("stakeholder_changes", [])[:5]:
            lines.append(f"- {item}")
        lines.append("下一轮推进路径:")
        for item in sections.get("next_round", [])[:5]:
            lines.append(f"- {item}")

    lines.extend(_render_case_body(eval_name, transcript_text))
```

### Extending build_meeting_todo_candidates for TODO-01/02
```python
# In evals/meeting_output_bridge.py
def _build_action_item_candidates(...) -> list[WriteCandidate]:
    # ... existing candidate building ...
    intent = _classify_action_intent(item, evidence_container)
    rationale = _generate_action_rationale(item, evidence_container)
    payload["意图"] = intent
    payload["判定理由"] = rationale
    # ... rest of candidate creation ...
```

### Intent classification (TODO-01)
```python
# In evals/meeting_output_bridge.py or scene_runtime.py
TWO_MONTHS_INTENTS = frozenset({"风险干预", "扩张推进", "关系维护", "项目进展"})

def _classify_action_intent(item: dict[str, object], evidence_container: EvidenceContainer) -> str:
    summary = str(item.get("summary") or "")
    theme = str(item.get("theme") or "").lower()

    if any(kw in summary for kw in ["风险", "预警", "下降", "流失", "竞品"]):
        return "风险干预"
    if any(kw in summary for kw in ["扩张", "增加", "扩容", "新客", "开拓"]):
        return "扩张推进"
    if any(kw in summary for kw in ["关系", "维护", "拜访", "沟通", "维护"]):
        return "关系维护"
    return "项目进展"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Generic meeting summary output | Four fixed customer-operating sections | Phase 17 (CORE-02) | AM gets scannable risks/opportunities/stakeholder changes/next-round path |
| Todo candidates with only summary/owner/due_at | Todo candidates with 意图 (intent) and 判定理由 (rationale) | Phase 17 (TODO-01/02) | Each action is classified and explained before write-back |
| Rationale as free-form description text | Rationale as structured field (判定理由) | Phase 17 (TODO-02) | Downstream traceability, not just human readability |

**Deprecated/outdated:**
- None — Phase 17 builds on existing infrastructure, does not deprecate prior behavior

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | SceneResult contract (STANDARD_SCENE_RESULT_FIELDS) remains frozen in Phase 17 | D-14 | Planner would create tasks that modify SceneResult instead of using payload |
| A2 | ExpertAnalysisHelper remains thin (assembly only, no judgment) | D-13 | Planner would add judgment logic to the helper instead of scene layer |
| A3 | Four fixed sections derive from evidence, not hardcoded | CORE-02 | Tests would pass but output would be template text, not derived analysis |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

---

## Open Questions

1. **How is `_derive_structured_sections()` implemented?**
   - What we know: It takes `evidence_container`, `transcript_text`, and `gateway_result` as inputs; outputs a dict with keys `risks`, `opportunities`, `stakeholder_changes`, `next_round`; each value is a list of 0-5 strings.
   - What's unclear: Whether this is a new function in `meeting_output_bridge.py` or part of the scene layer; whether it uses keyword extraction, LLM inference, or pattern matching against evidence.
   - Recommendation: Scene layer decides. The `meeting_output_bridge.py` provides the output artifact formatting; the content generation is at scene layer per D-13.

2. **How is `_classify_action_intent()` implemented?**
   - What we know: Four intent categories are fixed; classification may be rule-based (keywords) or inferred.
   - What's unclear: Whether this uses keyword matching against action item text, or inference from evidence context.
   - Recommendation: Keyword-based rule classification is sufficient for v1.2. LLM inference can be added later as an enhancement.

3. **Does evals.json need new eval cases or updated assertions for existing cases?**
   - What we know: Existing evals check for live-first gate; CORE-02 requires four named sections to appear in output.
   - What's unclear: Whether new assertion patterns (e.g., `contains_all: ["风险:", "机会:", "干系人变化:", "下一轮推进路径:"]`) are sufficient, or new eval cases are needed.
   - Recommendation: Update existing eval case assertions to include the four section headers as required patterns.

---

## Environment Availability

> Step 2.6: SKIPPED (no external dependencies identified beyond those already present in the project).

Phase 17 is entirely a code extension of existing infrastructure:
- No new Python packages required
- No new external services required
- No new CLI tools required
- Existing test infrastructure (pytest, evals/runner.py) covers all Phase 17 requirements

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | pytest.ini (if present) or pyproject.toml |
| Quick run command | `pytest tests/test_meeting_output_bridge.py tests/test_scene_runtime.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| CORE-02 | Post-meeting output contains four fixed sections with 2-5 bullets each | unit | `pytest tests/test_meeting_output_bridge.py -k test_core02` | needs new |
| CORE-02 | Section content varies based on available evidence | unit | `pytest tests/test_meeting_output_bridge.py -k test_evidence_driven_sections` | needs new |
| TODO-01 | WriteExecutionCandidate payload contains 意图 field | unit | `pytest tests/test_scene_runtime.py -k test_intent_classification` | needs new |
| TODO-01 | Intent classification is one of four fixed values | unit | `pytest tests/test_meeting_output_bridge.py -k test_intent_values` | needs new |
| TODO-02 | Candidate payload contains 判定理由 field | unit | `pytest tests/test_scene_runtime.py -k test_rationale_field` | needs new |
| TODO-02 | Rationale displayed before candidate in output | integration | `pytest tests/test_meeting_output_bridge.py -k test_rationale_precedes_candidate` | needs new |
| CORE-02 | Evals pass with new section format | eval | `pytest tests/test_meeting_output_bridge.py -k test_unilever_bridge_output_passes_eval` | existing, needs update |

### Sampling Rate
- **Per task commit:** `pytest tests/test_meeting_output_bridge.py tests/test_scene_runtime.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_meeting_output_bridge.py` — add tests for CORE-02 four-section output format
- [ ] `tests/test_scene_runtime.py` — add tests for TODO-01 intent classification and TODO-02 rationale field in WriteExecutionCandidate payload
- [ ] `evals/evals.json` — update existing eval case assertions to include four-section headers as required patterns
- [ ] `tests/conftest.py` — add fixtures for EvidenceContainer with typed content for section derivation tests

---

## Security Domain

> Security enforcement is implicitly enabled. Phase 17 operates within the existing scene runtime and does not introduce new attack surfaces.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V4 Access Control | no | N/A — Phase 17 is read/analysis phase |
| V5 Input Validation | yes | All action item fields (summary, theme, due_at, owner) already validated through existing schema preflight before candidate creation |
| V8 Data Protection | yes | Structured fields (意图, 判定理由) stored in candidate payload; no new secrets or credentials introduced |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious action item fields (XSS in summary) | Tampering | Existing field validation in `build_meeting_todo_candidates`; output rendered as plain text |
| Intent field injection | Tampering | Intent values constrained to four fixed values (enum validation) |
| Rationale field injection | Tampering | Rationale generated from evidence, not user-provided; existing evidence container guards |

---

## Sources

### Primary (HIGH confidence)
- `runtime/expert_analysis_helper.py` — ExpertAnalysisHelper assembly contract, D-04/D-05 boundary (read directly)
- `runtime/scene_runtime.py` — SceneResult contract (STANDARD_SCENE_RESULT_FIELDS), run_post_meeting_scene(), WriteExecutionCandidate (read directly)
- `evals/meeting_output_bridge.py` — build_meeting_output_artifact(), build_meeting_todo_candidates() — current implementation to extend (read directly)
- `17-CONTEXT.md` — all D-0X decisions, phase boundary, implementation constraints (read directly)

### Secondary (MEDIUM confidence)
- `evals/runner.py` — evaluate_case() pattern-matching framework, assertion types (read directly)
- `tests/test_meeting_output_bridge.py` — existing test patterns for post-meeting output (read directly)
- `tests/test_scene_runtime.py` — existing test patterns for scene runtime (read directly)
- `evals/evals.json` — existing eval case definitions (implicit — patterns defined in tests)

### Tertiary (LOW confidence)
- None — all primary sources were read directly from the codebase

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies introduced; all patterns from existing codebase
- Architecture: HIGH — existing scene runtime pattern preserved; no contract changes
- Pitfalls: HIGH — all pitfalls derived from D-0X decisions and existing code patterns

**Research date:** 2026-04-17
**Valid until:** 2026-05-17 (30 days — phase domain is stable)
