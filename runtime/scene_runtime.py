"""Shared scene runtime contracts and the first scene adapter."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


from .gateway import FeishuWorkbenchGateway
from .lark_cli import LarkCliClient
from .live_adapter import LarkCliBaseQueryBackend, LarkCliCustomerBackend, LiveWorkbenchConfig
from .models import WriteCandidate, WriteExecutionResult
from .runtime_sources import RuntimeSourceLoader
from .todo_writer import TodoWriter
from .expert_analysis_helper import EvidenceContainer, EvidenceSource
from .confirmation_checklist import (
    build_archive_refresh_checklist,
    build_meeting_prep_checklist,
    build_proposal_checklist,
    render_confirmation_checklist,
)
from .expert_card_loader import RegistryCache


@dataclass(frozen=True)
class PlatformCapabilities:
    """Per-platform capability map for orchestration strategy selection.

    Per OpenCode review concern LOW-09: capability detection per platform.
    Per AA-01-PLAN.md Section 4: platform adapter selection.
    """
    platform: str
    supports_parallel: bool          # Can run multiple subagents concurrently
    supports_streaming: bool         # Can stream responses
    supports_structured_output: bool # Can return typed/structured responses
    supports_toolsets: bool          # Has tool-calling capability
    max_concurrent: int              # Maximum concurrent subagent invocations
    timeout_default: int             # Default timeout in seconds


PLATFORM_CAPABILITY_MAP: dict[str, PlatformCapabilities] = {
    # openclaw: KNOWN — verified via /openclaw/openclaw docs
    "openclaw": PlatformCapabilities(
        platform="openclaw",
        supports_parallel=True,
        supports_streaming=False,
        supports_structured_output=True,
        supports_toolsets=True,
        max_concurrent=3,
        timeout_default=120,
    ),
    # hermes: ASSUMED — capability research deferred to Phase 27+
    "hermes": PlatformCapabilities(
        platform="hermes",
        supports_parallel=True,
        supports_streaming=False,
        supports_structured_output=True,
        supports_toolsets=True,
        max_concurrent=3,
        timeout_default=120,
    ),
    # claude_code: ASSUMED — capability research deferred to Phase 27+
    "claude_code": PlatformCapabilities(
        platform="claude_code",
        supports_parallel=True,
        supports_streaming=False,
        supports_structured_output=True,
        supports_toolsets=True,
        max_concurrent=3,
        timeout_default=120,
    ),
    # codex: ASSUMED — capability research deferred to Phase 27+
    "codex": PlatformCapabilities(
        platform="codex",
        supports_parallel=True,
        supports_streaming=False,
        supports_structured_output=False,
        supports_toolsets=False,
        max_concurrent=2,
        timeout_default=120,
    ),
}


OrchestrationStrategy = Literal["sequential", "council", "parallel"]


def get_platform_capabilities(platform: str) -> PlatformCapabilities | None:
    """Get capabilities for a platform.

    Returns None if platform is unknown.
    """
    return PLATFORM_CAPABILITY_MAP.get(platform)


def select_orchestration_strategy(
    expert_count: int,
    platforms: list[str],
    force: OrchestrationStrategy | None = None
) -> OrchestrationStrategy:
    """Select optimal orchestration strategy based on expert count and platform capabilities.

    Rules:
    - 1 expert: always sequential
    - 2 experts: sequential (safer, lower token cost)
    - 3+ experts: council if all platforms support parallel, else sequential
    - force parameter overrides automatic selection

    Per AA-01-PLAN.md Section 5: Pattern Selection Matrix.
    Per OpenCode review concern LOW-09: capability-based strategy selection.
    """
    if force:
        return force

    if expert_count == 1:
        return "sequential"

    if expert_count == 2:
        return "sequential"

    # 3+ experts: check if all platforms support parallel
    if expert_count >= 3:
        all_support_parallel = all(
            PLATFORM_CAPABILITY_MAP.get(p, PLATFORM_CAPABILITY_MAP["openclaw"]).supports_parallel
            for p in platforms
        )
        if all_support_parallel:
            return "council"

    return "sequential"

# STAT-01: Four-lens keyword sets for account posture derivation
_STAT_RISK_KEYWORDS = {"风险", "预警", "下降", "流失", "竞品", "问题", "挑战", "障碍", "下滑", "收紧", "压力", "危机", "逾期", "负向"}
_STAT_OPPORTUNITY_KEYWORDS = {"机会", "扩张", "增加", "扩容", "新客", "开拓", "增长", "潜力", "空间", "上行", "突破", "拓展", "增量", "机会点"}
_STAT_RELATIONSHIP_KEYWORDS = {"关系", "信任", "合作", "沟通", "对接", "联系", "配合", "协同", "维护", "深化"}
_STAT_PROJECT_PROGRESS_KEYWORDS = {"进展", "进度", "完成", "交付", "里程碑", "阶段", "推进", "落地", "执行", "状态"}

# ARCH-01: Five-dimension keyword sets for archive refresh derivation (per D-01, D-02)
_ARCH_HISTORY_KEYWORDS = {"历史", "过去", "此前", "之前", "历年", "历程", "往日", "以往", "先前"}
_ARCH_PEOPLE_KEYWORDS = {"关键人物", "负责人", "决策人", "接口人", "干系人", "对接人", "联系人", "主要联系人"}
_ARCH_RISK_KEYWORDS = {"风险", "预警", "下降", "流失", "竞品", "问题", "挑战", "障碍", "下滑", "危机", "逾期", "负向", "压力", "风险点"}
_ARCH_OPPORTUNITY_KEYWORDS = {"机会", "扩张", "增加", "扩容", "新客", "开拓", "增长", "潜力", "空间", "上行", "突破", "拓展", "增量", "机会点", "新增", "上量"}
_ARCH_POSTURE_KEYWORDS = {"姿态", "策略", "方向", "定位", "战略", "打法", "思路", "规划", "计划", "重心"}

# ARCH-01: Source mapping per dimension (per D-19)
_ARCH_LENS_SOURCE_MAP: dict[str, list[str]] = {
    "historical_arc": ["customer_archive", "meeting_notes"],
    "key_people": ["contact_records", "customer_archive"],
    "risk": ["customer_master", "action_plan"],
    "opportunity": ["meeting_notes", "action_plan"],
    "operating_posture": ["customer_master", "action_plan", "meeting_notes"],
}

# PROP-01: Five-dimension keyword sets for proposal/report/resource-coordination derivation (per D-06)
_PROPOSAL_OBJECTIVE_KEYWORDS = {"目标", "目的", "意图", "期望", "想要达成", "规划"}
_PROPOSAL_JUDGMENT_KEYWORDS = {"判断", "评估", "结论", "认为", "核心是", "关键点", "重点"}
_PROPOSAL_NARRATIVE_KEYWORDS = {"叙事", "说明", "阐述", "背景", "情况", "现状", "原因", "历程"}
_PROPOSAL_RESOURCE_KEYWORDS = {"资源", "支持", "协助", "需要", "请求", "投入", "预算", "人力", "时间", "资源需求"}
_PROPOSAL_QUESTION_KEYWORDS = {"待确认", "待定", "不确定", "需确认", "疑问", "问题", "待解决"}

# PROP-01: Source mapping per dimension (per D-05)
_PROPOSAL_LENS_SOURCE_MAP: dict[str, list[str]] = {
    "objective": ["customer_master", "meeting_notes"],
    "core_judgment": ["customer_master", "action_plan", "meeting_notes"],
    "main_narrative": ["meeting_notes", "customer_archive", "action_plan"],
    "resource_asks": ["action_plan", "meeting_notes"],
    "open_questions": ["customer_archive", "contact_records"],
}


def _derive_account_posture_lenses(
    evidence_container: Any,
) -> dict[str, list[str]]:
    """Derive four account-posture lenses from evidence container.

    Returns dict with keys: risk, opportunity, relationship, project_progress.
    Each value is 1-3 scannable conclusions (keywords found in source text).
    Uses keyword-based extraction (no LLM inference).

    Per D-10: lens conclusions are traceable to EvidenceContainer sources.
    """
    from runtime.expert_analysis_helper import LENS_SOURCE_MAP

    if evidence_container is None:
        return {"risk": [], "opportunity": [], "relationship": [], "project_progress": []}

    lens_texts: dict[str, list[str]] = {
        "risk": [], "opportunity": [], "relationship": [], "project_progress": []
    }
    for lens_name, source_names in LENS_SOURCE_MAP.items():
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
        "risk": _extract(combined.get("risk", ""), _STAT_RISK_KEYWORDS),
        "opportunity": _extract(combined.get("opportunity", ""), _STAT_OPPORTUNITY_KEYWORDS),
        "relationship": _extract(combined.get("relationship", ""), _STAT_RELATIONSHIP_KEYWORDS),
        "project_progress": _extract(combined.get("project_progress", ""), _STAT_PROJECT_PROGRESS_KEYWORDS),
    }


def _derive_proposal_lenses(
    evidence_container: Any,
) -> dict[str, list[str]]:
    """Derive five proposal lenses from evidence container.

    Returns dict with keys: objective, core_judgment, main_narrative, resource_asks, open_questions.
    Each value is 1-3 scannable conclusions (keywords found in source text).
    Uses keyword-based extraction (no LLM inference).

    Per D-10: lens conclusions are traceable to EvidenceContainer sources.
    Per D-09: independent judgment logic at proposal scene layer — not shared with Phase 17/18/19.
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


