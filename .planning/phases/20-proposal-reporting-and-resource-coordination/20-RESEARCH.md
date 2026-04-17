# Phase 20: Proposal, Reporting, And Resource Coordination - Research

**Researched:** 2026-04-18
**Domain:** Python CLI scene runtime with Feishu workbench integration
**Confidence:** HIGH

## Summary

Phase 20 delivers a unified `proposal` scene supporting three types (proposal/report/resource-coordination) with a fixed five-dimension output format. The scene reuses Phase 16 EvidenceContainer and ExpertAnalysisHelper for materials assembly, extends Phase 19 confirmation checklist infrastructure for WRITE-02, and implements Feishu-native output routing per WRITE-01. The implementation follows the same scene runtime pattern as `run_meeting_prep_scene()` but with proposal-specific checklist, keyword sets, and output dimensions.

**Primary recommendation:** Implement `run_proposal_scene()` as the 7th registered scene, using `build_proposal_checklist()` (extending confirmation_checklist.py), five-dimension keyword extraction, and type-based Feishu routing via existing RuntimeSources.

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Single unified `proposal` scene registered in scene registry -- three types differentiated by `proposal_type` parameter (proposal / report / resource-coordination)
- **D-02:** Three types share same input structure and five-section output format, with type-specific emphasis
- **D-03:** Scene handler: `run_proposal_scene()` registered as `proposal` in scene_registry.py
- **D-04:** User explicitly names primary reference materials; system auto-supplements via EvidenceContainer
- **D-05:** EvidenceContainer presents "I found these materials" before scene execution
- **D-06:** Fixed five-section output: Objective, Core Judgment, Main Narrative, Resource Asks, Open Questions
- **D-07:** Type-specific emphasis: proposal emphasizes core judgment + narrative; report emphasizes narrative; resource-coordination emphasizes resource asks
- **D-08:** Output delivered as structured text + SceneResult.payload
- **D-09:** Each scene has independent judgment logic -- shared infrastructure, independent scene-layer judgment
- **D-10:** Default routing by type: proposal/report -> Drive customer folder; resource-coordination -> Task or Base 行动计划 table
- **D-11:** Routing is recommendation + confirmation (WRITE-02 pattern)
- **D-12:** WRITE-01 applies to proposal and reporting artifacts
- **D-13:** Reuses Phase 19 confirmation_checklist.py infrastructure
- **D-14:** Proposal checklist: WRITE-02 universal four items + scene-specific (proposal_type, output_destination)
- **D-15:** Minimal-questions principle -- system infers suggestions, user only confirms or modifies
- **D-16:** No agency introduction -- remains recommendation-first and human-in-the-loop

### Deferred Ideas (OUT OF SCOPE)

- Agency / autonomous agent capability -- would require dedicated milestone with authority boundaries, safety confirmations, and accountability models
- Shared judgment framework across scenes -- per D-09, each scene has independent judgment

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PROP-01 | Proposal/report/resource-coordination structured draft with five-dimension output | Keyword-based lens extraction proven in Phase 16/17/18/19; extends to 5 proposal dimensions |
| WRITE-01 | Feishu-native durable-output routing by default | RuntimeSources.customer_archive_folder for Drive; action_plan_table for Base; TodoWriter for Task |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Five-dimension proposal synthesis | API/Backend (scene_runtime.py) | -- | EvidenceContainer assembly and lens extraction happen at scene layer |
| Pre-scene confirmation checklist | API/Backend | -- | Checklist rendering and confirmation before scene dispatch |
| Feishu-native output routing | API/Backend | -- | Drive folder (proposal/report), Base table or Task (resource-coordination) |
| ExpertAnalysisHelper materials assembly | API/Backend | -- | Phase 16 foundation; assembles but does not interpret |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python 3.11+ | current | Runtime language | Project requirement |
| pytest | current | Test framework | Per common/testing.md |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `EvidenceContainer` | existing (Phase 16) | Track sources per dimension | All scene evidence assembly |
| `ExpertAnalysisHelper` | existing (Phase 16) | Assembly/combination only | Scene layer uses, does not interpret |
| `SceneRegistry` | existing (Phase 16) | Scene dispatch | New `proposal` registers here |
| `SceneResult` | existing (Phase 16) | Scene output contract | All scenes return same contract |
| `ConfirmationChecklist` | existing (Phase 19) | WRITE-02 checklist infrastructure | Extended by `build_proposal_checklist()` |
| `LiveWorkbenchConfig` | existing (Phase 19) | Feishu source configuration | Used for Drive/Base routing |

