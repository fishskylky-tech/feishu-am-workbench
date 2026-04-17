"""Tests for PREP-01: meeting prep seven-dimension brief."""

from __future__ import annotations

import pytest

from runtime.scene_runtime import (
    _derive_account_posture_lenses,
    _render_meeting_prep_output,
    run_meeting_prep_scene,
)
from runtime.expert_analysis_helper import EvidenceContainer, EvidenceSource


class TestMeetingPrepSevenDimension:
    """Test seven-dimension output per D-07."""

    def test_render_output_includes_all_seven_dimensions(self) -> None:
        """_render_meeting_prep_output renders all 7 dimensions."""
        stat01 = {"risk": ["风险"], "opportunity": ["机会"], "relationship": ["关系"], "project_progress": ["进展"]}
        lines = _render_meeting_prep_output(
            stat01_lens_results=stat01,
            key_people_items=["张三 | 负责人"],
            meeting_objectives=["Q2目标对齐"],
            risk_items=["风险1"],
            opportunity_items=["机会1"],
            suggested_questions=["问题1"],
            suggested_next_steps=["步骤1"],
        )
        assert lines[0] == "--- 会前准备简报 ---"
        content = "\n".join(lines)
        assert "当前状态:" in content
        assert "关键人物:" in content
        assert "目的:" in content
        assert "风险:" in content
        assert "机会:" in content
        assert "建议问题:" in content
        assert "建议后续步骤:" in content

    def test_current_status_reuses_stat01_four_lens(self) -> None:
        """当前状态 dimension reuses STAT-01 four-lens output per D-08."""
        stat01 = {
            "risk": ["风险信号1", "风险信号2"],
            "opportunity": ["机会信号1"],
            "relationship": ["关系信号1", "关系信号2", "关系信号3"],
            "project_progress": ["进展信号1"],
        }
        lines = _render_meeting_prep_output(
            stat01_lens_results=stat01,
            key_people_items=[],
            meeting_objectives=[],
            risk_items=[],
            opportunity_items=[],
            suggested_questions=[],
            suggested_next_steps=[],
        )
        content = "\n".join(lines)
        assert "风险: 风险信号1, 风险信号2" in content
        assert "机会: 机会信号1" in content
        assert "关系: 关系信号1, 关系信号2, 关系信号3" in content
        assert "进展: 进展信号1" in content

    def test_current_status_shows_placeholder_when_empty(self) -> None:
        """Empty STAT-01 lenses show placeholder text."""
        stat01 = {"risk": [], "opportunity": [], "relationship": [], "project_progress": []}
        lines = _render_meeting_prep_output(
            stat01_lens_results=stat01,
            key_people_items=[],
            meeting_objectives=[],
            risk_items=[],
            opportunity_items=[],
            suggested_questions=[],
            suggested_next_steps=[],
        )
        content = "\n".join(lines)
        assert "暂无风险信号" in content
        assert "暂无机会信号" in content
        assert "暂无关系信号" in content
        assert "暂无进展信号" in content

    def test_each_dimension_capped_at_three_items(self) -> None:
        """Each dimension shows at most 3 items per D-02."""
        stat01 = {k: [f"item{i}" for i in range(5)] for k in ["risk", "opportunity", "relationship", "project_progress"]}
        lines = _render_meeting_prep_output(
            stat01_lens_results=stat01,
            key_people_items=[f"kp{i}" for i in range(5)],
            meeting_objectives=[f"obj{i}" for i in range(5)],
            risk_items=[f"risk{i}" for i in range(5)],
            opportunity_items=[f"opp{i}" for i in range(5)],
            suggested_questions=[f"q{i}" for i in range(5)],
            suggested_next_steps=[f"s{i}" for i in range(5)],
        )
        content = "\n".join(lines)
        for section in ["风险:", "机会:", "关系:", "进展:"]:
            line = next((l for l in lines if section in l), None)
            assert line is not None, f"{section} not found in output"
            if "暂无" not in line:
                parts = line.split(": ")[1] if ": " in line else ""
                if parts:
                    item_count = len(parts.split(", "))
                    assert item_count <= 3, f"{section} has {item_count} items"


class TestMeetingPrepStat01Reuse:
    """Test STAT-01 four-lens reuse per D-08."""

    def test_stat01_lens_results_extracted_from_evidence(self) -> None:
        """_derive_account_posture_lenses extracts risk and opportunity from evidence."""
        container = EvidenceContainer()
        container.sources["customer_master"] = EvidenceSource(
            name="customer_master", quality="live", available=True,
            content=["客户: TestCo", "风险: 竞品压力", "机会: 扩张需求"]
        )
        container.sources["action_plan"] = EvidenceSource(
            name="action_plan", quality="recovered", available=True,
            content=["进展: Q2交付中"]
        )
        stat01 = _derive_account_posture_lenses(container)
        assert "风险" in stat01["risk"] or "竞品" in stat01["risk"]
        assert "机会" in stat01["opportunity"] or "扩张" in stat01["opportunity"]

    def test_stat01_reuse_returns_empty_when_no_container(self) -> None:
        """STAT-01 reuse returns empty lists when evidence_container is None."""
        result = _derive_account_posture_lenses(None)
        assert result == {"risk": [], "opportunity": [], "relationship": [], "project_progress": []}


class TestMeetingPrepSceneRegistration:
    """Test meeting-prep scene registration per D-09."""

    def test_meeting_prep_registered_in_registry(self) -> None:
        """meeting-prep scene is registered in scene registry."""
        from runtime.scene_registry import build_default_scene_registry
        registry = build_default_scene_registry()
        assert "meeting-prep" in registry.available_scenes()

    def test_meeting_prep_dispatch_returns_scene_result(self) -> None:
        """dispatching meeting-prep scene returns SceneResult."""
        from pathlib import Path
        from runtime.scene_registry import build_default_scene_registry
        from runtime.scene_runtime import SceneRequest

        registry = build_default_scene_registry()
        request = SceneRequest(
            scene_name="meeting-prep",
            repo_root=Path("/tmp"),
            customer_query="test-customer",
            inputs={},
            options={},
        )
        result = registry.dispatch(request)
        assert result.scene_name == "meeting-prep"
        assert "会前准备简报" in result.output_text