def _render_proposal_output(
    lens_results: dict[str, list[str]],
    proposal_type: str,
) -> list[str]:
    """Render five-dimension proposal output per D-06, D-07.

    Type-specific emphasis per D-07:
      - proposal: emphasizes core_judgment + main_narrative
      - report: emphasizes main_narrative
      - resource-coordination: emphasizes resource_asks
    """
    lines = ["--- 提案/报告/资源协调草案 ---"]

    # Objective (1-2 sentences, max 2 items per D-06)
    lines.append("目的:")
    obj_items = lens_results.get("objective", [])
    if obj_items:
        for item in obj_items[:2]:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无目的信息")

    # Core Judgment (emphasized for proposal type, max 4 items per D-06)
    lines.append("核心判断:")
    judgment_items = lens_results.get("core_judgment", [])
    if proposal_type == "proposal":
        max_judgments = 4
    else:
        max_judgments = 3
    if judgment_items:
        for item in judgment_items[:max_judgments]:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无核心判断")

    # Main Narrative (emphasized for report type, max 3 items per D-06)
    lines.append("主要叙事:")
    narrative_items = lens_results.get("main_narrative", [])
    if proposal_type == "report":
        max_narrative = 3
    else:
        max_narrative = 2
    if narrative_items:
        for item in narrative_items[:max_narrative]:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无叙事内容")

    # Resource Asks (emphasized for resource-coordination type, max 3 items per D-06)
    lines.append("资源请求:")
    resource_items = lens_results.get("resource_asks", [])
    if proposal_type == "resource-coordination":
        max_resource = 4
    else:
        max_resource = 2
    if resource_items:
        for item in resource_items[:max_resource]:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无资源请求")

    # Open Questions (max 3 items per D-06)
    lines.append("待确认问题:")
    question_items = lens_results.get("open_questions", [])
    if question_items:
        for item in question_items[:3]:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无待确认问题")

    return lines


def _infer_proposal_output_destination(
    evidence_container: Any,
    proposal_type: str,
) -> str:
    """Infer default output destination based on proposal_type per D-12.

    Per D-12: Default routing by proposal type:
      - proposal -> Drive customer archive folder
      - report -> Drive customer archive folder or weekly-report folder
      - resource-coordination -> Task module or Base 行动计划 table

    Returns a human-readable destination string for the confirmation checklist.
    """
    if proposal_type in ("proposal", "report"):
        # Route to Drive folder
        if evidence_container:
            arch_src = evidence_container.sources.get("customer_archive")
            if arch_src and arch_src.available:
                archive_name = arch_src.raw_data.get("name", "客户档案文件夹")
                return f"Drive 已有档案: {archive_name}"
        return "Drive 客户档案文件夹"
    else:
        # resource-coordination -> Task or Base 行动计划
        return "Base 行动计划表 / Task"


def _extract_action_items_from_proposal(
    lens_results: dict[str, list[str]],
    proposal_type: str,
) -> list[dict[str, str]]:
    """Extract action items from proposal lens results for Base/Task write.

    Per D-10: resource-coordination type routes to Base 行动计划 table or Task module.
    Only extracts from resource_asks and open_questions for action item creation.

    Returns list of action item dicts with keys: subject, description, due_date (optional).
    """
    action_items = []

    if proposal_type != "resource-coordination":
        return action_items

    # Extract from resource_asks
    resource_items = lens_results.get("resource_asks", [])
    for item in resource_items[:3]:
        action_items.append({
            "subject": f"资源协调: {item}",
            "description": item,
        })

    # Extract from open_questions
    question_items = lens_results.get("open_questions", [])
    for item in question_items[:2]:
        action_items.append({
            "subject": f"待确认: {item}",
            "description": item,
        })

    return action_items


def _build_proposal_routing_payload(
    proposal_type: str,
    confirmed_destination: str,
    lens_results: dict[str, list[str]],
    customer_info: dict[str, Any],
) -> dict[str, Any]:
    """Build routing payload for proposal output per D-11, D-12.

    Per D-11: Routing is recommendation + confirmation (same as Phase 19 WRITE-02 pattern).
    Per D-12: Default routing by type — proposal/report to Drive, resource-coordination to Base/Task.

    Returns routing payload dict with destination_type, target, content summary.
    """
    output_content = "\n".join([
        "目的:",
        *lens_results.get("objective", ["- 暂无目的信息"]),
        "",
        "核心判断:",
        *lens_results.get("core_judgment", ["- 暂无核心判断"]),
        "",
        "主要叙事:",
        *lens_results.get("main_narrative", ["- 暂无叙事内容"]),
        "",
        "资源请求:",
        *lens_results.get("resource_asks", ["- 暂无资源请求"]),
        "",
        "待确认问题:",
        *lens_results.get("open_questions", ["- 暂无待确认问题"]),
    ])

    if proposal_type in ("proposal", "report"):
        # Drive routing
        return {
            "destination_type": "drive_doc",
            "target": confirmed_destination,
            "content": output_content,
            "customer": customer_info,
            "doc_type": "proposal" if proposal_type == "proposal" else "report",
        }
    else:
        # Resource-coordination: Base table or Task
        action_items = _extract_action_items_from_proposal(lens_results, proposal_type)
        return {
            "destination_type": "base_table" if action_items else "task",
            "target": "行动计划" if action_items else "task",
            "content": output_content,
            "action_items": action_items,
            "customer": customer_info,
        }


def _render_four_lens_judgments(lens_results: dict[str, list[str]]) -> list[str]:
    """Render four-lens results as labeled sub-items within judgments field.

    Format per D-01: "风险: <conclusion1>; <conclusion2>" etc.
    Returns list of judgment strings, one per lens that has conclusions.
    """
    labels = {
        "risk": "风险",
        "opportunity": "机会",
        "relationship": "关系",
        "project_progress": "进展",
    }
    judgments: list[str] = []
    for lens_key, label in labels.items():
        conclusions = lens_results.get(lens_key, [])
        if conclusions:
            judgments.append(f"{label}: {'; '.join(conclusions)}")
    return judgments


def _derive_archive_refresh_lenses(
    evidence_container: Any,
) -> dict[str, list[str]]:
    """Derive five archive-refresh lenses from evidence container.

    Returns dict with keys: historical_arc, key_people, risk, opportunity, operating_posture.
    Each value is 1-3 scannable conclusions (keywords found in source text).
    Uses keyword-based extraction (no LLM inference).

    Per D-01, D-02: each dimension produces 1-3 scannable conclusions.
    """
    if evidence_container is None:
        return {k: [] for k in _ARCH_LENS_SOURCE_MAP.keys()}

    lens_texts: dict[str, list[str]] = {k: [] for k in _ARCH_LENS_SOURCE_MAP.keys()}
    for lens_name, source_names in _ARCH_LENS_SOURCE_MAP.items():
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
        "historical_arc": _extract(combined.get("historical_arc", ""), _ARCH_HISTORY_KEYWORDS),
        "key_people": _extract(combined.get("key_people", ""), _ARCH_PEOPLE_KEYWORDS),
        "risk": _extract(combined.get("risk", ""), _ARCH_RISK_KEYWORDS),
        "opportunity": _extract(combined.get("opportunity", ""), _ARCH_OPPORTUNITY_KEYWORDS),
        "operating_posture": _extract(combined.get("operating_posture", ""), _ARCH_POSTURE_KEYWORDS),
    }