## Architecture Patterns

### System Architecture Diagram

```
User Input (customer + goal + materials)
    │
    ├─► [Pre-scene Checklist] ──► build_proposal_checklist()
    │       │                         │
    │       │                         ├─► WRITE-02 universal items
    │       │                         ├─► proposal_type (proposal/report/resource-coordination)
    │       │                         └─► output_destination (system-suggested per type)
    │       │
    ├─► [Proposal Scene: run_proposal_scene()]
    │       │
    │       └─► EvidenceContainer ──► Five-dimension lens extraction
    │                                       │
    │                                       ├─► Objective (目的) -- 1-2 sentences on goal
    │                                       ├─► Core Judgment (核心判断) -- 2-4 expert assessments
    │                                       ├─► Main Narrative (主要叙事) -- structured arguments
    │                                       ├─► Resource Asks (资源请求) -- resources needed (emphasized for resource-coordination)
    │                                       └─► Open Questions (待确认问题) -- unresolved items
    │
    └─► [Feishu Output Routing]
            │
            ├─► proposal type -> Drive customer archive folder
            ├─► report type -> Drive customer archive folder or weekly-report folder
            └─► resource-coordination type -> Task module or Base 行动计划 table
```

### Recommended Project Structure

```
runtime/
├── scene_runtime.py           # Existing scenes + new run_proposal_scene()
├── scene_registry.py          # Registers new "proposal" scene
├── confirmation_checklist.py  # Phase 19 infrastructure + new build_proposal_checklist()
├── expert_analysis_helper.py  # Phase 16 foundation (unchanged)
```

### Pattern 1: run_proposal_scene() (extends run_meeting_prep_scene() pattern)

Per D-03, D-08: follows same structure as `run_meeting_prep_scene()`.

```python
# Source: scene_runtime.py lines 704-843 (run_meeting_prep_scene)
def run_proposal_scene(request: SceneRequest) -> SceneResult:
    topic_text = str(request.inputs.get("topic_text") or "")
    gateway_result, recovery = _build_live_scene_context(request, topic_text=topic_text)

    # Build confirmation checklist BEFORE scene output (per D-13)
    checklist = build_proposal_checklist(evidence_container, recovery)
    checklist_output = render_confirmation_checklist(checklist)

    # Derive five-dimension lenses from evidence
    evidence_container = getattr(recovery, 'evidence_container', None)
    lens_results = _derive_proposal_lenses(evidence_container)

    # Type-specific emphasis per D-07
    proposal_type = request.inputs.get("proposal_type", "proposal")

    # Render five-dimension output
    output_lines = _render_proposal_output(lens_results, proposal_type)

    # Build output: checklist shown first, then five-dimension brief
    lines = checklist_output + output_lines + [...standard context...]

    return _build_context_result(
        request=request,
        gateway_result=gateway_result,
        recovery=recovery,
        facts=facts,
        judgments=judgments,
        open_questions=open_questions,
        recommendations=recommendations,
        output_text="\n".join(lines),
        payload={
            "scene_payload": {
                "proposal_type": proposal_type,
                "proposal_lenses": lens_results,
                "confirmation_checklist_output": checklist_output,
                "confirmed_answers": checklist.confirmed_answers(),
                "evidence_container": evidence_container,
            }
        },
    )
```

### Pattern 2: Five-Dimension Keyword Sets for Proposal

Extends ARCH-01/STAT-01 keyword extraction pattern per D-06.

