# Phase 18: Account Posture And Cohort Scanning - Research

**Researched:** 2026-04-17
**Domain:** Customer account-posture analysis (single-customer four-lens) and cohort scanning (multi-customer dynamic-query)
**Confidence:** HIGH (implementation decisions locked in 18-CONTEXT.md; code patterns verified)

## Summary

Phase 18 upgrades the single-customer recent-status scene with four-lens output (STAT-01) and introduces a new cohort scan scene with dynamic condition query (SCAN-01). Both build on the Phase 16 `EvidenceContainer` and `ExpertAnalysisHelper` foundation without modifying the `SceneResult` contract. The STAT-01 upgrade modifies `run_customer_recent_status_scene()` to produce labeled lens sub-items in the `judgments` field; SCAN-01 adds `run_cohort_scan_scene()` which iterates over a cohort of customers (fetched via existing `LarkCliCustomerBackend._list_records()` path), runs per-customer four-lens analysis, then aggregates cohort-level signals and recommendations.

**Primary recommendation:** STAT-01 mirrors the Phase 17 four-section output pattern but uses a parallel lens framing (risk/opportunity/relationship/project-progress); SCAN-01 reuses the same per-customer analysis path and adds an aggregation layer on top.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Four-lens output (risk/机会, opportunity/机会, relationship/关系, project-progress/进展) as labeled sub-items within judgments
- **D-02:** STAT-01 implemented as an upgrade to existing `customer-recent-status` scene — not a new standalone scene
- **D-03:** Cohort defined via dynamic condition query (natural language interpreted into filter criteria)
- **D-04:** Cohort scan limit default 10; if exceeded, prompt user to narrow
- **D-05:** Cohort output uses "aggregated summary + key customers" structure
- **D-06:** Individual entries in cohort context follow same four-lens framing
- **D-07:** Two-tier recommendations (cohort-level 1-3 items + per-customer 1-2 items)
- **D-08:** Total recommendation cap ~10 for actionability
- **D-09:** ExpertAnalysisHelper stays thin — assembly/combination only
- **D-10:** EvidenceContainer tracks source evidence per lens
- **D-11:** SceneResult contract unchanged
- **D-12:** Cohort scanning is user-triggered analytical entry, NOT scheduled

### Deferred Ideas (OUT OF SCOPE)
- SCAN-02 (scheduled/semi-automatic customer scanning) — future requirement, not in scope for Phase 18

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STAT-01 | Single-customer recent-status uses fixed four lenses (risk, opportunity, relationship, project-progress) | Four-lens output pattern derived from Phase 17 `_derive_structured_sections()`; EvidenceContainer extends for lens-aware source tracking |
| SCAN-01 | User can request a class of customers and receive grouped signals, common issues, and suggested actions | New scene function `run_cohort_scan_scene()`; dynamic condition query via existing `LarkCliCustomerBackend`; aggregation layer on top of per-customer four-lens analysis |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Four-lens STAT-01 output | API / Backend | — | `run_customer_recent_status_scene()` in scene_runtime.py assembles lenses from EvidenceContainer |
| SCAN-01 cohort scene | API / Backend | — | `run_cohort_scan_scene()` orchestrates per-customer iteration and aggregation |
| Dynamic condition query parsing | API / Backend | — | Scene layer interprets natural language into filter criteria; existing backend supports record fetching |
| Per-customer four-lens analysis | API / Backend | — | Reuses existing EvidenceContainer + scene analysis per customer |
| Cohort aggregation | API / Backend | — | Scene layer combines per-customer results into cohort signals/issues |
| EvidenceContainer lens tracking | API / Backend | — | Extend EvidenceContainer with per-lens source attribution (D-10) |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `runtime/scene_runtime.py` | existing | Scene functions including `run_customer_recent_status_scene()` | Base for STAT-01 upgrade |
| `runtime/expert_analysis_helper.py` | existing | `EvidenceContainer`, `ExpertAnalysisHelper`, `EvidenceSource` | Phase 16 foundation for multi-source evidence |
| `runtime/scene_registry.py` | existing | Scene dispatch via `build_default_scene_registry()` | SCAN-01 registers same way |
| `runtime/models.py` | existing | `SceneResult`, `SceneRequest`, `CustomerMatch`, `CustomerResolution` | Unchanged contract |
| `runtime/live_adapter.py` | existing | `LarkCliCustomerBackend` with `_list_records()` for customer master | Fetches all customers for cohort scan |
| `evals/meeting_output_bridge.py` | existing | `_derive_structured_sections()` with keyword-based extraction | Pattern to replicate for four-lens STAT-01 |