def _render_archive_refresh_output(lens_results: dict[str, list[str]]) -> list[str]:
    """Render five-dimension archive refresh output per D-01, D-02.

    Format:
    --- 档案更新建议 ---
    历史弧线:
    - {1-3 items}
    关键人物:
    - {1-3 items}
    风险:
    - {1-3 items}
    机会:
    - {1-3 items}
    运营姿态:
    - {1-3 items}

    Per D-02: each dimension produces 1-3 scannable conclusions, labeled and readable.
    """
    dimension_labels = {
        "historical_arc": "历史弧线",
        "key_people": "关键人物",
        "risk": "风险",
        "opportunity": "机会",
        "operating_posture": "运营姿态",
    }
    lines = ["--- 档案更新建议 ---"]
    for key, label in dimension_labels.items():
        conclusions = lens_results.get(key, [])
        if conclusions:
            lines.append(f"{label}: {', '.join(conclusions[:3])}")
        else:
            lines.append(f"{label}: 暂无结论")
    return lines


def _render_meeting_prep_output(
    stat01_lens_results: dict[str, list[str]],
    key_people_items: list[str],
    meeting_objectives: list[str],
    risk_items: list[str],
    opportunity_items: list[str],
    suggested_questions: list[str],
    suggested_next_steps: list[str],
) -> list[str]:
    """Render seven-dimension meeting prep output per D-07, D-08.

    Format:
    --- 会前准备简报 ---
    当前状态: (reuses STAT-01 four-lens output)
      风险: {keyword conclusions}
      机会: {keyword conclusions}
      关系: {keyword conclusions}
      进展: {keyword conclusions}
    关键人物:
    - {name} | {role} | {relationship}
    目的:
    - {meeting objectives}
    风险:
    - {1-3 items}
    机会:
    - {1-3 items}
    建议问题:
    - {1-3 questions}
    建议后续步骤:
    - {1-3 steps}

    Per D-08: 当前状态 dimension reuses STAT-01 four-lens output directly.
    """
    lines = ["--- 会前准备简报 ---", "当前状态:"]
    # STAT-01 four lenses reused per D-08
    lines.append(f"  风险: {', '.join(stat01_lens_results.get('risk', [])[:3]) or '暂无风险信号'}")
    lines.append(f"  机会: {', '.join(stat01_lens_results.get('opportunity', [])[:3]) or '暂无机会信号'}")
    lines.append(f"  关系: {', '.join(stat01_lens_results.get('relationship', [])[:3]) or '暂无关系信号'}")
    lines.append(f"  进展: {', '.join(stat01_lens_results.get('project_progress', [])[:3]) or '暂无进展信号'}")

    # 关键人物
    lines.append("关键人物:")
    if key_people_items:
        for item in key_people_items[:3]:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无关键人物信息")

    # 目的
    lines.append("目的:")
    if meeting_objectives:
        for obj in meeting_objectives[:3]:
            lines.append(f"- {obj}")
    else:
        lines.append("- 暂无会议目的信息")

    # 风险
    lines.append("风险:")
    if risk_items:
        for item in risk_items[:3]:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无风险信息")

    # 机会
    lines.append("机会:")
    if opportunity_items:
        for item in opportunity_items[:3]:
            lines.append(f"- {item}")
    else:
        lines.append("- 暂无机会信息")

    # 建议问题
    lines.append("建议问题:")
    if suggested_questions:
        for q in suggested_questions[:3]:
            lines.append(f"- {q}")
    else:
        lines.append("- 暂无建议问题")

    # 建议后续步骤
    lines.append("建议后续步骤:")
    if suggested_next_steps:
        for step in suggested_next_steps[:3]:
            lines.append(f"- {step}")
    else:
        lines.append("- 暂无建议后续步骤")

    return lines


SceneFallbackCategory = Literal[
    "none",
    "customer",
    "context",
    "permission",
    "validation",
    "safety",
]

STANDARD_SCENE_RESULT_FIELDS = frozenset(
    {
        "scene_name",
        "resource_status",
        "customer_status",
        "context_status",
        "used_sources",
        "facts",
        "judgments",
        "open_questions",
        "recommendations",
        "fallback_category",
        "fallback_reason",
        "fallback_message",
        "write_ceiling",
        "output_text",
    }
)


@dataclass
class SceneRequest:
    scene_name: str
    repo_root: Path
    customer_query: str
    inputs: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class SceneResult:
    scene_name: str
    resource_status: str
    customer_status: str
    context_status: str
    write_ceiling: str
    used_sources: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    judgments: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    fallback_category: SceneFallbackCategory = "none"
    fallback_reason: str | None = None
    fallback_message: str | None = None
    output_text: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def structured_result(self) -> dict[str, Any]:
        result = {
            "scene_name": self.scene_name,
            "resource_status": self.resource_status,
            "customer_status": self.customer_status,
            "context_status": self.context_status,
            "used_sources": list(self.used_sources),
            "facts": list(self.facts),
            "judgments": list(self.judgments),
            "open_questions": list(self.open_questions),
            "recommendations": list(self.recommendations),
            "fallback_category": self.fallback_category,
            "fallback_reason": self.fallback_reason,
            "fallback_message": self.fallback_message,
            "write_ceiling": self.write_ceiling,
            "output_text": self.output_text,
        }
        collision_payload: dict[str, Any] = {}
        for key, value in self.payload.items():
            if key in STANDARD_SCENE_RESULT_FIELDS:
                collision_payload[key] = deepcopy(value)
                continue
            result[key] = deepcopy(value)
        if collision_payload:
            scene_payload = result.get("scene_payload")
            if not isinstance(scene_payload, dict):
                scene_payload = {} if scene_payload is None else {"value": deepcopy(scene_payload)}
            scene_payload["reserved_payload_fields"] = collision_payload
            result["scene_payload"] = scene_payload
        return result

    def render_text(self) -> str:
        return self.output_text


def _build_live_scene_context(
    request: SceneRequest,
    *,
    topic_text: str = "",
) -> tuple[Any, Any]:
    from evals.meeting_output_bridge import recover_live_context

    repo_root = request.repo_root.expanduser()
    gateway = FeishuWorkbenchGateway.for_live_lark_cli(str(repo_root))
    sources = RuntimeSourceLoader(repo_root).load()
    query_backend = LarkCliBaseQueryBackend(
        LarkCliClient(),
        LiveWorkbenchConfig.from_sources(sources),
    )
    gateway_result = gateway.run(customer_query=request.customer_query)
    recovery = recover_live_context(
        gateway_result=gateway_result,
        query_backend=query_backend,
        topic_text=topic_text,
    )
    return gateway_result, recovery


def _normalize_scene_path(raw_path: Any, repo_root: Path) -> Path:
    path = Path(str(raw_path)).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path


def _build_context_result(
    *,
    request: SceneRequest,
    gateway_result: Any,
    recovery: Any,
    facts: list[str],
    judgments: list[str],
    open_questions: list[str],
    recommendations: list[str],
    output_text: str,
    payload: dict[str, Any] | None = None,
    write_ceiling: str | None = None,
) -> SceneResult:
    resource_status = gateway_result.resource_resolution.status
    customer_resolution = gateway_result.customer_resolution
    customer_status = customer_resolution.status if customer_resolution is not None else "missing"
    effective_write_ceiling = write_ceiling or recovery.write_ceiling
    fallback_category, fallback_message = _classify_fallback(
        customer_status=customer_status,
        context_status=recovery.status,
        fallback_reason=recovery.fallback_reason,
        write_ceiling=effective_write_ceiling,
    )
    return SceneResult(
        scene_name=request.scene_name,
        resource_status=resource_status,
        customer_status=customer_status,
        context_status=recovery.status,
        used_sources=list(recovery.used_sources),
        facts=facts,
        judgments=judgments,
        open_questions=open_questions,
        recommendations=recommendations,
        fallback_category=fallback_category,
        fallback_reason=recovery.fallback_reason,
        fallback_message=fallback_message,
        write_ceiling=effective_write_ceiling,
        output_text=output_text,
        payload=payload or {},
    )