```python
# Five-dimension keyword sets for PROP-01
_PROPOSAL_OBJECTIVE_KEYWORDS = {"目标", "目的", "意图", "期望", "想要达成"}
_PROPOSAL_JUDGMENT_KEYWORDS = {"判断", "评估", "结论", "认为", "结论是", "核心是"}
_PROPOSAL_NARRATIVE_KEYWORDS = {"叙事", "说明", "阐述", "背景", "情况", "现状", "原因"}
_PROPOSAL_RESOURCE_KEYWORDS = {"资源", "支持", "协助", "需要", "请求", "投入", "预算", "人力", "时间"}
_PROPOSAL_QUESTION_KEYWORDS = {"待确认", "待定", "不确定", "需确认", "疑问", "问题"}

# Source mapping per dimension
_PROPOSAL_LENS_SOURCE_MAP = {
    "objective": ["customer_master", "meeting_notes"],
    "core_judgment": ["customer_master", "action_plan", "meeting_notes"],
    "main_narrative": ["meeting_notes", "customer_archive", "action_plan"],
    "resource_asks": ["action_plan", "meeting_notes"],
    "open_questions": ["customer_archive", "contact_records"],
}
```

### Pattern 3: build_proposal_checklist() (extends Phase 19 pattern)

Per D-13, D-14, D-15: reuses ConfirmationChecklist infrastructure with scene-specific items.

```python
# Source: confirmation_checklist.py lines 151-218 (build_meeting_prep_checklist)
def build_proposal_checklist(
    evidence_container: Any | None,
    recovery: Any | None,
) -> ConfirmationChecklist:
    """Build proposal scene confirmation checklist per D-13, D-14, D-15.

    D-13: Includes WRITE-02 universal items: audience, purpose, internal/external, resource-coordination.
    D-14: Scene-specific items -- proposal_type, output_destination.
    D-15: System-inferred suggestions from EvidenceContainer.
    """
    checklist = ConfirmationChecklist(scene_name="proposal")

    # WRITE-02 universal items (D-13)
    checklist.audience = ChecklistItem(
        key="audience",
        label="受众",
        system_suggestion="客户内部",
    )
    checklist.purpose = ChecklistItem(
        key="purpose",
        label="目的",
        system_suggestion="提案参考",
    )
    checklist.internal_external = ChecklistItem(
        key="internal_external",
        label="内部/外部",
        system_suggestion="内部使用",
    )
    checklist.resource_coordination = ChecklistItem(
        key="resource_coordination",
        label="资源协调需要",
        system_suggestion="不涉及" if evidence_container is None else _infer_resource_need(evidence_container),
    )

    # D-14: Scene-specific items
    # proposal_type is passed as input, shown as suggestion
    checklist.items.append(ChecklistItem(
        key="proposal_type",
        label="提案类型",
        system_suggestion="proposal",  # default, can be proposal/report/resource-coordination
    ))

    # D-15: output_destination inferred from proposal_type
    checklist.items.append(ChecklistItem(
        key="output_destination",
        label="输出目的地",
        system_suggestion=_infer_output_destination(evidence_container, recovery),
    ))

    return checklist
```

### Pattern 4: Feishu-Native Output Routing

Per D-10, D-11: type-based routing with confirmation.

```python
# Source: live_adapter.py lines 55-91 (LiveWorkbenchConfig)
# Routing configuration from RuntimeSources:
#   - customer_archive_folder: FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER
#   - action_plan_table: FEISHU_AM_ACTION_PLAN_TABLE (行动计划)
#   - todo_tasklist_guid: FEISHU_AM_TODO_TASKLIST_GUID

def _infer_output_destination(evidence_container: Any, recovery: Any) -> str:
    """Infer default output destination based on available Feishu resources.

    Per D-10: proposal_type determines routing:
      - proposal -> Drive customer archive folder
      - report -> Drive customer archive folder or weekly-report folder
      - resource-coordination -> Task module or Base 行动计划 table
    """
    if evidence_container is None:
        return "Drive 客户档案文件夹"

    # Check what Feishu resources are available
    arch_src = evidence_container.sources.get("customer_archive")
    if arch_src and arch_src.available:
        return f"Drive 已有档案: {arch_src.raw_data.get('name', '客户档案文件夹')}"

    return "Drive 客户档案文件夹"


def _route_proposal_output(
    proposal_type: str,
    confirmed_destination: str,
    output_content: str,
    customer_info: dict[str, Any],
) -> dict[str, Any]:
    """Route proposal output to Feishu destination per confirmed_destination.

    Per D-11: confirmed writes route through existing unified writer path.
    """
    if proposal_type in ("proposal", "report"):
        # Route to Drive folder
        return {
            "destination_type": "drive_doc",
            "target": confirmed_destination,  # folder_token
            "content": output_content,
            "customer": customer_info,
        }
    else:  # resource-coordination
        # Route to Base 行动计划 table or Task
        return {
            "destination_type": "base_table",
            "target": "行动计划",
            "content": _extract_action_items(output_content),
            "customer": customer_info,
        }
```