### No New Dependencies
Phase 18 requires no new npm/pypi packages — all functionality achieved through existing codebase patterns.

## Architecture Patterns

### System Architecture Diagram

```
User Input (STAT-01 or SCAN-01)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  scene_runtime.py                                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  run_customer_recent_status_scene() [STAT-01 upgrade] │  │
│  │  run_cohort_scan_scene() [SCAN-01 new]                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐   ┌─────────────────────────────────────┐
│ EvidenceContainer│   │ For SCAN-01:                      │
│ (with lens-aware │   │ LarkCliCustomerBackend._list_records()
│  source tracking)│   │ → all customers → filter by       │
└─────────────────┘   │   dynamic condition query           │
         │            │   → per-customer STAT-01 analysis   │
         ▼            │   → aggregate cohort signals        │
┌─────────────────────────────────────────────────────────────┐
│  Four-Lens Output (per STAT-01 D-01)                       │
│  judgments = [                                              │
│    "风险: <lens-1-conclusion>",                            │
│    "风险: <lens-2-conclusion>",                            │
│    "机会: <lens-1-conclusion>",                            │
│    ...                                                      │
│  ]                                                          │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  SceneResult (unchanged contract)                           │
│  → output_text, judgments, recommendations, payload          │
└─────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
runtime/
├── scene_runtime.py          # MODIFY: add run_cohort_scan_scene();
│                             #        upgrade run_customer_recent_status_scene()
├── scene_registry.py         # MODIFY: register "cohort-scan" scene
├── expert_analysis_helper.py # MODIFY: add lens-aware EvidenceContainer extension
│                             #        or separate LensAwareContainer
├── live_adapter.py           # MODIFY: LarkCliCustomerBackend.add_filter_query()
│                             #        for dynamic condition query
models/
├── models.py                 # MODIFY: add CohortScanRequest, CohortFilterCondition,
│                             #        LensLabeledJudgment (or reuse existing)
evals/
├── meeting_output_bridge.py   # EXTEND: reuse _derive_structured_sections pattern
│                             #        for four-lens extraction
tests/
├── test_scene_runtime.py     # MODIFY: add tests for STAT-01 four-lens output
│                             #        and SCAN-01 cohort scan
├── test_cohort_scan.py        # CREATE: new test file for SCAN-01
```

### Pattern 1: Four-Lens Output (STAT-01)

**What:** STAT-01 produces structured judgments in the `judgments` field with lens labels (风险, 机会, 关系, 进展), 1-3 conclusions per lens.

**When to use:** Single-customer account posture readout.

**Implementation approach:** Extend `run_customer_recent_status_scene()` to use the `EvidenceContainer` and keyword-based section derivation similar to Phase 17's `_derive_structured_sections()`. The lens assignment logic (which sources feed which lens) remains at the scene layer per D-09.

```python
# Pattern for four-lens judgments (STAT-01)
# Source: derived from _derive_structured_sections() in evals/meeting_output_bridge.py

LENS_SOURCE_MAP = {
    "risk": ["customer_master", "contact_records", "action_plan"],
    "opportunity": ["customer_master", "meeting_notes", "action_plan"],
    "relationship": ["contact_records", "meeting_notes"],
    "project_progress": ["action_plan", "meeting_notes", "customer_archive"],
}

def _derive_account_posture_lenses(
    container: EvidenceContainer,
) -> dict[str, list[str]]:
    """Derive four account-posture lenses from evidence container.

    Returns dict with keys: risk, opportunity, relationship, project_progress.
    Each value is 1-3 scannable conclusions.
    """
    # Lens-specific source text collection
    lens_texts: dict[str, list[str]] = {lens: [] for lens in LENS_SOURCE_MAP}
    for lens, source_names in LENS_SOURCE_MAP.items():
        for name in source_names:
            src = container.sources.get(name)
            if src and src.available and src.content:
                lens_texts[lens].extend(src.content)

    # Keyword-based extraction per lens
    combined = {lens: " ".join(texts) for lens, texts in lens_texts.items()}

    RISK_KEYWORDS = {"风险", "预警", "下降", "流失", "竞品", "问题", "挑战", "障碍", "下滑", "收紧", "压力", "危机", "逾期", "负向"}
    OPPORTUNITY_KEYWORDS = {"机会", "扩张", "增加", "扩容", "新客", "开拓", "增长", "潜力", "空间", "上行", "突破", "拓展", "增量", "机会点"}
    RELATIONSHIP_KEYWORDS = {"关系", "信任", "合作", "沟通", "对接", "联系", "配合", "协同", "维护", "深化"}
    PROJECT_PROGRESS_KEYWORDS = {"进展", "进度", "完成", "交付", "里程碑", "阶段", "推进", "落地", "执行", "状态"}

    def _extract_conclusions(text: str, keywords: set[str], max_items: int = 3) -> list[str]:
        seen: set[str] = set()
        items: list[str] = []
        for kw in keywords:
            if kw in text and kw not in seen:
                seen.add(kw)
                items.append(kw)
                if len(items) >= max_items:
                    break
        return items

    return {
        "risk": _extract_conclusions(combined.get("risk", ""), RISK_KEYWORDS),
        "opportunity": _extract_conclusions(combined.get("opportunity", ""), OPPORTUNITY_KEYWORDS),
        "relationship": _extract_conclusions(combined.get("relationship", ""), RELATIONSHIP_KEYWORDS),
        "project_progress": _extract_conclusions(combined.get("project_progress", ""), PROJECT_PROGRESS_KEYWORDS),
    }
```