def run_post_meeting_scene(request: SceneRequest) -> SceneResult:
    from evals.meeting_output_bridge import (
        build_meeting_output_artifact,
        build_meeting_todo_candidates,
        recover_live_context,
        run_confirmed_todo_write,
    )
    from runtime.expert_card_loader import load_expert_cards

    # AGENT-02: Load expert cards at start (interface contract step 1)
    expert_cards = load_expert_cards(request.scene_name, request.repo_root)
    input_audit_result: Any = None
    output_audit_result: Any = None

    repo_root = request.repo_root.expanduser()
    transcript_file = _normalize_scene_path(request.inputs["transcript_file"], repo_root)
    eval_name = str(request.inputs["eval_name"])
    action_items = list(request.inputs.get("action_items") or [])
    confirm_write = bool(request.options.get("confirm_write", False))

    gateway = FeishuWorkbenchGateway.for_live_lark_cli(str(repo_root))
    sources = RuntimeSourceLoader(repo_root).load()
    query_backend = LarkCliBaseQueryBackend(
        LarkCliClient(),
        LiveWorkbenchConfig.from_sources(sources),
    )

    gateway_result = gateway.run(customer_query=request.customer_query)
    recovery = recover_live_context(
        gateway_result=gateway_result,
        query_backend=query_backend,
        topic_text=transcript_file.stem,
    )
    candidates = build_meeting_todo_candidates(
        eval_name=eval_name,
        gateway_result=gateway_result,
        action_items=action_items or None,
    )

    write_results: list[WriteExecutionResult] = []
    if confirm_write and candidates:
        todo_writer = TodoWriter.for_live_lark_cli(str(repo_root))
        write_results = run_confirmed_todo_write(
            candidates=candidates,
            todo_writer=todo_writer,
        )

    evidence_container = getattr(recovery, 'evidence_container', None)

    # AGENT-02: Input audit before evidence assembly (interface contract step 2)
    if expert_cards["input_review"] and expert_cards["input_review"].enabled:
        from runtime.expert_analysis_helper import run_input_audit
        input_audit_result = run_input_audit(evidence_container, expert_cards["input_review"])

    artifact = build_meeting_output_artifact(
        eval_name=eval_name,
        transcript_path=transcript_file,
        gateway_result=gateway_result,
        recovery=recovery,
        write_results=write_results,
        evidence_container=evidence_container,
    )

    resource_status = gateway_result.resource_resolution.status
    customer_resolution = gateway_result.customer_resolution
    customer_status = customer_resolution.status if customer_resolution is not None else "missing"
    facts = list(recovery.key_context)
    open_questions = [*recovery.open_questions, *recovery.candidate_conflicts]
    recommendations = [
        str(candidate.payload.get("summary") or "")
        for candidate in candidates
        if str(candidate.payload.get("summary") or "").strip()
    ]
    fallback_category, fallback_message = _classify_fallback(
        customer_status=customer_status,
        context_status=recovery.status,
        fallback_reason=recovery.fallback_reason,
        write_ceiling=recovery.write_ceiling,
    )

    # AGENT-02: Output audit before SceneResult returned (interface contract step 4)
    if expert_cards["output_review"] and expert_cards["output_review"].enabled:
        from runtime.expert_analysis_helper import run_output_audit
        output_audit_result = run_output_audit(recommendations, expert_cards["output_review"])

    return SceneResult(
        scene_name=request.scene_name,
        resource_status=resource_status,
        customer_status=customer_status,
        context_status=recovery.status,
        used_sources=list(recovery.used_sources),
        facts=facts,
        judgments=[],
        open_questions=open_questions,
        recommendations=recommendations,
        fallback_category=fallback_category,
        fallback_reason=recovery.fallback_reason,
        fallback_message=fallback_message,
        write_ceiling=recovery.write_ceiling,
        output_text=str(artifact["output_text"]),
        payload={
            "candidate_count": len(candidates),
            "candidates": [_serialize_candidate(candidate) for candidate in candidates],
            "write_result_details": deepcopy(artifact["write_result_details"]),
            "scene_payload": {
                "meeting_eval": eval_name,
                "transcript_file": transcript_file.name,
            },
            # AGENT-02: Expert card audit results in payload
            "input_audit_result": input_audit_result,
            "output_audit_result": output_audit_result,
        },
    )


def _serialize_candidate(candidate: Any) -> dict[str, Any]:
    return {
        "target_object": candidate.target_object,
        "operation": candidate.operation,
        "payload": dict(candidate.payload),
        "match_basis": dict(candidate.match_basis),
        "source_context": dict(candidate.source_context),
    }


def run_customer_recent_status_scene(request: SceneRequest) -> SceneResult:
    from runtime.expert_analysis_helper import build_lens_attributions
    from runtime.expert_card_loader import load_expert_cards

    # AGENT-02: Load expert cards at start (interface contract step 1)
    expert_cards = load_expert_cards(request.scene_name, request.repo_root)
    input_audit_result: Any = None

    topic_text = str(request.inputs.get("topic_text") or "")
    gateway_result, recovery = _build_live_scene_context(request, topic_text=topic_text)
    facts = list(recovery.key_context)
    judgments: list[str] = []
    if recovery.status == "completed":
        judgments.append("当前客户近期状态已有足够 live 证据，可继续输出经营判断。")
    else:
        judgments.append("当前客户近期状态仍有上下文缺口，判断应保持 recommendation-first。")
    if recovery.candidate_conflicts:
        judgments.append("部分档案或会议证据存在冲突，近期状态需要人工复核后再沉淀。")
    elif recovery.write_ceiling == "normal":
        judgments.append("当前证据链没有触发额外 safety downgrade。")

    # STAT-01: Derive four-lens account posture judgments from evidence container
    evidence_container = getattr(recovery, 'evidence_container', None)
    lens_results = _derive_account_posture_lenses(evidence_container)
    four_lens_judgments = _render_four_lens_judgments(lens_results)
    judgments.extend(four_lens_judgments)

    open_questions = [*recovery.open_questions, *recovery.candidate_conflicts]
    recommendations: list[str] = []
    if recovery.missing_sources:
        recommendations.append(
            f"优先补齐 {'、'.join(recovery.missing_sources)} 后再更新客户最近状态。"
        )
    if recovery.candidate_conflicts:
        recommendations.append("先确认档案或会议纪要候选，再决定是否沉淀为正式客户状态结论。")
    if not recommendations:
        recommendations.append("基于当前 live 上下文整理一版客户最近状态结论，供后续会前/会后复用。")

    # Build lens attributions for traceability per D-10
    lens_attributions = build_lens_attributions(evidence_container, lens_results) if evidence_container else []

    lines = [
        f"资源解析状态: {gateway_result.resource_resolution.status}",
        f"客户解析状态: {_render_customer_status(gateway_result)}",
        f"场景上下文状态: {recovery.status}",
        f"写回上限: {recovery.write_ceiling}",
    ]
    if facts:
        lines.append("事实:")
        lines.extend(f"- {item}" for item in facts)
    if judgments:
        lines.append("判断:")
        lines.extend(f"- {item}" for item in judgments)
    if open_questions:
        lines.append("开放问题:")
        lines.extend(f"- {item}" for item in open_questions)
    if recommendations:
        lines.append("建议:")
        lines.extend(f"- {item}" for item in recommendations)

    # AGENT-02: Input audit before _build_context_result (input only, no output per expert-cards.yaml)
    if expert_cards["input_review"] and expert_cards["input_review"].enabled:
        from runtime.expert_analysis_helper import run_input_audit
        input_audit_result = run_input_audit(evidence_container, expert_cards["input_review"])

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
                "topic_text": topic_text,
                "missing_sources": list(recovery.missing_sources),
                "candidate_conflicts": list(recovery.candidate_conflicts),
                "evidence_container": evidence_container,
                "lens_attributions": lens_attributions,
            },
            # AGENT-02: Expert card audit result in payload
            "input_audit_result": input_audit_result,
        },
    )