### Pattern 5: Scene Registration

Per D-03: registers as `proposal` in scene_registry.py.

```python
# Source: scene_registry.py lines 51-60
def build_default_scene_registry() -> SceneRegistry:
    registry = SceneRegistry()
    registry.register("post-meeting-synthesis", run_post_meeting_scene)
    registry.register("customer-recent-status", run_customer_recent_status_scene)
    registry.register("archive-refresh", run_archive_refresh_scene)
    registry.register("todo-capture-and-update", run_todo_capture_and_update_scene)
    registry.register("cohort-scan", run_cohort_scan_scene)
    registry.register("meeting-prep", run_meeting_prep_scene)
    # Phase 20: new scene
    registry.register("proposal", run_proposal_scene)  # <-- ADD THIS LINE
    return registry
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-source evidence assembly | Custom source tracking per scene | `EvidenceContainer` + `ExpertAnalysisHelper` | Phase 16 foundation; tracks quality, availability, missing sources |
| Five-dimension lens extraction | Custom synthesis functions | Keyword-based extraction pattern | Proven in STAT-01, ARCH-01, PREP-01 |
| WRITE-02 confirmation checklist | Custom checklist class | `build_proposal_checklist()` extending Phase 19 | Per D-13 reuses Phase 19 infrastructure |
| Feishu output routing | Custom routing logic | Existing RuntimeSources + LiveWorkbenchConfig | Already configured for Drive folders and Base tables |

## Common Pitfalls

### Pitfall 1: Re-using Phase 17/18 judgment logic instead of independent judgment
**What goes wrong:** Proposal scene imports or reuses post-meeting or account-posture judgment frameworks.
**Why it happens:** D-09 explicitly states independent scene-layer judgment, but implementing team may assume shared logic is more efficient.
**How to avoid:** Implement proposal-specific keyword sets and extraction in `run_proposal_scene()` only. Do NOT call `_derive_account_posture_lenses()` or `_derive_archive_refresh_lenses()` as subroutines.
**Warning signs:** Scene output format matches post-meeting or archive-refresh instead of proposal's five-dimension format.

### Pitfall 2: Missing type-specific emphasis in output
**What goes wrong:** All three proposal types emit identical output regardless of `proposal_type`.
**Why it happens:** D-07 defines type-specific emphasis but implementation doesn't vary content depth per type.
**How to avoid:** In `_render_proposal_output()`, add type-specific content depth -- proposal emphasizes core_judgment + main_narrative; report emphasizes main_narrative; resource-coordination emphasizes resource_asks.
**Warning signs:** Output for resource-coordination looks identical to proposal output.

### Pitfall 3: Drive doc creation without checking folder availability
**What goes wrong:** Output routing assumes Drive folder exists without verifying `customer_archive_folder` is configured.
**Why it happens:** WRITE-01 routing assumes Feishu resources are always available.
**How to avoid:** Check `runtime_sources.customer_archive_folder` availability before suggesting Drive routing. Fall back to "本地草稿" if Drive not accessible.
**Warning signs:** Output suggests Drive destination when `FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER` is not set.

### Pitfall 4: Breaking SceneResult contract with proposal-specific payload
**What goes wrong:** New scene adds fields that collide with `STANDARD_SCENE_RESULT_FIELDS`.
**Why it happens:** `proposal_lenses` or `proposal_type` added at top-level payload instead of inside `scene_payload`.
**How to avoid:** Use `_build_context_result()` for all scene result construction. Store proposal-specific data in `payload['scene_payload']` only.
**Warning signs:** Structured output has duplicate keys when calling `structured_result()`.

## Code Examples

### Five-Dimension Derivation Function

```python
# Source: Extends ARCH-01 pattern from scene_runtime.py lines 113-153
_PROPOSAL_LENS_SOURCE_MAP = {
    "objective": ["customer_master", "meeting_notes"],
    "core_judgment": ["customer_master", "action_plan", "meeting_notes"],
    "main_narrative": ["meeting_notes", "customer_archive", "action_plan"],
    "resource_asks": ["action_plan", "meeting_notes"],
    "open_questions": ["customer_archive", "contact_records"],
}