### Pattern 2: Cohort Scan Scene (SCAN-01)

**What:** New scene that fetches multiple customers, applies dynamic condition filter, runs per-customer four-lens analysis, then aggregates into cohort-level signals and per-customer highlights.

**When to use:** User asks "show me all customers with activity in last 3 months" or similar cohort definition.

**Implementation approach:**

```python
# Pattern for SCAN-01 scene function
def run_cohort_scan_scene(request: SceneRequest) -> SceneResult:
    """Cohort scan scene — user-triggered analytical entry point.

    Implements D-03 (dynamic condition query), D-04 (limit default 10),
    D-05 (aggregated summary + key customers), D-06-D-08 (output structure).
    """
    cohort_limit = request.options.get("cohort_limit", 10)
    condition_query = request.inputs.get("condition_query", "")  # natural language

    # 1. Fetch all customers from customer master
    backend = _build_customer_backend(request.repo_root)
    all_customers = backend.list_all_customers()  # uses _list_records with limit=200

    # 2. Parse dynamic condition into filter criteria
    filter_criteria = _parse_condition_query(condition_query)  # D-03

    # 3. Apply filter to get cohort
    cohort = _apply_filter(all_customers, filter_criteria)

    # 4. Check limit — if exceeded, return prompt to narrow (D-04)
    if len(cohort) > cohort_limit:
        return _build_cohort_limit_result(request, cohort, cohort_limit)

    # 5. Per-customer four-lens analysis (reuses STAT-01 pattern)
    customer_results: list[dict[str, Any]] = []
    for customer in cohort:
        per_customer_lenses = _run_single_customer_lens_analysis(customer)
        customer_results.append(per_customer_lenses)

    # 6. Aggregate cohort-level signals and issues (D-05)
    cohort_signals = _aggregate_cohort_signals(customer_results)
    cohort_issues = _aggregate_cohort_issues(customer_results)
    key_customers = _select_key_customers(customer_results)  # top 3-5 by risk/opportunity

    # 7. Build two-tier recommendations (D-07, D-08)
    recommendations = _build_cohort_recommendations(
        cohort_signals=cohort_signals,
        cohort_issues=cohort_issues,
        key_customers=key_customers,
    )

    # 8. Render output
    output_text = _render_cohort_output(cohort_signals, cohort_issues, key_customers, recommendations)

    return SceneResult(
        scene_name=request.scene_name,
        resource_status="resolved",
        customer_status="cohort",
        context_status="completed",
        used_sources=["customer_master", "contact_records", "action_plan", "meeting_notes"],
        facts=[],
        judgments=_render_lens_judgments(customer_results),
        open_questions=[],
        recommendations=recommendations,
        fallback_category="none",
        fallback_reason=None,
        fallback_message=None,
        write_ceiling="recommendation-only",
        output_text=output_text,
        payload={
            "cohort_size": len(cohort),
            "key_customers": key_customers,
            "cohort_signals": cohort_signals,
            "cohort_issues": cohort_issues,
        },
    )
```

### Pattern 3: Dynamic Condition Query Parsing

**What:** Interpret natural language cohort description into filter criteria.