def run_archive_refresh_scene(request: SceneRequest) -> SceneResult:
    topic_text = str(request.inputs.get("topic_text") or "客户档案")
    gateway_result, recovery = _build_live_scene_context(request, topic_text=topic_text)
    facts = list(recovery.key_context)
    has_archive_anchor = any("客户档案" in item for item in facts)
    judgments: list[str] = []
    if has_archive_anchor:
        judgments.append("当前 archive refresh 已有可定位的客户档案锚点。")
    else:
        judgments.append("当前还没有稳定的客户档案锚点，archive refresh 只能停留在候选确认。")
    if recovery.candidate_conflicts:
        judgments.append("档案候选存在冲突或弱证据，refresh 不能直接进入正式沉淀。")

    # ARCH-01: Derive five-dimension lenses from evidence container
    evidence_container = getattr(recovery, 'evidence_container', None)
    lens_results = _derive_archive_refresh_lenses(evidence_container)

    # D-10: Build and render confirmation checklist BEFORE scene output
    checklist = build_archive_refresh_checklist(evidence_container, recovery)
    checklist_output = render_confirmation_checklist(checklist)

    archive_refresh_lines = _render_archive_refresh_output(lens_results)

    open_questions = [*recovery.open_questions, *recovery.candidate_conflicts]
    recommendations: list[str] = []
    if has_archive_anchor and not recovery.candidate_conflicts:
        recommendations.append("以当前客户档案锚点为主，整理需要补充到 archive 的最近进展和行动变化。")
    if "客户档案" in recovery.missing_sources or not has_archive_anchor:
        recommendations.append("先补齐 canonical archive 链接或确认档案候选，再执行 refresh。")
    if recovery.candidate_conflicts:
        recommendations.append("先确认 canonical archive，再决定是否把 refresh 结果当作正式客户事实沉淀。")
    if not recommendations:
        recommendations.append("当前 archive 视角已足够作为 refresh 建议输入，但后续写回仍需走现有共享安全路径。")

    # Build output: checklist shown first per D-10, then five-dimension archive refresh
    lines = checklist_output + archive_refresh_lines + [
        f"资源解析状态: {gateway_result.resource_resolution.status}",
        f"客户解析状态: {_render_customer_status(gateway_result)}",
        f"场景上下文状态: {recovery.status}",
        f"写回上限: {recovery.write_ceiling}",
    ]
    if facts:
        lines.append("事实:")
        lines.extend(f"- {item}" for item in facts)
    if judgments:
        lines.append("判断:")
        lines.extend(f"- {item}" for item in judgments)
    if open_questions:
        lines.append("开放问题:")
        lines.extend(f"- {item}" for item in open_questions)
    if recommendations:
        lines.append("建议:")
        lines.extend(f"- {item}" for item in recommendations)

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
                "topic_text": topic_text,
                "archive_refresh_lenses": lens_results,
                "confirmation_checklist_output": checklist_output,
                "confirmed_answers": checklist.confirmed_answers(),
                "archive_anchor_ready": has_archive_anchor,
                "missing_sources": list(recovery.missing_sources),
                "candidate_conflicts": list(recovery.candidate_conflicts),
                "evidence_container": evidence_container,
            }
        },
    )


def run_meeting_prep_scene(request: SceneRequest) -> SceneResult:
    """Meeting prep scene — produces seven-dimension recommendation-first brief.

    Per D-07: Seven dimensions — 当前状态, 关键人物, 目的, 风险, 机会, 建议问题, 建议后续步骤.
    Per D-08: 当前状态 dimension reuses STAT-01 four-lens output when available.
    Per D-09: New standalone scene registers as 'meeting-prep' in scene registry.
    Per D-10: Confirmation checklist is shown BEFORE scene executes.

    Uses _build_live_scene_context() for evidence assembly and
    _derive_account_posture_lenses() for STAT-01 four-lens reuse.
    """
    topic_text = str(request.inputs.get("topic_text") or "")
    gateway_result, recovery = _build_live_scene_context(request, topic_text=topic_text)
    facts = list(recovery.key_context)

    # D-08: Reuse STAT-01 four-lens for 当前状态 dimension
    evidence_container = getattr(recovery, 'evidence_container', None)
    stat01_lens_results = _derive_account_posture_lenses(evidence_container)

    # Build seven-dimension synthesis from evidence
    # Key people: extract from contact_records
    key_people_items: list[str] = []
    if evidence_container:
        contact_src = evidence_container.sources.get("contact_records")
        if contact_src and contact_src.available and contact_src.content:
            for content in contact_src.content[:5]:
                if any(kw in content for kw in ["负责人", "决策人", "接口人", "关键人物", "联系人"]):
                    key_people_items.append(content)

    # Meeting objectives: from user inputs or inferred
    meeting_objectives = []
    if request.inputs.get("meeting_type"):
        meeting_objectives.append(f"会议类型: {request.inputs.get('meeting_type')}")
    if request.inputs.get("agenda"):
        agenda = request.inputs.get("agenda")
        if isinstance(agenda, list):
            meeting_objectives.extend([str(a) for a in agenda[:3]])
        else:
            meeting_objectives.append(str(agenda))

    # Risk items: from customer_master and action_plan
    risk_items = list(stat01_lens_results.get("risk", []))[:3]

    # Opportunity items: from meeting_notes and action_plan
    opportunity_items = list(stat01_lens_results.get("opportunity", []))[:3]

    # Suggested questions: derived from gaps (open questions and missing sources)
    suggested_questions = []
    if recovery.open_questions:
        for q in recovery.open_questions[:2]:
            suggested_questions.append(f"确认: {q}")
    if recovery.missing_sources:
        suggested_questions.append(f"待补齐: {', '.join(list(recovery.missing_sources)[:2])}")

    # Suggested next steps: from recommendations in evidence
    suggested_next_steps = []
    if recovery.missing_sources:
        suggested_next_steps.append(f"优先补齐 {', '.join(list(recovery.missing_sources)[:2])}")
    if key_people_items:
        suggested_next_steps.append("确认关键人物信息和联系方式")

    # Build judgments
    judgments: list[str] = []
    if recovery.status == "completed":
        judgments.append("当前会前准备已有足够 live 证据，可继续输出判断建议。")
    else:
        judgments.append("当前会前准备仍有上下文缺口，判断应保持 recommendation-first。")
    if evidence_container and evidence_container.critical_source_missing:
        judgments.append("关键证据来源缺失，建议优先补齐后再进行会前准备。")

    # Build open questions
    open_questions = list(recovery.open_questions)
    if recovery.candidate_conflicts:
        open_questions.extend(recovery.candidate_conflicts)

    # Build recommendations
    recommendations: list[str] = []
    if not stat01_lens_results.get("risk") and not stat01_lens_results.get("opportunity"):
        recommendations.append("建议先运行客户近期状态(scene: customer-recent-status)获取当前账户姿态。")
    if not key_people_items:
        recommendations.append("建议先确认客户关键人物信息后再进行会前准备。")
    if suggested_next_steps:
        recommendations.extend(suggested_next_steps[:2])

    # D-10: Render confirmation checklist BEFORE scene output
    checklist = build_meeting_prep_checklist(evidence_container, recovery)
    checklist_output = render_confirmation_checklist(checklist)

    # Render seven-dimension output
    output_lines = _render_meeting_prep_output(
        stat01_lens_results=stat01_lens_results,
        key_people_items=key_people_items,
        meeting_objectives=meeting_objectives,
        risk_items=risk_items,
        opportunity_items=opportunity_items,
        suggested_questions=suggested_questions,
        suggested_next_steps=suggested_next_steps,
    )

    # Build output: checklist shown first per D-10, then seven-dimension brief
    lines = checklist_output + output_lines + [
        f"资源解析状态: {gateway_result.resource_resolution.status}",
        f"客户解析状态: {_render_customer_status(gateway_result)}",
        f"场景上下文状态: {recovery.status}",
        f"写回上限: {recovery.write_ceiling}",
    ]
    if facts:
        lines.append("事实:")
        lines.extend(f"- {item}" for item in facts)
    if judgments:
        lines.append("判断:")
        lines.extend(f"- {item}" for item in judgments)
    if open_questions:
        lines.append("开放问题:")
        lines.extend(f"- {item}" for item in open_questions)
    if recommendations:
        lines.append("建议:")
        lines.extend(f"- {item}" for item in recommendations)

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
                "topic_text": topic_text,
                "stat01_lens_results": stat01_lens_results,  # D-08 reuse
                "evidence_container": evidence_container,
                "missing_sources": list(recovery.missing_sources),
                "candidate_conflicts": list(recovery.candidate_conflicts),
                "confirmation_checklist_output": checklist_output,  # D-10
                "confirmed_answers": checklist.confirmed_answers(),  # D-10
            }
        },
    )


