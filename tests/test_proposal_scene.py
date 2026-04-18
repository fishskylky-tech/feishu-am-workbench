"""Tests for PROP-01: proposal/report/resource-coordination scene and WRITE-01: Feishu-native routing."""

from __future__ import annotations

import unittest
from pathlib import Path

import pytest

from runtime.scene_runtime import (
    _derive_proposal_lenses,
    _infer_proposal_output_destination,
    _extract_action_items_from_proposal,
    _build_proposal_routing_payload,
    _render_proposal_output,
    run_proposal_scene,
    SceneRequest,
)
from runtime.scene_registry import dispatch_scene
from runtime.confirmation_checklist import (
    build_proposal_checklist,
)
from runtime.expert_analysis_helper import EvidenceContainer, EvidenceSource


class TestProposalFiveDimension:
    """Test five-dimension output per D-06."""

    def test_render_output_includes_all_five_dimensions(self) -> None:
        """_render_proposal_output renders all 5 sections per D-06."""
        lens_results = {
            "objective": ["目标1"],
            "core_judgment": ["判断1"],
            "main_narrative": ["叙事1"],
            "resource_asks": ["资源1"],
            "open_questions": ["问题1"],
        }
        lines = _render_proposal_output(lens_results, "proposal")
        assert lines[0] == "--- 提案/报告/资源协调草案 ---"
        content = "\n".join(lines)
        assert "目的:" in content
        assert "核心判断:" in content
        assert "主要叙事:" in content
        assert "资源请求:" in content
        assert "待确认问题:" in content

    def test_objective_max_two_items(self) -> None:
        """Objective dimension shows max 2 items per D-06."""
        lens_results = {
            "objective": ["目标1", "目标2", "目标3"],
            "core_judgment": [],
            "main_narrative": [],
            "resource_asks": [],
            "open_questions": [],
        }
        lines = _render_proposal_output(lens_results, "proposal")
        content = "\n".join(lines)
        # Count items under 目的
        purpose_section = False
        item_count = 0
        for line in lines:
            if "目的:" in line:
                purpose_section = True
                continue
            if purpose_section and line.startswith("- "):
                item_count += 1
            if purpose_section and not line.startswith("- ") and "目的" not in line:
                break
        assert item_count <= 2

    def test_core_judgment_placeholder_when_empty(self) -> None:
        """Empty core_judgment shows placeholder text."""
        lens_results = {
            "objective": [],
            "core_judgment": [],
            "main_narrative": [],
            "resource_asks": [],
            "open_questions": [],
        }
        lines = _render_proposal_output(lens_results, "proposal")
        content = "\n".join(lines)
        assert "暂无核心判断" in content

    def test_resource_asks_placeholder_when_empty(self) -> None:
        """Empty resource_asks shows placeholder text."""
        lens_results = {
            "objective": [],
            "core_judgment": [],
            "main_narrative": [],
            "resource_asks": [],
            "open_questions": [],
        }
        lines = _render_proposal_output(lens_results, "proposal")
        content = "\n".join(lines)
        assert "暂无资源请求" in content

    def test_open_questions_placeholder_when_empty(self) -> None:
        """Empty open_questions shows placeholder text."""
        lens_results = {
            "objective": [],
            "core_judgment": [],
            "main_narrative": [],
            "resource_asks": [],
            "open_questions": [],
        }
        lines = _render_proposal_output(lens_results, "proposal")
        content = "\n".join(lines)
        assert "暂无待确认问题" in content