def _derive_proposal_lenses(
    evidence_container: Any,
) -> dict[str, list[str]]:
    """Derive five proposal lenses from evidence container.

    Returns dict with keys: objective, core_judgment, main_narrative, resource_asks, open_questions.
    Each value is 1-3 scannable conclusions (keywords found in source text).
    """
    if evidence_container is None:
        return {k: [] for k in _PROPOSAL_LENS_SOURCE_MAP.keys()}

    lens_texts: dict[str, list[str]] = {k: [] for k in _PROPOSAL_LENS_SOURCE_MAP.keys()}
    for lens_name, source_names in _PROPOSAL_LENS_SOURCE_MAP.items():
        for name in source_names:
            src = evidence_container.sources.get(name)
            if src and src.available and src.content:
                lens_texts[lens_name].extend(src.content)

    combined = {lens: " ".join(texts) for lens, texts in lens_texts.items()}

    def _extract(text: str, keywords: set[str], max_items: int = 3) -> list[str]:
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
        "objective": _extract(combined.get("objective", ""), _PROPOSAL_OBJECTIVE_KEYWORDS),
        "core_judgment": _extract(combined.get("core_judgment", ""), _PROPOSAL_JUDGMENT_KEYWORDS),
        "main_narrative": _extract(combined.get("main_narrative", ""), _PROPOSAL_NARRATIVE_KEYWORDS),
        "resource_asks": _extract(combined.get("resource_asks", ""), _PROPOSAL_RESOURCE_KEYWORDS),
        "open_questions": _extract(combined.get("open_questions", ""), _PROPOSAL_QUESTION_KEYWORDS),
    }
```

### Five-Dimension Output Rendering

```python
# Source: Per D-06, D-07 and UI-SPEC.md
def _render_proposal_output(
    lens_results: dict[str, list[str]],
    proposal_type: str,
) -> list[str]:
    """Render five-dimension proposal output per D-06, D-07.

    Type-specific emphasis:
      - proposal: emphasizes core_judgment + main_narrative
      - report: emphasizes main_narrative
      - resource-coordination: emphasizes resource_asks
    """
    lines = ["--- 提案/报告/资源协调草案 ---"]

    # Objective
    lines.append("目的:")
    obj_items = lens_results.get("objective", [])
    if obj_items:
        lines.extend(f"- {item}" for item in obj_items[:2])
    else:
        lines.append("- 暂无目的信息")

    # Core Judgment (emphasized for proposal type)
    lines.append("核心判断:")
    judgment_items = lens_results.get("core_judgment", [])
    if judgment_items:
        lines.extend(f"- {item}" for item in judgment_items[:4])
    else:
        lines.append("- 暂无核心判断")

    # Main Narrative (emphasized for report type, present for all)
    lines.append("主要叙事:")
    narrative_items = lens_results.get("main_narrative", [])
    if narrative_items:
        lines.extend(f"- {item}" for item in narrative_items[:3])
    else:
        lines.append("- 暂无叙事内容")

    # Resource Asks (emphasized for resource-coordination type)
    lines.append("资源请求:")
    resource_items = lens_results.get("resource_asks", [])
    if resource_items:
        lines.extend(f"- {item}" for item in resource_items[:3])
    else:
        lines.append("- 暂无资源请求")

    # Open Questions
    lines.append("待确认问题:")
    question_items = lens_results.get("open_questions", [])
    if question_items:
        lines.extend(f"- {item}" for item in question_items[:3])
    else:
        lines.append("- 暂无待确认问题")

    return lines
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No proposal scene | Unified proposal scene with three types (PROP-01) | Phase 20 | Single scene handles proposal/report/resource-coordination via proposal_type parameter |
| No Feishu-native output routing for proposals | Default routing to Drive or Base per type (WRITE-01) | Phase 20 | Proposal outputs route to Feishu destinations by default |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Drive doc creation uses existing `customer_archive_folder` for folder token | Architecture Patterns | If Drive API requires different folder token, routing logic needs update |
| A2 | Base 行动计划 table supports resource-coordination writes | Architecture Patterns | If table schema incompatible, need separate writer path |
| A3 | Five-dimension keyword extraction sufficient for proposal output | Common Pitfalls | If LLM synthesis required, entire approach needs redesign |