def run_proposal_scene(request: SceneRequest) -> SceneResult:
    """Proposal/report/resource-coordination scene — produces five-dimension structured brief.

    Per D-01: Single unified scene with three types differentiated by `proposal_type` parameter.
    Per D-02: Three types share same input structure and five-section output format.
    Per D-03: Scene handler registered as `proposal` in scene_registry.py.
    Per D-04: User explicitly names primary reference materials; system auto-supplements via EvidenceContainer.
    Per D-05: EvidenceContainer presents "I found these materials" before scene execution.
    Per D-06: Fixed five-section output — objective, core judgment, main narrative, resource asks, open questions.
    Per D-07: Type-specific emphasis — proposal emphasizes core judgment + narrative; report emphasizes narrative; resource-coordination emphasizes resource asks.
    Per D-09: Independent judgment logic — not shared with Phase 17/18/19 judgment frameworks.
    Per D-10: Confirmation checklist shown BEFORE scene output.
    Per D-11: Routing is recommendation + confirmation (WRITE-02 pattern).
    Per D-12: Default routing by type — proposal/report to Drive, resource-coordination to Base/Task.
    Per D-19: No agency/autonomous behavior — remains recommendation-first and human-in-the-loop.
    """
    topic_text = str(request.inputs.get("topic_text") or "")
    gateway_result, recovery = _build_live_scene_context(request, topic_text=topic_text)
    facts = list(recovery.key_context)

    # Per D-01, D-02: proposal_type from user input (default proposal)
    proposal_type = str(request.inputs.get("proposal_type") or "proposal")
    if proposal_type not in ("proposal", "report", "resource-coordination"):
        proposal_type = "proposal"

    # Per D-04, D-05: evidence assembly via EvidenceContainer
    evidence_container = getattr(recovery, 'evidence_container', None)

    # Per D-10: Render confirmation checklist BEFORE scene output
    # Per D-14: proposal_type passed to checklist for type-specific suggestion
    checklist = build_proposal_checklist(evidence_container, recovery, proposal_type=proposal_type)
    checklist_output = render_confirmation_checklist(checklist)

    # Per D-06: Derive five-dimension lenses from evidence
    lens_results = _derive_proposal_lenses(evidence_container)

    # Per D-07: Type-specific emphasis in output rendering
    output_lines = _render_proposal_output(lens_results, proposal_type)

    # Per D-11: Build routing payload after confirmation
    confirmed_answers = checklist.confirmed_answers()
    confirmed_destination = confirmed_answers.get(
        "output_destination",
        _infer_proposal_output_destination(evidence_container, proposal_type),
    )

    # Build customer info for routing
    customer_resolution = gateway_result.customer_resolution
    customer_info: dict[str, Any] = {}
    if customer_resolution and customer_resolution.candidates:
        best = customer_resolution.candidates[0]
        customer_info = {
            "customer_id": best.customer_id,
            "short_name": best.short_name,
            "archive_link": getattr(best, "archive_link", None),
        }

    routing_payload = _build_proposal_routing_payload(
        proposal_type=proposal_type,
        confirmed_destination=confirmed_destination,
        lens_results=lens_results,
        customer_info=customer_info,
    )

    # Build judgments per D-09 (independent judgment logic)
    judgments: list[str] = []
    if recovery.status == "completed":
        judgments.append("当前提案准备已有足够 live 证据，可继续输出判断建议。")
    else:
        judgments.append("当前提案准备仍有上下文缺口，判断应保持 recommendation-first。")
    if evidence_container and evidence_container.critical_source_missing:
        judgments.append("关键证据来源缺失，建议优先补齐后再进行提案准备。")

    # Per D-06: Build open questions from missing sources and gaps
    open_questions = list(recovery.open_questions)
    if recovery.missing_sources:
        open_questions.extend([f"待补齐: {s}" for s in list(recovery.missing_sources)[:2]])

    # Build recommendations
    recommendations: list[str] = []
    if not lens_results.get("objective"):
        recommendations.append("建议补充客户目标和意图信息后再生成提案。")
    if not lens_results.get("core_judgment") and not lens_results.get("main_narrative"):
        recommendations.append("建议先确认客户近期动态和历史合作背景。")
    if proposal_type == "resource-coordination" and not lens_results.get("resource_asks"):
        recommendations.append("资源协调类型建议明确资源需求和投入计划。")

    # Per D-11: Add routing recommendation to output
    routing_recommendation = f"建议输出至: {confirmed_destination}"
    if confirmed_answers.get("proposal_type"):
        routing_recommendation += f" (类型: {confirmed_answers.get('proposal_type')})"
    recommendations.insert(0, routing_recommendation)

    # Build output: checklist shown first per D-10, then five-dimension brief
    lines = checklist_output + output_lines + [
        f"资源解析状态: {gateway_result.resource_resolution.status}",
        f"客户解析状态: {_render_customer_status(gateway_result)}",
        f"场景上下文状态: {recovery.status}",
        f"写回上限: {recovery.write_ceiling}",
    ]
    if facts:
        lines.append("事实:")
        lines.extend(f"- {item}" for item in facts)
    if judgments:
        lines.append("判断:")
        lines.extend(f"- {item}" for item in judgments)
    if open_questions:
        lines.append("开放问题:")
        lines.extend(f"- {item}" for item in open_questions)
    if recommendations:
        lines.append("建议:")
        lines.extend(f"- {item}" for item in recommendations)

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
                "topic_text": topic_text,
                "proposal_type": proposal_type,
                "proposal_lenses": lens_results,
                "confirmation_checklist_output": checklist_output,
                "confirmed_answers": confirmed_answers,
                "evidence_container": evidence_container,
                "missing_sources": list(recovery.missing_sources),
                "candidate_conflicts": list(recovery.candidate_conflicts),
                "routing_payload": routing_payload,  # Per D-11
            }
        },
    )


def run_todo_capture_and_update_scene(request: SceneRequest) -> SceneResult:
    from evals.meeting_output_bridge import run_confirmed_todo_write

    topic_text = str(request.inputs.get("topic_text") or "")
    gateway_result, recovery = _build_live_scene_context(request, topic_text=topic_text)
    candidates = _build_follow_on_todo_candidates(request, gateway_result)
    confirm_write = bool(request.options.get("confirm_write", False))

    write_results: list[WriteExecutionResult] = []
    if confirm_write and candidates:
        todo_writer = TodoWriter.for_live_lark_cli(str(request.repo_root.expanduser()))
        write_results = run_confirmed_todo_write(
            candidates=candidates,
            todo_writer=todo_writer,
        )

    facts = list(recovery.key_context)
    judgments: list[str] = []
    if candidates:
        judgments.append("当前 follow-on 信息已整理成可进入统一 Todo path 的候选。")
    else:
        judgments.append("当前没有足够明确的 follow-on 项可转成 Todo candidate。")
    if recovery.write_ceiling == "recommendation-only" or recovery.candidate_conflicts:
        judgments.append("由于 live context 不完整或证据冲突，当前仍应保持 recommendation-first。")

    open_questions = [*recovery.open_questions, *recovery.candidate_conflicts]
    if not candidates:
        open_questions.append("需要提供明确的 follow-on summary/owner/due_at 才能生成 Todo 候选。")

    recommendations = [
        str(candidate.payload.get("summary") or "")
        for candidate in candidates
        if str(candidate.payload.get("summary") or "").strip()
    ]
    if not recommendations:
        recommendations.append("先补充需要沉淀为 Todo 的后续动作，再决定是否确认写回。")

    lines = [
        f"资源解析状态: {gateway_result.resource_resolution.status}",
        f"客户解析状态: {_render_customer_status(gateway_result)}",
        f"场景上下文状态: {recovery.status}",
        f"写回上限: {recovery.write_ceiling}",
        f"候选数量: {len(candidates)}",
    ]
    if facts:
        lines.append("事实:")
        lines.extend(f"- {item}" for item in facts)
    if judgments:
        lines.append("判断:")
        lines.extend(f"- {item}" for item in judgments)
    if open_questions:
        lines.append("开放问题:")
        lines.extend(f"- {item}" for item in open_questions)
    if recommendations:
        lines.append("建议:")
        lines.extend(f"- {item}" for item in recommendations)

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
            "candidate_count": len(candidates),
            "candidates": [_serialize_candidate(candidate) for candidate in candidates],
            "write_result_details": [item.structured_result() for item in write_results],
            "scene_payload": {
                "topic_text": topic_text,
                "missing_sources": list(recovery.missing_sources),
                "candidate_conflicts": list(recovery.candidate_conflicts),
                "evidence_container": getattr(recovery, 'evidence_container', None),
            },
        },
    )