**When to use:** SCAN-01 user defines cohort via description like "customers with activity in last 3 months".

**Implementation approach:** Simple keyword/pattern extraction to build filter criteria:

```python
# Pattern for dynamic condition parsing (D-03)
def _parse_condition_query(condition_query: str) -> dict[str, Any]:
    """Parse natural language condition into filter criteria.

    Returns dict like:
      {"activity_within_days": 90,
       "has_open_tasks": True,
       "status": ["active", "expanding"]}
    """
    criteria: dict[str, Any] = {}

    query_lower = condition_query.lower()

    # Activity-based filters
    if "最近" in condition_query or "近" in condition_query:
        import re
        days_match = re.search(r"(\d+)\s*(天|月|周)", condition_query)
        if days_match:
            amount, unit = days_match.groups()
            days = int(amount) * {"天": 1, "周": 7, "月": 30}.get(unit, 1)
            criteria["activity_within_days"] = days

    # Status-based filters
    if "活跃" in condition_query or "active" in query_lower:
        criteria.setdefault("status", []).append("active")
    if "风险" in condition_query or "risk" in query_lower:
        criteria.setdefault("status", []).append("at_risk")
    if "机会" in condition_query or "opportunity" in query_lower:
        criteria.setdefault("status", []).append("opportunity")

    # Fallback: use full text as text-match filter on customer names
    if not criteria:
        criteria["name_contains"] = condition_query

    return criteria
```

### Anti-Patterns to Avoid
- **Adding scheduled/automated scanning:** SCAN-01 is explicitly user-triggered (D-12). Do not add cron, queue, or timer-based scanning.
- **Bypassing EvidenceContainer for STAT-01:** Even for single-customer analysis, EvidenceContainer provides source tracking per lens (D-10). Do not skip it.
- **Unbounded cohort output:** D-04 mandates a default limit of 10; if exceeded, the scene returns a prompt to narrow rather than a bloated result.
- **More than ~10 recommendations:** D-08 caps at 10 total; aggregate or prioritize ruthlessly.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-source evidence assembly | Custom source aggregation | `EvidenceContainer` + `ExpertAnalysisHelper` | Already handles quality tracking, missing-source flags, write ceiling |
| Scene dispatch | Custom scene router | `scene_registry.py` + `build_default_scene_registry()` | Already handles unknown scene errors and registration |
| Four-lens keyword extraction | LLM-based interpretation | Phase 17's `_derive_structured_sections()` pattern | Keyword-based is deterministic, fast, no API cost |
| Customer master fetching | Direct API calls | `LarkCliCustomerBackend._list_records()` | Already authenticated and configured |

**Key insight:** The Phase 16 EvidenceContainer infrastructure and Phase 17 four-section derivation pattern provide 80% of STAT-01 and SCAN-01. Phase 18 combines and extends, not reinvents.

## Runtime State Inventory

> Not applicable — Phase 18 is a greenfield feature addition (STAT-01 upgrade + SCAN-01 new scene), not a rename/refactor/migration phase.

## Common Pitfalls

### Pitfall 1: Unbounded Cohort Result Set
**What goes wrong:** User asks for "all customers" and gets an unwieldy result.
**Why it happens:** No limit enforcement when fetching from customer master.
**How to avoid:** D-04 mandates explicit limit check; if exceeded, return structured prompt to narrow scope.
**Warning signs:** Cohort size > 10 in payload without `fallback_category` set.

### Pitfall 2: Four-Lens Output Without Source Attribution
**What goes wrong:** Lens conclusions appear disconnected from their evidence sources.
**Why it happens:** Skipping EvidenceContainer per-lens tracking (D-10).
**How to avoid:** Each lens conclusion must be traceable to a specific `EvidenceSource` in the container.
**Warning signs:** `judgments` list items don't map to `payload.evidence_container.sources`.

### Pitfall 3: Modifying SceneResult Contract
**What goes wrong:** Downstream code (gateway, UI adapters) breaks when unexpected fields appear.
**Why it happens:** Adding new top-level fields to SceneResult instead of using `payload`.
**How to avoid:** All new structured data (cohort_signals, key_customers, lens_judgments) goes in `SceneResult.payload`, not top-level fields.

### Pitfall 4: Heavy LLM Inference in Hot Path
**What goes wrong:** Cohort scan with per-customer LLM analysis becomes slow/expensive.
**Why it happens:** Using LLM for every lens derivation instead of keyword-based extraction.
**How to avoid:** Reuse `_derive_structured_sections()` keyword approach; save LLM for complex cases requiring expert judgment (post-aggregation).