class TestProposalTypeEmphasis:
    """Test type-specific emphasis per D-07."""

    def test_proposal_type_emphasizes_core_judgment(self) -> None:
        """Proposal type shows 4 core judgments per D-07."""
        lens_results = {
            "objective": [],
            "core_judgment": ["判断1", "判断2", "判断3", "判断4", "判断5"],
            "main_narrative": ["叙事1"],
            "resource_asks": [],
            "open_questions": [],
        }
        lines = _render_proposal_output(lens_results, "proposal")
        content = "\n".join(lines)
        # Count core judgment items
        judgment_count = content.count("- 判断")
        assert judgment_count == 4

    def test_report_type_emphasizes_narrative(self) -> None:
        """Report type shows 3 narrative items per D-07."""
        lens_results = {
            "objective": [],
            "core_judgment": [],
            "main_narrative": ["叙事1", "叙事2", "叙事3", "叙事4"],
            "resource_asks": [],
            "open_questions": [],
        }
        lines = _render_proposal_output(lens_results, "report")
        content = "\n".join(lines)
        # Count narrative items (should be max 3 for report)
        narrative_count = content.count("- 叙事")
        assert narrative_count == 3

    def test_resource_coordination_emphasizes_resource_asks(self) -> None:
        """Resource-coordination type shows 4 resource items per D-07."""
        lens_results = {
            "objective": [],
            "core_judgment": [],
            "main_narrative": [],
            "resource_asks": ["资源1", "资源2", "资源3", "资源4", "资源5"],
            "open_questions": [],
        }
        lines = _render_proposal_output(lens_results, "resource-coordination")
        content = "\n".join(lines)
        # Count resource items (should be max 4 for resource-coordination)
        resource_count = content.count("- 资源")
        assert resource_count == 4

    def test_resource_coordination_extracts_action_items(self) -> None:
        """Resource-coordination extracts action items for Base/Task routing per D-10."""
        lens_results = {
            "objective": [],
            "core_judgment": [],
            "main_narrative": [],
            "resource_asks": ["资源需求1", "资源需求2"],
            "open_questions": ["待确认1"],
        }
        action_items = _extract_action_items_from_proposal(lens_results, "resource-coordination")
        assert len(action_items) == 3  # 2 resource + 1 question
        assert "subject" in action_items[0]
        assert "description" in action_items[0]

    def test_proposal_type_does_not_extract_action_items(self) -> None:
        """Proposal type does not extract action items per D-07."""
        lens_results = {
            "objective": [],
            "core_judgment": [],
            "main_narrative": [],
            "resource_asks": ["资源1"],
            "open_questions": [],
        }
        action_items = _extract_action_items_from_proposal(lens_results, "proposal")
        assert len(action_items) == 0


class TestProposalChecklist:
    """Test WRITE-02 confirmation checklist per D-13, D-14, D-15."""

    def test_proposal_checklist_has_universal_items(self) -> None:
        """Proposal checklist includes all 4 WRITE-02 universal items per D-13."""
        checklist = build_proposal_checklist(None, None)
        assert checklist.audience is not None
        assert checklist.purpose is not None
        assert checklist.internal_external is not None
        assert checklist.resource_coordination is not None

    def test_proposal_checklist_scene_name(self) -> None:
        """Proposal checklist has scene_name='proposal'."""
        checklist = build_proposal_checklist(None, None)
        assert checklist.scene_name == "proposal"

    def test_proposal_checklist_has_scene_specific_items(self) -> None:
        """Proposal checklist has scene-specific items per D-14."""
        checklist = build_proposal_checklist(None, None)
        item_keys = [item.key for item in checklist.items]
        assert "proposal_type" in item_keys
        assert "output_destination" in item_keys

    def test_proposal_checklist_accepts_proposal_type_parameter(self) -> None:
        """build_proposal_checklist accepts proposal_type parameter per D-14."""
        checklist = build_proposal_checklist(None, None, proposal_type="report")
        # Find proposal_type item
        proposal_type_item = next((item for item in checklist.items if item.key == "proposal_type"), None)
        assert proposal_type_item is not None
        assert proposal_type_item.system_suggestion == "report"

    def test_proposal_checklist_infers_destination_from_evidence(self) -> None:
        """build_proposal_checklist infers output_destination from evidence per D-15."""
        container = EvidenceContainer()
        container.sources["customer_archive"] = EvidenceSource(
            name="customer_archive",
            quality="archived",
            available=True,
            content=["历史档案"],
            raw_data={"name": "测试客户档案"},
        )
        checklist = build_proposal_checklist(container, None)
        dest_item = next((item for item in checklist.items if item.key == "output_destination"), None)
        assert dest_item is not None
        assert "测试客户档案" in dest_item.system_suggestion