def _build_follow_on_todo_candidates(
    request: SceneRequest,
    gateway_result: Any,
) -> list[Any]:
    resolution = gateway_result.customer_resolution
    if resolution is None or resolution.status != "resolved" or not resolution.candidates:
        return []

    customer = resolution.candidates[0]
    raw_items = list(request.inputs.get("todo_items") or [])
    candidates: list[Any] = []
    for index, item in enumerate(raw_items):
        summary = str(item.get("summary") or item.get("title") or "").strip()
        if not summary:
            continue
        due_at = item.get("due_at")
        payload: dict[str, Any] = {
            "summary": summary,
            "customer": customer.short_name,
            "priority": str(item.get("priority") or "中"),
            "description": str(
                item.get("description")
                or "来自 Todo follow-on scene 的建议态事项；确认后才进入统一写回。"
            ),
        }
        owner = str(item.get("owner") or "").strip()
        if owner:
            payload["owner"] = owner
        if due_at is not None:
            payload["due_at"] = due_at

        candidates.append(
            WriteExecutionCandidate(
                customer=customer,
                index=index,
                payload=payload,
            ).as_write_candidate()
        )
    return candidates


@dataclass
class WriteExecutionCandidate:
    customer: Any
    index: int
    payload: dict[str, Any]

    def as_write_candidate(self) -> Any:
        due_at = self.payload.get("due_at")
        if isinstance(due_at, str) and len(due_at) >= 7:
            time_window = due_at[:7]
        else:
            time_window = "follow_on"
        return WriteCandidate(
            object_name="待办",
            target_object="todo",
            layer="reminder",
            operation="create",
            semantic_fields=["summary", "owner", "customer", "priority", "due_at"],
            payload=dict(self.payload),
            match_basis={
                "customer": self.customer.short_name,
                "time_window": time_window,
                "candidate_index": str(self.index),
            },
            source_context={
                "scenario": "todo_follow_on",
                "customer_id": self.customer.customer_id,
                "scene_name": "todo-capture-and-update",
            },
        )


def _render_customer_status(gateway_result: Any) -> str:
    customer_resolution = gateway_result.customer_resolution
    if customer_resolution is None:
        return "missing"
    if customer_resolution.status == "resolved" and customer_resolution.candidates:
        best = customer_resolution.candidates[0]
        return f"{best.short_name} / 客户ID {best.customer_id or 'missing'}"
    return customer_resolution.status


def _classify_fallback(
    *,
    customer_status: str,
    context_status: str,
    fallback_reason: str | None,
    write_ceiling: str,
) -> tuple[SceneFallbackCategory, str | None]:
    reason = (fallback_reason or "").casefold()
    if customer_status != "resolved":
        return "customer", "客户还没有被唯一确认，当前结果只能先停留在建议层。"
    if not fallback_reason and context_status == "completed" and write_ceiling != "recommendation-only":
        return "none", None
    if "permission" in reason or "scope" in reason or "denied" in reason or "forbidden" in reason:
        return "permission", "当前缺少必要权限或资源可见性，结果只能先停留在建议层。"
    if "schema" in reason or "preflight" in reason or "field" in reason or "validation" in reason:
        return "validation", "实时校验没有通过，当前不能继续推进写回。"
    if "guard" in reason or "protected" in reason or "risk" in reason or "blocked" in reason:
        return "safety", "安全规则拦住了继续执行或写回，当前只保留建议结果。"
    if context_status != "completed" or write_ceiling == "recommendation-only":
        return "context", "现场资料还不够完整，当前结果只能作为建议参考。"
    return "context", "当前结果存在受限条件，请先按 fallback 原因补足信息后再继续。"


def _parse_condition_query(condition_query: str) -> dict[str, Any]:
    """Parse natural language condition into filter criteria.

    Per D-03: user defines cohort via dynamic condition query interpreted into filter criteria.

    Returns dict like:
      {"name_contains": "text"}  or
      {"status": ["active"]}    or
      {"activity_within_days": 90}

    If no specific pattern recognized, returns {"name_contains": condition_query}.
    """
    criteria: dict[str, Any] = {}
    query_lower = condition_query.lower()

    # Activity-based filters
    if "最近" in condition_query or "近" in condition_query:
        import re
        days_match = re.search(r"(\d+)\s*(天|周|个月?)", condition_query)
        if days_match:
            amount, unit = days_match.groups()
            days = int(amount) * {"天": 1, "周": 7, "月": 30, "个月": 30}.get(unit, 1)
            criteria["activity_within_days"] = days

    # Status-based filters
    if "活跃" in condition_query or "active" in query_lower:
        criteria.setdefault("status", []).append("active")
    if "风险" in condition_query or "risk" in query_lower:
        criteria.setdefault("status", []).append("at_risk")
    if "机会" in condition_query or "opportunity" in query_lower:
        criteria.setdefault("status", []).append("opportunity")
    if "扩张" in condition_query or "expanding" in query_lower:
        criteria.setdefault("status", []).append("expanding")

    # Fallback: use full text as text-match filter on customer names
    if not criteria:
        criteria["name_contains"] = condition_query

    return criteria


def _build_cohort_limit_result(
    request: SceneRequest,
    cohort_size: int,
    cohort_limit: int,
    all_customers: list[dict[str, str]],
    condition_query: str,
) -> SceneResult:
    """Return result when cohort size exceeds limit.

    Per D-04: when result set exceeds limit, user is prompted to narrow scope.
    """
    suggestions = [
        f"当前筛选结果包含 {cohort_size} 个客户，已超过单次分析上限 {cohort_limit}。",
        "请缩小范围后重试，例如：",
        "- 指定客户名称关键词（如 'XX 公司'）",
        "- 指定客户状态（如 '风险客户' 或 '机会客户'）",
        f"- 指定时间范围（如 '近 3 个月有活动的客户'）",
    ]
    return SceneResult(
        scene_name=request.scene_name,
        resource_status="resolved",
        customer_status="cohort",
        context_status="completed",
        used_sources=["customer_master"],
        facts=[f"筛选条件: {condition_query}", f"命中客户数: {cohort_size}"],
        judgments=[f"当前Cohort规模 {cohort_size} 超过分析上限 {cohort_limit}，建议缩小范围。"],
        open_questions=[],
        recommendations=[f"请缩小筛选条件后重新发起Cohort扫描（当前上限 {cohort_limit} 客户）"],
        fallback_category="none",
        fallback_reason=None,
        fallback_message=None,
        write_ceiling="recommendation-only",
        output_text="\n".join(suggestions),
        payload={
            "cohort_size": cohort_size,
            "cohort_limit": cohort_limit,
            "condition_query": condition_query,
            "limiting_applied": True,
        },
    )


def _build_empty_cohort_result(request: SceneRequest, condition_query: str) -> SceneResult:
    return SceneResult(
        scene_name=request.scene_name,
        resource_status="resolved",
        customer_status="cohort",
        context_status="completed",
        used_sources=["customer_master"],
        facts=[f"筛选条件: {condition_query}"],
        judgments=["未从客户主数据中获取到任何客户记录。"],
        open_questions=["请检查客户主数据表是否可访问。"],
        recommendations=["确认客户主数据表链接正确且有数据后重试。"],
        fallback_category="none",
        fallback_reason=None,
        fallback_message=None,
        write_ceiling="recommendation-only",
        output_text=f"未找到符合条件的客户记录。筛选条件: {condition_query}",
        payload={"cohort_size": 0, "condition_query": condition_query},
    )


def _aggregate_cohort_signals(customer_lens_results: list[dict[str, Any]]) -> list[str]:
    """Aggregate common positive signals across cohort.

    D-05: 2-3 common signals across the cohort.
    """
    signal_counts: dict[str, int] = {}
    for item in customer_lens_results:
        lens_results = item.get("lens_results", {})
        for lens_key in ["opportunity", "relationship", "project_progress"]:
            for conclusion in lens_results.get(lens_key, []):
                signal_counts[conclusion] = signal_counts.get(conclusion, 0) + 1

    # Return top 3 most common signals appearing in >= 2 customers
    top_signals = sorted(
        [(s, c) for s, c in signal_counts.items() if c >= 2],
        key=lambda x: -x[1]
    )[:3]
    return [s for s, _ in top_signals]