## Code Examples

### STAT-01 Upgrade: Lens-Aware EvidenceContainer Extension

```python
# Extension to expert_analysis_helper.py or scene_runtime.py
# Per D-10: EvidenceContainer tracks source evidence per lens

@dataclass
class LensAttribution:
    lens: str  # "risk", "opportunity", "relationship", "project_progress"
    source_names: list[EvidenceSourceName]
    conclusion: str
    confidence: float = 1.0


def build_lens_attributions(
    container: EvidenceContainer,
    lens_results: dict[str, list[str]],
) -> list[LensAttribution]:
    """Build per-lens source attribution for STAT-01 output.

    D-10: Each lens draws from relevant sources.
    """
    attributions: list[LensAttribution] = []
    for lens_name, conclusions in lens_results.items():
        source_map = {
            "risk": ["customer_master", "contact_records", "action_plan"],
            "opportunity": ["customer_master", "meeting_notes", "action_plan"],
            "relationship": ["contact_records", "meeting_notes"],
            "project_progress": ["action_plan", "meeting_notes", "customer_archive"],
        }
        source_names = source_map.get(lens_name, [])
        for conclusion in conclusions:
            attributions.append(LensAttribution(
                lens=lens_name,
                source_names=source_names,
                conclusion=conclusion,
            ))
    return attributions
```

### SCAN-01: Dynamic Condition Query via CustomerBackend Extension

```python
# Extension to live_adapter.py — LarkCliCustomerBackend
# D-03: User defines cohort via dynamic condition query

class LarkCliCustomerBackend:
    # ... existing methods ...

    def list_all_customers(self, limit: int = 200) -> list[dict[str, str]]:
        """List all customers from customer master for cohort scanning."""
        if not self.config.base_token:
            return []
        return self._list_records(self.config.table_target("客户主数据"), limit=limit)

    def filter_customers(
        self,
        customers: list[dict[str, str]],
        criteria: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Apply filter criteria to customer list.

        Supports: activity_within_days, status, name_contains
        """
        filtered = customers
        if "name_contains" in criteria:
            term = criteria["name_contains"].lower()
            filtered = [
                c for c in filtered
                if term in str(c.get("简称", "")).lower()
                or term in str(c.get("客户名称", "")).lower()
            ]
        if "status" in criteria:
            statuses = criteria["status"]
            filtered = [c for c in filtered if c.get("状态") in statuses]
        # Additional criteria handlers...
        return filtered
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flat recent-status output with generic summary | Four-lens structured output (risk/opportunity/relationship/project-progress) | Phase 18 | Each lens produces 1-3 scannable conclusions for faster AM triage |
| Single-customer only | Single-customer (STAT-01) + cohort scan (SCAN-01) | Phase 18 | AMs can now analyze individual accounts AND groups |
| Keyword-only four-section (Phase 17) | Lens-aware source attribution per conclusion | Phase 18 | Conclusions are traceable to specific evidence sources |

**Deprecated/outdated:**
- None in scope for Phase 18.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `_list_records()` on customer master table can return up to 200 records for cohort scan | SCAN-01 implementation | If limit is lower, cohort scan may miss customers — verify with live Feishu API |
| A2 | Dynamic condition query parsing via keyword extraction is sufficient for v1.2 | SCAN-01 implementation | If user queries are more complex, may need fuller NLP parsing — defer to Phase 21 if needed |

## Open Questions

1. **What fields in the customer master support dynamic condition filtering?**
   - What we know: Customer master has 简称, 客户名称, 公司名称, 客户ID, 客户档案, 状态 fields.
   - What's unclear: Are there activity/tracking fields (last_contact_date, last_activity) usable for "activity in last N days" filters?
   - Recommendation: Check actual Feishu table schema for customer master to confirm what filter fields are available.

2. **How does the LLM expert analysis layer interact with the keyword-based lens extraction?**
   - What we know: Phase 17 uses keyword-based extraction for four-section output.
   - What's unclear: Should STAT-01/SCAN-01 also have an optional LLM enhancement pass?
   - Recommendation: Start with keyword-only (consistent with Phase 17), add LLM layer in Phase 21 if VAL-05 validation shows gaps.

3. **Should cohort scan results be cached or stored?**
   - What we know: SCAN-01 is user-triggered analytical entry, not scheduled.
   - What's unclear: Does the user need results persisted for later reference?
   - Recommendation: Not in v1.2 scope; deferred to SCAN-02 or WRITE-01/02 phases.

## Environment Availability

Step 2.6: SKIPPED (no external dependencies beyond existing codebase)

Phase 18 uses only existing runtime code and Python standard library. No new package installations required.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | pytest.ini (if present) or pyproject.toml |
| Quick run command | `pytest tests/test_scene_runtime.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STAT-01 | Four-lens output (risk/opportunity/relationship/project_progress) in judgments | unit | `pytest tests/test_scene_runtime.py::TestStat01FourLensOutput -x` | YES (will extend) |
| STAT-01 | Each lens produces 1-3 conclusions | unit | `pytest tests/test_scene_runtime.py::TestStat01LensCount -x` | NO (new) |
| STAT-01 | Lens attributions traceable to EvidenceContainer sources | unit | `pytest tests/test_scene_runtime.py::TestStat01LensAttribution -x` | NO (new) |
| SCAN-01 | Cohort scene registered and dispatchable | unit | `pytest tests/test_scene_runtime.py::TestCohortScanDispatch -x` | NO (new) |
| SCAN-01 | Dynamic condition query parsing | unit | `pytest tests/test_cohort_scan.py::TestConditionQueryParsing -x` | NO (new) |
| SCAN-01 | Cohort limit enforcement (default 10, prompt if exceeded) | unit | `pytest tests/test_cohort_scan.py::TestCohortLimit -x` | NO (new) |
| SCAN-01 | Aggregated cohort signals and per-customer highlights | unit | `pytest tests/test_cohort_scan.py::TestCohortAggregation -x` | NO (new) |
| SCAN-01 | Recommendation cap (~10 total) | unit | `pytest tests/test_cohort_scan.py::TestRecommendationCap -x` | NO (new) |