**If this table is empty:** All claims in this research were verified or cited -- no user confirmation needed.

## Open Questions

1. **How does lark-cli create a Drive document in a folder?**
   - What we know: `LarkCliResourceProbe._confirm_drive_folder()` checks folder access; `customer_archive_folder` is the folder token
   - What's unclear: Is there a `drive doc create` subcommand in lark-cli, or does it require different API?
   - Recommendation: Check lark-cli documentation for doc creation commands

2. **Does the Base table write path support resource-coordination items?**
   - What we know: `行动计划` table has `customer_id`, `subject`, `due_at` as dedupe keys
   - What's unclear: Whether resource items fit the existing action plan schema
   - Recommendation: Verify schema compatibility before implementing Base routing for resource-coordination

3. **How is proposal_type passed from user input to scene?**
   - What we know: SceneRequest.inputs contains arbitrary key-value pairs
   - What's unclear: Is `proposal_type` a required input or optional with default?
   - Recommendation: Make `proposal_type` optional with default "proposal"; infer from goal keywords if not provided

## Environment Availability

Step 2.6: SKIPPED (no external dependencies beyond existing codebase)

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | pytest.ini (if exists) or pyproject.toml |
| Quick run command | `pytest tests/test_scene_runtime.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PROP-01 | Five-dimension output produces conclusions per dimension | unit | `pytest tests/test_proposal_scene.py::TestProposalFiveDimension -x` | needs new |
| PROP-01 | Type-specific emphasis varies by proposal_type | unit | `pytest tests/test_proposal_scene.py::TestProposalTypeEmphasis -x` | needs new |
| WRITE-01 | Output routing suggestion based on proposal_type | unit | `pytest tests/test_proposal_scene.py::TestProposalRouting -x` | needs new |
| WRITE-02 | Checklist includes WRITE-02 universal + scene-specific items | unit | `pytest tests/test_proposal_scene.py::TestProposalChecklist -x` | needs new |

### Wave 0 Gaps
- `tests/test_scene_runtime.py` -- existing, covers Phase 12-19 scenes
- `tests/test_proposal_scene.py` -- needed for PROP-01, WRITE-01 (Phase 20)
- `tests/test_confirmation_checklist.py` -- already exists (Phase 19), needs `build_proposal_checklist` tests
- Framework install: already detected (pytest in project)

## Security Domain

Step: SKIPPED (security_enforcement not explicitly disabled; however this phase is internal CLI scene logic with no new external attack surface. All writes route through existing guarded writer path per D-16.)

## Sources

### Primary (HIGH confidence)
- `runtime/scene_runtime.py` -- verified run_meeting_prep_scene() implementation pattern, keyword extraction, SceneResult contract
- `runtime/confirmation_checklist.py` -- verified ConfirmationChecklist, ChecklistItem, build_meeting_prep_checklist() pattern
- `runtime/scene_registry.py` -- verified SceneRegistry dispatch mechanism, scene registration pattern
- `runtime/expert_analysis_helper.py` -- verified EvidenceContainer, ExpertAnalysisHelper, LENS_SOURCE_MAP
- `runtime/live_adapter.py` -- verified LiveWorkbenchConfig, RuntimeSources for Drive/Base routing
- `runtime/models.py` -- verified SceneRequest, SceneResult, WriteCandidate contracts

### Secondary (MEDIUM confidence)
- Phase 19 RESEARCH.md -- verified confirmation checklist design, minimal-questions principle, WRITE-02 infrastructure
- Phase 16/19 context files -- provided architectural decisions and integration points

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries and patterns verified from existing codebase
- Architecture: HIGH -- patterns from Phase 16/18/19 are established and Phase 20 extends them
- Pitfalls: MEDIUM -- type-specific emphasis and routing logic not yet implemented, could vary from assumptions

**Research date:** 2026-04-18
**Valid until:** 2026-05-18 (30 days for stable domain)