def _aggregate_cohort_issues(customer_lens_results: list[dict[str, Any]]) -> list[str]:
    """Aggregate common issues/risk signals across cohort.

    D-05: 2-3 common issues across the cohort.
    """
    issue_counts: dict[str, int] = {}
    for item in customer_lens_results:
        lens_results = item.get("lens_results", {})
        for conclusion in lens_results.get("risk", []):
            issue_counts[conclusion] = issue_counts.get(conclusion, 0) + 1

    # Return top 3 most common issues appearing in >= 2 customers
    top_issues = sorted(
        [(i, c) for i, c in issue_counts.items() if c >= 2],
        key=lambda x: -x[1]
    )[:3]
    return [i for i, _ in top_issues]


def _select_key_customers(customer_lens_results: list[dict[str, Any]], max_key: int = 5) -> list[dict[str, Any]]:
    """Select top 3-5 customers flagged as highest risk or biggest opportunity.

    D-05: 3-5 customers flagged as highest risk or biggest opportunity.
    Returns list of dicts with customer_record and lens_results.
    """
    scored: list[tuple[int, dict[str, Any]]] = []
    for item in customer_lens_results:
        lens_results = item.get("lens_results", {})
        risk_count = len(lens_results.get("risk", []))
        opp_count = len(lens_results.get("opportunity", []))
        # Score: risk weight 2x opportunity weight
        score = risk_count * 2 + opp_count
        scored.append((score, item))

    scored.sort(key=lambda x: -x[0])
    return [item for _, item in scored[:max_key]]


def _build_cohort_recommendations(
    cohort_signals: list[str],
    cohort_issues: list[str],
    key_customers: list[dict[str, Any]],
) -> list[str]:
    """Build two-tier recommendations capped at ~10 total.

    D-07: cohort-level 1-3 + per-customer 1-2 each (max ~10 total).
    """
    recommendations: list[str] = []

    # Cohort-level recommendations (1-3 items)
    if cohort_issues:
        recommendations.append(f"关注Cohort整体风险: {'; '.join(cohort_issues[:3])}")
    if cohort_signals:
        recommendations.append(f"把握Cohort共同机会: {'; '.join(cohort_signals[:3])}")
    if len(cohort_signals) + len(cohort_issues) < 2:
        recommendations.append("建议深入分析各客户差异以制定差异化策略。")

    # Per-customer recommendations (1-2 per key customer)
    for item in key_customers[:5]:
        customer_record = item.get("customer_record", {})
        name = customer_record.get("简称") or customer_record.get("客户名称", "未知客户")
        lens_results = item.get("lens_results", {})
        risk_items = lens_results.get("risk", [])
        opp_items = lens_results.get("opportunity", [])

        customer_recs: list[str] = []
        if risk_items:
            customer_recs.append(f"风险关注: {'; '.join(risk_items[:2])}")
        if opp_items:
            customer_recs.append(f"机会把握: {'; '.join(opp_items[:2])}")
        if not customer_recs:
            customer_recs.append("维持当前关系维护节奏")

        recommendations.append(f"【{name}】{' | '.join(customer_recs)}")

    # D-08: cap at ~10 total
    return recommendations[:10]


def _render_cohort_output(
    cohort_size: int,
    cohort_signals: list[str],
    cohort_issues: list[str],
    key_customers: list[dict[str, Any]],
    recommendations: list[str],
) -> str:
    """Render cohort scan output as readable text."""
    lines = [
        f"Cohort 扫描结果（命中 {cohort_size} 个客户）",
        "",
    ]
    if cohort_signals:
        lines.append("共同信号:")
        for signal in cohort_signals:
            lines.append(f"  - {signal}")
    if cohort_issues:
        lines.append("共同问题:")
        for issue in cohort_issues:
            lines.append(f"  - {issue}")
    if key_customers:
        lines.append("")
        lines.append("重点关注客户:")
        for item in key_customers:
            record = item.get("customer_record", {})
            name = record.get("简称") or record.get("客户名称", "未知")
            lens_results = item.get("lens_results", {})
            lines.append(f"  ■ {name}")
            for lens_key, label in [("risk", "风险"), ("opportunity", "机会"), ("relationship", "关系"), ("project_progress", "进展")]:
                conclusions = lens_results.get(lens_key, [])
                if conclusions:
                    lines.append(f"    {label}: {'; '.join(conclusions)}")
    if recommendations:
        lines.append("")
        lines.append("建议行动:")
        for rec in recommendations:
            lines.append(f"  - {rec}")
    return "\n".join(lines)


def run_cohort_scan_scene(request: SceneRequest) -> SceneResult:
    """Cohort scan scene — user-triggered analytical entry point.

    Per D-03 (dynamic condition query), D-04 (limit default 10),
    D-05 (aggregated summary + key customers), D-06-D-08 (output structure),
    D-12 (user-triggered, NOT scheduled).

    Uses LarkCliCustomerBackend.list_all_customers() for customer fetch,
    _parse_condition_query() for filter criteria,
    and _derive_account_posture_lenses() for per-customer four-lens analysis.
    """
    from runtime.live_adapter import LarkCliCustomerBackend

    cohort_limit = int(request.options.get("cohort_limit", 10))
    condition_query = str(request.inputs.get("condition_query", ""))

    repo_root = request.repo_root.expanduser()
    gateway = FeishuWorkbenchGateway.for_live_lark_cli(str(repo_root))
    sources = RuntimeSourceLoader(repo_root).load()
    query_backend = LarkCliBaseQueryBackend(
        LarkCliClient(),
        LiveWorkbenchConfig.from_sources(sources),
    )

    # 1. Fetch all customers from customer master
    customer_backend = LarkCliCustomerBackend(
        LarkCliClient(),
        LiveWorkbenchConfig.from_sources(sources),
    )
    all_customers = customer_backend.list_all_customers(limit=200)
    if not all_customers:
        return _build_empty_cohort_result(request, condition_query)

    # 2. Parse dynamic condition into filter criteria
    filter_criteria = _parse_condition_query(condition_query)

    # 3. Apply filter to get cohort
    cohort = customer_backend.filter_customers(all_customers, filter_criteria)

    # 4. Check limit — if exceeded, return prompt to narrow (D-04)
    if len(cohort) > cohort_limit:
        return _build_cohort_limit_result(request, len(cohort), cohort_limit, all_customers, condition_query)

    # 5. Per-customer four-lens analysis (reuses STAT-01 pattern)
    customer_lens_results: list[dict[str, Any]] = []
    for customer_record in cohort:
        customer_id = customer_record.get("客户ID") or customer_record.get("customer_id") or ""
        # Build a minimal EvidenceContainer for this customer
        # Sources are drawn from the customer record itself
        customer_container = EvidenceContainer()
        customer_container.sources["customer_master"] = EvidenceSource(
            name="customer_master",
            quality="live",
            available=True,
            content=[
                f"客户名称: {customer_record.get('客户名称', '')}",
                f"简称: {customer_record.get('简称', '')}",
                f"状态: {customer_record.get('状态', '')}",
            ],
        )
        lens_results = _derive_account_posture_lenses(customer_container)
        customer_lens_results.append({
            "customer_record": customer_record,
            "lens_results": lens_results,
        })

    # 6. Aggregate cohort-level signals and issues
    cohort_signals = _aggregate_cohort_signals(customer_lens_results)
    cohort_issues = _aggregate_cohort_issues(customer_lens_results)
    key_customers = _select_key_customers(customer_lens_results)  # top 3-5 by risk/opportunity

    # 7. Build two-tier recommendations (D-07, D-08)
    recommendations = _build_cohort_recommendations(
        cohort_signals=cohort_signals,
        cohort_issues=cohort_issues,
        key_customers=key_customers,
    )

    # 8. Render output
    output_text = _render_cohort_output(
        cohort_size=len(cohort),
        cohort_signals=cohort_signals,
        cohort_issues=cohort_issues,
        key_customers=key_customers,
        recommendations=recommendations,
    )

    return SceneResult(
        scene_name=request.scene_name,
        resource_status="resolved",
        customer_status="cohort",
        context_status="completed",
        used_sources=["customer_master"],
        facts=[f"筛选条件: {condition_query}", f"命中客户数: {len(cohort)}"],
        judgments=[],
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