### Sampling Rate
- **Per task commit:** `pytest tests/test_scene_runtime.py -x -q` (fast subset)
- **Per wave merge:** `pytest tests/ -x -q` (full suite)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- `tests/test_scene_runtime.py` — extend existing with STAT-01 four-lens tests
- `tests/test_cohort_scan.py` — new file covering SCAN-01 behaviors
- No framework install needed — pytest already present

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V4 Access Control | no | N/A — read-only analytical queries |
| V5 Input Validation | yes | Natural language condition query parsed via keyword extraction — no direct user input to SQL |

### Known Threat Patterns for Phase 18 Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Condition query injection into customer filter | Tampering | Keyword-based extraction only; no raw SQL construction |
| Unbounded cohort enumeration | Information Disclosure | D-04 limit enforcement (default 10) prevents large result dumps |

**Security note:** Phase 18 is read-only analytical output. No writes, no authentication changes, no new data exposure paths. Security surface is minimal.

## Sources

### Primary (HIGH confidence)
- `runtime/scene_runtime.py` — verified `run_customer_recent_status_scene()` structure and `_build_context_result()` pattern
- `runtime/scene_registry.py` — verified scene registration pattern via `build_default_scene_registry()`
- `runtime/expert_analysis_helper.py` — verified `EvidenceContainer`, `ExpertAnalysisHelper.assemble()`, and `EvidenceAssemblyInput` patterns
- `evals/meeting_output_bridge.py` — verified `_derive_structured_sections()` keyword extraction pattern for four-section output
- `runtime/live_adapter.py` — verified `LarkCliCustomerBackend.search_customer_master()` and `_list_records()` for customer fetching

### Secondary (MEDIUM confidence)
- Phase 17 four-section output decisions (D-01 to D-08 in 17-CONTEXT.md) — STAT-01 uses parallel lens framing
- Phase 16 EvidenceContainer decisions (D-04, D-05, D-10 in 16-CONTEXT.md) — lens-aware source tracking principle

### Tertiary (LOW confidence)
- Customer master field schema (assumed fields: 简称, 客户名称, 公司名称, 客户ID, 客户档案, 状态) — confirmed via `customer_resolver.py` but not verified against live Feishu table schema

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all existing libraries, no new dependencies
- Architecture: HIGH — patterns verified in codebase (Phase 16/17), decisions locked in 18-CONTEXT.md
- Pitfalls: MEDIUM — some assumptions about customer master schema and condition query complexity

**Research date:** 2026-04-17
**Valid until:** 2026-05-17 (30 days for stable phase)
