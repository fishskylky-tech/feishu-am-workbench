"""Confirmation checklist contracts for scene execution.

Per D-10: confirmation checklists are shown BEFORE scene executes.
User confirms or modifies checklist items before the scene runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConfirmationChecklist:
    """A confirmation checklist with suggested items and user-confirmed answers."""
    items: list[str] = field(default_factory=list)
    confirmed_answers: dict[str, bool] = field(default_factory=dict)

    def confirmed_answers(self) -> dict[str, bool]:
        """Return the dict of confirmed answers."""
        return self.confirmed_answers


def build_archive_refresh_checklist(
    evidence_container: Any,
    recovery: Any,
) -> ConfirmationChecklist:
    """Build a confirmation checklist for archive refresh scene.

    Per D-10: checklist is shown BEFORE scene executes.
    Provides system suggestions for what archive refresh will act on.
    """
    items = [
        "确认要刷新客户档案吗？",
        "确认基于当前 live 上下文生成档案更新建议？",
        "确认写回目标路径为 Feishu 原生路径？",
    ]
    if evidence_container is not None:
        available = evidence_container.available_sources() if hasattr(evidence_container, 'available_sources') else []
        if available:
            items.insert(0, f"可用证据来源: {', '.join(available)}")
    return ConfirmationChecklist(items=items)


def render_confirmation_checklist(checklist: ConfirmationChecklist) -> list[str]:
    """Render a confirmation checklist as a list of output lines.

    Per D-10: rendered checklist is shown to user before scene execution.
    """
    if not checklist.items:
        return []
    lines = ["=== 确认检查清单 ==="]
    for i, item in enumerate(checklist.items, 1):
        lines.append(f"{i}. {item}")
    lines.append("请确认以上项目 [Y/n]: ")
    return lines