class TestProposalRouting:
    """Test WRITE-01 Feishu-native routing per D-10, D-11, D-12."""

    def test_proposal_type_routes_to_drive(self) -> None:
        """Proposal type suggests Drive routing per D-12."""
        dest = _infer_proposal_output_destination(None, "proposal")
        assert "Drive" in dest

    def test_report_type_routes_to_drive(self) -> None:
        """Report type suggests Drive routing per D-12."""
        dest = _infer_proposal_output_destination(None, "report")
        assert "Drive" in dest

    def test_resource_coordination_routes_to_base_or_task(self) -> None:
        """Resource-coordination type suggests Base or Task routing per D-12."""
        dest = _infer_proposal_output_destination(None, "resource-coordination")
        assert "Base" in dest or "Task" in dest

    def test_build_proposal_routing_payload_for_proposal(self) -> None:
        """_build_proposal_routing_payload returns drive_doc for proposal per D-12."""
        payload = _build_proposal_routing_payload(
            "proposal",
            "Drive 客户档案文件夹",
            {"objective": [], "core_judgment": [], "main_narrative": [], "resource_asks": [], "open_questions": []},
            {"customer_id": "test", "short_name": "Test"},
        )
        assert payload["destination_type"] == "drive_doc"
        assert payload["target"] == "Drive 客户档案文件夹"
        assert "content" in payload

    def test_build_proposal_routing_payload_for_resource_coordination(self) -> None:
        """_build_proposal_routing_payload returns base_table/task for resource-coordination per D-12."""
        payload = _build_proposal_routing_payload(
            "resource-coordination",
            "Base 行动计划表",
            {"objective": [], "core_judgment": [], "main_narrative": [], "resource_asks": ["资源1"], "open_questions": []},
            {"customer_id": "test", "short_name": "Test"},
        )
        assert payload["destination_type"] in ("base_table", "task")
        assert "action_items" in payload


class TestProposalLensDerivation:
    """Test five-dimension lens derivation from evidence."""

    def test_derive_proposal_lenses_extracts_objective(self) -> None:
        """_derive_proposal_lenses extracts objective from customer_master and meeting_notes."""
        container = EvidenceContainer()
        container.sources["customer_master"] = EvidenceSource(
            name="customer_master",
            quality="live",
            available=True,
            content=["客户: TestCo", "目标: 提升营收"],
        )
        container.sources["meeting_notes"] = EvidenceSource(
            name="meeting_notes",
            quality="recovered",
            available=True,
            content=["目标: Q3扩张"],
        )
        lens_results = _derive_proposal_lenses(container)
        assert "目标" in lens_results["objective"] or "营收" in lens_results["objective"]

    def test_derive_proposal_lenses_extracts_resource_asks(self) -> None:
        """_derive_proposal_lenses extracts resource asks from action_plan and meeting_notes."""
        container = EvidenceContainer()
        container.sources["action_plan"] = EvidenceSource(
            name="action_plan",
            quality="recovered",
            available=True,
            content=["资源需求: 人力投入", "需要预算支持"],
        )
        lens_results = _derive_proposal_lenses(container)
        assert len(lens_results["resource_asks"]) > 0

    def test_derive_proposal_lenses_returns_empty_when_no_container(self) -> None:
        """_derive_proposal_lenses returns empty lists when evidence_container is None."""
        result = _derive_proposal_lenses(None)
        expected_keys = ["objective", "core_judgment", "main_narrative", "resource_asks", "open_questions"]
        assert list(result.keys()) == expected_keys
        assert all(v == [] for v in result.values())


