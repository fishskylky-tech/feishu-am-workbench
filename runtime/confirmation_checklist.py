"""WRITE-02: Confirmation checklist infrastructure for expert-led scene outputs.

Per D-10: Checklist is shown BEFORE scene executes — intent-driven output generation.
Per D-11: Minimal-questions principle — system infers from EvidenceContainer, recovered
    context, archive, and STAT-01 output; only asks when genuinely missing AND critical.
Per D-12: Scene-specific checklists — not standardized across scenes.

D-13 through D-17 define scene-specific items:
    Archive refresh: refresh type, archive location suggestion, key people sync, update action plans, update archives
    Meeting prep: meeting type, agenda, prior meeting reference (as suggestions, not questions)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChecklistItem:
    """A single checklist item with system suggestion and confirmation state."""

    key: str
    label: str
    system_suggestion: str
    user_confirmed: bool = False
    user_modification: str | None = None

    def confirmed_value(self) -> str:
        """Return the confirmed value (user modification or system suggestion)."""
        if self.user_modification is not None:
            return self.user_modification
        return self.system_suggestion


@dataclass
class ConfirmationChecklist:
    """Scene confirmation checklist capturing user intent before scene execution.

    Per D-10: Answers precede scene execution.
    Per D-11: Minimal-questions — system infers suggestions, user confirms or modifies.
    """

    scene_name: str
    items: list[ChecklistItem] = field(default_factory=list)

    # WRITE-02 universal items always present
    audience: ChecklistItem | None = None
    purpose: ChecklistItem | None = None
    internal_external: ChecklistItem | None = None
    resource_coordination: ChecklistItem | None = None

    def confirmed_answers(self) -> dict[str, str]:
        """Return dict of confirmed answers keyed by item key."""
        answers = {}
        for item in self.items:
            answers[item.key] = item.confirmed_value()
        if self.audience:
            answers["audience"] = self.audience.confirmed_value()
        if self.purpose:
            answers["purpose"] = self.purpose.confirmed_value()
        if self.internal_external:
            answers["internal_external"] = self.internal_external.confirmed_value()
        if self.resource_coordination:
            answers["resource_coordination"] = self.resource_coordination.confirmed_value()
        return answers

    def all_confirmed(self) -> bool:
        """True if all items have been confirmed (accepted or modified)."""
        return all(
            item.user_confirmed or item.user_modification is not None
            for item in self.items
        )


def build_archive_refresh_checklist(
    evidence_container: Any | None,
    recovery: Any | None,
) -> ConfirmationChecklist:
    """Build archive refresh scene confirmation checklist per D-13, D-14, D-15.

    D-13: Includes WRITE-02 universal items: audience, purpose, internal/external, resource-coordination.
    D-14: Scene-specific item — refresh type (补充历史 vs 校正现有档案).
    D-15: System-inferred suggestions for archive location, key people sync, update decisions.
    """
    checklist = ConfirmationChecklist(scene_name="archive-refresh")

    # WRITE-02 universal items (D-13)
    checklist.audience = ChecklistItem(
        key="audience",
        label="受众",
        system_suggestion="客户内部",
    )
    checklist.purpose = ChecklistItem(
        key="purpose",
        label="目的",
        system_suggestion="档案更新参考",
    )
    checklist.internal_external = ChecklistItem(
        key="internal_external",
        label="内部/外部",
        system_suggestion="内部使用",
    )
    checklist.resource_coordination = ChecklistItem(
        key="resource_coordination",
        label="资源协调需要",
        system_suggestion="不涉及",
    )

    # D-14: Refresh type
    checklist.items.append(ChecklistItem(
        key="refresh_type",
        label="刷新类型",
        system_suggestion="补充历史",
    ))

    # D-15: System-inferred suggestions
    archive_location = "客户档案文件夹"
    if evidence_container:
        arch_src = evidence_container.sources.get("customer_archive")
        if arch_src and arch_src.available:
            archive_location = f"已有档案: {arch_src.raw_data.get('name', archive_location)}"

    checklist.items.append(ChecklistItem(
        key="archive_location",
        label="档案位置建议",
        system_suggestion=archive_location,
    ))

    checklist.items.append(ChecklistItem(
        key="key_people_sync",
        label="关键人物同步",
        system_suggestion="同步关键人物表",
    ))

    checklist.items.append(ChecklistItem(
        key="update_action_plan",
        label="是否更新行动计划",
        system_suggestion="待确认",
    ))

    checklist.items.append(ChecklistItem(
        key="update_archive",
        label="是否更新档案",
        system_suggestion="待确认",
    ))

    return checklist


def build_meeting_prep_checklist(
    evidence_container: Any | None,
    recovery: Any | None,
) -> ConfirmationChecklist:
    """Build meeting prep scene confirmation checklist per D-16, D-17.

    D-16: Minimal — only WRITE-02 universal four items.
    D-17: Meeting-specific details (meeting type, agenda, prior meeting reference)
        are surfaced as suggestions, not questions.
    """
    checklist = ConfirmationChecklist(scene_name="meeting-prep")

    # D-16: WRITE-02 universal items only (meeting-specific details as suggestions per D-17)

    # Infer meeting type from evidence
    meeting_type = "复盘会"
    if evidence_container:
        mt_src = evidence_container.sources.get("meeting_notes")
        if mt_src and mt_src.content:
            for content in mt_src.content[:3]:
                if any(kw in content for kw in ["目标对齐", "Q1", "Q2", "季度"]):
                    meeting_type = "目标对齐会"
                    break
                if any(kw in content for kw in ["签约", "合同", "续约"]):
                    meeting_type = "商务谈判会"
                    break

    checklist.audience = ChecklistItem(
        key="audience",
        label="受众",
        system_suggestion="客户内部",
    )
    checklist.purpose = ChecklistItem(
        key="purpose",
        label="目的",
        system_suggestion="会前准备参考",
    )
    checklist.internal_external = ChecklistItem(
        key="internal_external",
        label="内部/外部",
        system_suggestion="内部使用",
    )
    checklist.resource_coordination = ChecklistItem(
        key="resource_coordination",
        label="资源协调需要",
        system_suggestion="不涉及",
    )

    # D-17: Meeting-specific as suggestions (not checklist items)
    checklist.items.append(ChecklistItem(
        key="meeting_type_suggestion",
        label="会议类型",
        system_suggestion=meeting_type,
    ))

    agenda_items = ["上次会议后续确认", "本次目标对齐", "下一步计划"]
    if evidence_container:
        mt_src = evidence_container.sources.get("meeting_notes")
        if mt_src and mt_src.content:
            agenda_items = mt_src.content[:3] if mt_src.content else agenda_items

    checklist.items.append(ChecklistItem(
        key="agenda_suggestion",
        label="议程建议",
        system_suggestion="\n".join([f"- {a}" for a in agenda_items]),
    ))

    return checklist


def render_confirmation_checklist(checklist: ConfirmationChecklist) -> list[str]:
    """Render confirmation checklist to terminal output format per UI-SPEC lines 153-186.

    Format:
    === {场景名}确认清单 ===

    1. {label}：{system_suggestion}
       > 系统建议: {system_suggestion}
       确认? [Y/n]

    ...

    [输入 q 退出，输入任意键继续执行场景]
    """
    lines = [f"=== {checklist.scene_name}确认清单 ===", ""]

    # Universal items first
    universal_items = [
        checklist.audience,
        checklist.purpose,
        checklist.internal_external,
        checklist.resource_coordination,
    ]

    idx = 1
    for item in universal_items:
        if item is None:
            continue
        lines.append(f"{idx}. {item.label}：{item.system_suggestion}")
        lines.append(f"   > 系统建议: {item.system_suggestion}")
        lines.append(f"   确认? [Y/n]")
        lines.append("")
        idx += 1

    # Scene-specific items
    for item in checklist.items:
        lines.append(f"{idx}. {item.label}：")
        lines.append(f"   > 系统建议: {item.system_suggestion}")
        if item.key.endswith("_suggestion"):
            lines.append(f"   确认? [Y/n] (建议值，无需修改可直接回车)")
        else:
            lines.append(f"   确认或修改: [直接回车确认 / 输入修改]")
        lines.append("")
        idx += 1

    lines.append("[输入 q 退出，输入任意键继续执行场景]")
    return lines