class TestProposalSceneRegistration:
    """Test proposal scene registration per D-03."""

    def test_proposal_registered_in_registry(self) -> None:
        """proposal scene is registered in scene registry."""
        from runtime.scene_registry import build_default_scene_registry
        registry = build_default_scene_registry()
        assert "proposal" in registry.available_scenes()

    def test_proposal_dispatch_returns_scene_result(self) -> None:
        """Dispatching proposal scene returns SceneResult."""
        from pathlib import Path
        from runtime.scene_registry import build_default_scene_registry
        from runtime.scene_runtime import SceneRequest

        registry = build_default_scene_registry()
        request = SceneRequest(
            scene_name="proposal",
            repo_root=Path("/tmp"),
            customer_query="test-customer",
            inputs={"proposal_type": "proposal"},
            options={},
        )
        result = registry.dispatch(request)
        assert result.scene_name == "proposal"
        assert "提案/报告/资源协调草案" in result.output_text or "确认清单" in result.output_text


class TestProposalRegression(unittest.TestCase):
    """VAL-05 regression: proposal scene handles 4 case types per D-01 to D-06."""

    def test_proposal_happy_path_dispatch_and_result_shape(self) -> None:
        """Happy-path: proposal dispatch returns valid SceneResult with expected shape."""
        request = SceneRequest(
            scene_name="proposal",
            repo_root=Path("."),
            customer_query="测试客户",
            inputs={"proposal_type": "proposal", "goal": "Q2合作推进", "materials": []},
        )
        result = dispatch_scene(request)
        self.assertEqual(result.scene_name, "proposal")
        self.assertIn(result.resource_status, ("live", "partial", "resolved"))
        self.assertIn(result.customer_status, ("resolved", "missing"))
        self.assertIn(result.context_status, ("complete", "partial", "context-limited", "not-run"))
        self.assertIn(result.write_ceiling, ("normal", "recommendation-only"))
        self.assertIsNotNone(result.payload)
        self.assertIsInstance(result.payload, dict)

    def test_proposal_limited_context_fallback_visible(self) -> None:
        """Limited-context: fallback_category is set and output/recommendations present."""
        request = SceneRequest(
            scene_name="proposal",
            repo_root=Path("."),
            customer_query="完全不存在的客户XYZ999不存在",
            inputs={"proposal_type": "proposal", "goal": "Q2合作推进", "materials": []},
        )
        result = dispatch_scene(request)
        self.assertIn(result.context_status, ("partial", "minimal", "context-limited", "not-run"))
        self.assertIn(result.fallback_category, ("context", "none", "customer"))
        self.assertTrue(
            result.output_text is not None or result.recommendations is not None,
            "Expected output_text or recommendations with limited context",
        )

    def test_proposal_unresolved_customer(self) -> None:
        """Unresolved customer: customer_status is not resolved, fallback_category is customer, write_ceiling is recommendation-only."""
        request = SceneRequest(
            scene_name="proposal",
            repo_root=Path("."),
            customer_query="完全不存在的客户XYZ999不存在",
            inputs={"proposal_type": "proposal", "goal": "Q2合作推进", "materials": []},
        )
        result = dispatch_scene(request)
        self.assertNotEqual(result.customer_status, "resolved")
        self.assertEqual(result.fallback_category, "customer")
        self.assertEqual(result.write_ceiling, "recommendation-only")

    def test_proposal_blocked_write(self) -> None:
        """Blocked-write: write_ceiling is recommendation-only, fallback_category is set, no write_candidates in payload."""
        request = SceneRequest(
            scene_name="proposal",
            repo_root=Path("."),
            customer_query="完全不存在的客户XYZ999不存在",
            inputs={"proposal_type": "proposal", "goal": "Q2合作推进", "materials": []},
        )
        result = dispatch_scene(request)
        self.assertEqual(result.write_ceiling, "recommendation-only")
        self.assertIn(result.fallback_category, ("customer", "safety", "permission", "context"))
        self.assertIsNotNone(result.recommendations)
        self.assertGreater(len(result.recommendations), 0)
        self.assertIsNotNone(result.payload)
        self.assertNotIn("write_candidates", result.payload)
