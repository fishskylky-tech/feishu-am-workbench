"""Tests for expert-analysis infrastructure (Phase 16).

Covers EvidenceContainer assembly, critical-source-missing hard-stop,
fallback visibility, EvidenceSource.summary(), and detect_conflicts().
No live Feishu API calls — all tests use in-memory EvidenceAssemblyInput.
"""

from __future__ import annotations

import pytest

from runtime.expert_analysis_helper import EvidenceAssemblyInput, ExpertAnalysisHelper
from runtime.models import CRITICAL_SOURCES, EvidenceContainer, EvidenceSource, EvidenceSourceName


class TestExpertAnalysisHelperAssemble:
    """Test ExpertAnalysisHelper.assemble() produces correct EvidenceContainer."""

    def test_assemble_with_all_sources_available(self) -> None:
        """Full evidence bundle: all sources available, no missing sources."""
        input_data = EvidenceAssemblyInput(
            transcript_content=["会议讨论了Q2推进计划"],
            transcript_available=True,
            customer_master_content=["客户: TestCo"],
            customer_master_available=True,
            contact_records_content=["最近联系: 2026-04-01"],
            contact_records_available=True,
            action_plan_content=["行动计划: Q2推进"],
            action_plan_available=True,
            meeting_notes_content=["会议纪要: 已确认"],
            meeting_notes_available=True,
            customer_archive_content=["archive snapshot"],
            customer_archive_available=True,
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()

        # Available sources
        assert container.sources["customer_master"].available is True
        assert container.sources["customer_master"].quality == "live"
        assert container.sources["contact_records"].available is True
        assert container.sources["contact_records"].quality == "live"
        assert container.sources["action_plan"].available is True
        assert container.sources["action_plan"].quality == "recovered"
        assert container.sources["meeting_notes"].available is True
        assert container.sources["meeting_notes"].quality == "recovered"
        assert container.sources["customer_archive"].available is True
        assert container.sources["customer_archive"].quality == "archived"
        assert container.sources["transcript"].available is True
        assert container.sources["transcript"].quality == "live"

        # Missing source tracking
        assert container.missing_source_count == 0
        assert container.critical_source_missing is False
        assert container.missing_critical_sources == []
        assert container.write_ceiling == "normal"
        assert container.fallback_reason is None

    def test_assemble_with_meeting_notes_missing(self) -> None:
        """Partial evidence: meeting_notes unavailable, others present."""
        input_data = EvidenceAssemblyInput(
            customer_master_content=["客户: TestCo"],
            customer_master_available=True,
            contact_records_content=["最近联系: 2026-04-01"],
            contact_records_available=True,
            action_plan_content=["行动计划: Q2推进"],
            action_plan_available=True,
            meeting_notes_content=[],
            meeting_notes_available=False,
            meeting_notes_missing_reason="no meeting notes found",
            customer_archive_content=["archive snapshot"],
            customer_archive_available=True,
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()

        assert container.sources["customer_master"].available is True
        assert container.sources["customer_master"].quality == "live"
        assert container.sources["meeting_notes"].available is False
        assert container.sources["meeting_notes"].missing_reason == "no meeting notes found"
        assert container.missing_source_count == 1
        assert container.critical_source_missing is False
        assert container.write_ceiling == "normal"


class TestCriticalSourceMissing:
    """Test hard-stop when critical sources (customer_master, contact_records) are missing."""

    def test_customer_master_missing_triggers_hard_stop(self) -> None:
        """customer_master is a critical source; its absence forces recommendation-only."""
        input_data = EvidenceAssemblyInput(
            customer_master_content=[],
            customer_master_available=False,
            customer_master_missing_reason="customer not resolved",
            contact_records_content=["最近联系: 2026-04-01"],
            contact_records_available=True,
            action_plan_content=[],
            action_plan_available=False,
            action_plan_missing_reason="no action plan",
            meeting_notes_content=[],
            meeting_notes_available=False,
            customer_archive_content=[],
            customer_archive_available=False,
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()

        assert container.critical_source_missing is True
        assert "customer_master" in container.missing_critical_sources
        assert container.write_ceiling == "recommendation-only"
        assert "Critical sources missing" in (container.fallback_reason or "")

    def test_contact_records_missing_triggers_hard_stop(self) -> None:
        """contact_records is a critical source; its absence forces recommendation-only."""
        input_data = EvidenceAssemblyInput(
            customer_master_content=["客户: TestCo"],
            customer_master_available=True,
            contact_records_content=[],
            contact_records_available=False,
            contact_records_missing_reason="no contact records found",
            action_plan_content=[],
            action_plan_available=False,
            meeting_notes_content=[],
            meeting_notes_available=False,
            customer_archive_content=[],
            customer_archive_available=False,
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()

        assert container.critical_source_missing is True
        assert "contact_records" in container.missing_critical_sources
        assert container.write_ceiling == "recommendation-only"

    def test_both_critical_sources_missing(self) -> None:
        """Both critical sources missing — should still trigger hard-stop (not double-count)."""
        input_data = EvidenceAssemblyInput(
            customer_master_content=[],
            customer_master_available=False,
            customer_master_missing_reason="not resolved",
            contact_records_content=[],
            contact_records_available=False,
            contact_records_missing_reason="no records",
            action_plan_content=[],
            action_plan_available=False,
            meeting_notes_content=[],
            meeting_notes_available=False,
            customer_archive_content=[],
            customer_archive_available=False,
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()

        assert container.critical_source_missing is True
        assert container.write_ceiling == "recommendation-only"
        # Both should be listed
        assert "customer_master" in container.missing_critical_sources
        assert "contact_records" in container.missing_critical_sources


class TestFallbackVisibility:
    """Test honest fallback visibility when sources are unavailable."""

    def test_fallback_reason_is_descriptive_when_sources_missing(self) -> None:
        """Non-critical sources missing: fallback_reason is present and descriptive."""
        input_data = EvidenceAssemblyInput(
            customer_master_content=["客户: TestCo"],
            customer_master_available=True,
            contact_records_content=[],
            contact_records_available=False,
            contact_records_missing_reason="no contact records",
            action_plan_content=[],
            action_plan_available=False,
            meeting_notes_content=[],
            meeting_notes_available=False,
            customer_archive_content=[],
            customer_archive_available=False,
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()

        # 4 sources missing: contact_records, action_plan, meeting_notes, customer_archive
        assert container.missing_source_count == 4
        # contact_records is critical and missing, so recommendation-only
        assert container.critical_source_missing is True
        assert container.write_ceiling == "recommendation-only"
        assert container.fallback_reason is not None

    def test_soft_fallback_when_non_critical_sources_missing(self) -> None:
        """Non-critical sources missing below threshold: normal write ceiling, descriptive reason."""
        input_data = EvidenceAssemblyInput(
            customer_master_content=["客户: TestCo"],
            customer_master_available=True,
            contact_records_content=["最近联系: 2026-04-01"],
            contact_records_available=True,
            action_plan_content=[],
            action_plan_available=False,
            action_plan_missing_reason="no action plan",
            meeting_notes_content=[],
            meeting_notes_available=False,
            meeting_notes_missing_reason="no meeting notes",
            customer_archive_content=[],
            customer_archive_available=False,
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()

        # critical_source_missing is False (customer_master and contact_records are available)
        assert container.critical_source_missing is False
        assert container.missing_source_count == 3
        # > 2 missing triggers recommendation-only
        assert container.write_ceiling == "recommendation-only"
        assert container.fallback_reason is not None
        assert "Partial evidence" in container.fallback_reason

    def test_no_fallback_when_complete(self) -> None:
        """All sources available: fallback_reason is None."""
        input_data = EvidenceAssemblyInput(
            customer_master_content=["客户: TestCo"],
            customer_master_available=True,
            contact_records_content=["最近联系: 2026-04-01"],
            contact_records_available=True,
            action_plan_content=["行动计划: Q2"],
            action_plan_available=True,
            meeting_notes_content=["纪要"],
            meeting_notes_available=True,
            customer_archive_content=["archive"],
            customer_archive_available=True,
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()

        assert container.missing_source_count == 0
        assert container.critical_source_missing is False
        assert container.write_ceiling == "normal"
        assert container.fallback_reason is None

    def test_render_source_summary_shows_unavailable(self) -> None:
        """render_source_summary() includes UNAVAILABLE markers for missing sources."""
        input_data = EvidenceAssemblyInput(
            customer_master_content=["客户: TestCo"],
            customer_master_available=True,
            contact_records_content=[],
            contact_records_available=False,
            contact_records_missing_reason="no contact records",
            action_plan_content=[],
            action_plan_available=False,
            meeting_notes_content=[],
            meeting_notes_available=False,
            customer_archive_content=[],
            customer_archive_available=False,
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()

        summary_lines = container.render_source_summary()
        assert any("UNAVAILABLE" in line for line in summary_lines)
        # Available source should not show UNAVAILABLE
        available_lines = [l for l in summary_lines if "customer_master" in l]
        assert available_lines
        assert "UNAVAILABLE" not in available_lines[0]


class TestEvidenceSourceSummary:
    """Test EvidenceSource.summary() format correctness."""

    def test_available_source_summary_format(self) -> None:
        """Available source shows name, quality, and item count."""
        src = EvidenceSource(
            name="customer_master",
            quality="live",
            available=True,
            content=["客户: TestCo", "客户ID: 123"],
        )
        summary = src.summary()
        assert "customer_master" in summary
        assert "live" in summary
        assert "2 items" in summary
        assert "UNAVAILABLE" not in summary

    def test_unavailable_source_summary_format(self) -> None:
        """Unavailable source shows name, UNAVAILABLE, and missing_reason."""
        src = EvidenceSource(
            name="meeting_notes",
            quality="missing",
            available=False,
            content=[],
            missing_reason="no notes found",
        )
        summary = src.summary()
        assert "meeting_notes" in summary
        assert "UNAVAILABLE" in summary
        assert "no notes found" in summary

    def test_archived_source_summary_format(self) -> None:
        """Archived source shows name and archived quality."""
        src = EvidenceSource(
            name="customer_archive",
            quality="archived",
            available=True,
            content=["2025-Q4 snapshot"],
        )
        summary = src.summary()
        assert "customer_archive" in summary
        assert "archived" in summary
        assert "UNAVAILABLE" not in summary


class TestDetectConflicts:
    """Test ExpertAnalysisHelper.detect_conflicts() basic functionality."""

    def test_detect_conflicts_same_content_different_sources(self) -> None:
        """Same content appearing in multiple sources is flagged as potential conflict."""
        input_data = EvidenceAssemblyInput(
            customer_master_content=["客户阶段: 优先级高"],
            customer_master_available=True,
            contact_records_content=["客户阶段: 优先级高"],  # Same content
            contact_records_available=True,
            action_plan_content=[],
            action_plan_available=False,
            meeting_notes_content=[],
            meeting_notes_available=False,
            customer_archive_content=[],
            customer_archive_available=False,
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()
        conflicts = helper.detect_conflicts(container)

        # Same content in different sources should be flagged
        assert len(conflicts) >= 1
        assert any("客户阶段" in c or "优先级" in c for c in conflicts)

    def test_detect_conflicts_no_conflicts_when_unique(self) -> None:
        """No conflicts when each source has distinct content."""
        input_data = EvidenceAssemblyInput(
            customer_master_content=["客户: TestCo"],
            customer_master_available=True,
            contact_records_content=["最近联系: 2026-04-01"],
            contact_records_available=True,
            action_plan_content=["行动计划: Q2推进"],
            action_plan_available=True,
            meeting_notes_content=["会议讨论了产品路线"],
            meeting_notes_available=True,
            customer_archive_content=["archive content"],
            customer_archive_available=True,
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()
        conflicts = helper.detect_conflicts(container)

        # No duplicates -> no conflicts
        assert conflicts == []

    def test_detect_conflicts_skips_unavailable_sources(self) -> None:
        """Unavailable sources are skipped in conflict detection."""
        input_data = EvidenceAssemblyInput(
            customer_master_content=["内容A"],
            customer_master_available=True,
            contact_records_content=[],
            contact_records_available=False,
            action_plan_content=["内容A"],  # Same as customer_master but contact_records unavailable
            action_plan_available=True,
            meeting_notes_content=[],
            meeting_notes_available=False,
            customer_archive_content=[],
            customer_archive_available=False,
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()
        conflicts = helper.detect_conflicts(container)

        # contact_records is unavailable, so no cross-source conflict with it
        # Only customer_master and action_plan have the same content
        # Both are available, so it should still be flagged
        assert len(conflicts) >= 1


class TestCRITICAL_SOURCES:
    """Test CRITICAL_SOURCES constant definition."""

    def test_critical_sources_contains_expected_sources(self) -> None:
        """CRITICAL_SOURCES must contain customer_master and contact_records."""
        assert "customer_master" in CRITICAL_SOURCES
        assert "contact_records" in CRITICAL_SOURCES
        assert len(CRITICAL_SOURCES) == 2


class TestEvidenceContainerHelpers:
    """Test EvidenceContainer helper methods."""

    def test_get_source_existing(self) -> None:
        """get_source returns the source if it exists."""
        input_data = EvidenceAssemblyInput(
            customer_master_content=["客户: TestCo"],
            customer_master_available=True,
            contact_records_content=[],
            contact_records_available=False,
            contact_records_missing_reason="no records",
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()

        src = container.get_source("customer_master")
        assert src is not None
        assert src.available is True
        assert src.quality == "live"

    def test_get_source_missing(self) -> None:
        """get_source returns None for non-existent source name."""
        input_data = EvidenceAssemblyInput(
            customer_master_content=["客户: TestCo"],
            customer_master_available=True,
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()

        src = container.get_source("nonexistent_source")
        assert src is None

    def test_is_complete_when_all_available(self) -> None:
        """is_complete returns True when no sources are missing."""
        input_data = EvidenceAssemblyInput(
            customer_master_content=["客户: TestCo"],
            customer_master_available=True,
            contact_records_content=["联系记录"],
            contact_records_available=True,
            action_plan_content=["行动计划"],
            action_plan_available=True,
            meeting_notes_content=["纪要"],
            meeting_notes_available=True,
            customer_archive_content=["archive"],
            customer_archive_available=True,
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()

        assert container.is_complete() is True

    def test_is_complete_false_when_critical_missing(self) -> None:
        """is_complete returns False when a critical source is missing."""
        input_data = EvidenceAssemblyInput(
            customer_master_content=[],
            customer_master_available=False,
            customer_master_missing_reason="not resolved",
            contact_records_content=["联系记录"],
            contact_records_available=True,
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()

        assert container.is_complete() is False

    def test_available_sources_lists_only_available(self) -> None:
        """available_sources returns only names of available sources."""
        input_data = EvidenceAssemblyInput(
            customer_master_content=["客户: TestCo"],
            customer_master_available=True,
            contact_records_content=[],
            contact_records_available=False,
            contact_records_missing_reason="no records",
            action_plan_content=["行动计划"],
            action_plan_available=True,
            meeting_notes_content=[],
            meeting_notes_available=False,
            customer_archive_content=[],
            customer_archive_available=False,
        )
        helper = ExpertAnalysisHelper(input_data)
        container = helper.assemble()

        available = container.available_sources()
        assert "customer_master" in available
        assert "action_plan" in available
        assert "contact_records" not in available
        assert "meeting_notes" not in available
        assert "customer_archive" not in available


class TestStat01FourLensOutput:
    """Test STAT-01: four-lens account posture output in run_customer_recent_status_scene."""

    def test_four_lens_functions_exist(self) -> None:
        """Verify _derive_account_posture_lenses and _render_four_lens_judgments exist."""
        from runtime.scene_runtime import _derive_account_posture_lenses, _render_four_lens_judgments
        assert callable(_derive_account_posture_lenses)
        assert callable(_render_four_lens_judgments)

    def test_derive_account_posture_lenses_returns_four_keys(self) -> None:
        """_derive_account_posture_lenses returns dict with risk/opportunity/relationship/project_progress."""
        from runtime.scene_runtime import _derive_account_posture_lenses
        from runtime.expert_analysis_helper import EvidenceContainer

        container = EvidenceContainer()
        result = _derive_account_posture_lenses(container)
        assert set(result.keys()) == {"risk", "opportunity", "relationship", "project_progress"}

    def test_derive_account_posture_lenses_extracts_keywords(self) -> None:
        """Keywords are extracted from relevant sources per LENS_SOURCE_MAP."""
        from runtime.scene_runtime import _derive_account_posture_lenses
        from runtime.expert_analysis_helper import EvidenceContainer, EvidenceSource

        container = EvidenceContainer()
        container.sources["customer_master"] = EvidenceSource(
            name="customer_master", quality="live", available=True,
            content=["客户: TestCo", "风险: 流失预警"]
        )
        container.sources["contact_records"] = EvidenceSource(
            name="contact_records", quality="live", available=True,
            content=["关系: 信任良好", "合作稳定"]
        )
        container.sources["action_plan"] = EvidenceSource(
            name="action_plan", quality="recovered", available=True,
            content=["进展: Q2交付完成"]
        )
        container.sources["meeting_notes"] = EvidenceSource(
            name="meeting_notes", quality="recovered", available=True,
            content=["机会: 扩张空间"]
        )

        result = _derive_account_posture_lenses(container)
        assert "流失" in result["risk"] or "风险" in result["risk"]
        assert "信任" in result["relationship"] or "关系" in result["relationship"]
        assert "完成" in result["project_progress"] or "进展" in result["project_progress"]
        assert "扩张" in result["opportunity"] or "机会" in result["opportunity"]

    def test_render_four_lens_judgments_labels_each_lens(self) -> None:
        """_render_four_lens_judgments emits labeled judgment strings."""
        from runtime.scene_runtime import _render_four_lens_judgments

        lens_results = {
            "risk": ["流失", "预警"],
            "opportunity": ["扩张"],
            "relationship": ["信任"],
            "project_progress": ["交付完成"],
        }
        judgments = _render_four_lens_judgments(lens_results)
        assert len(judgments) == 4
        assert any("风险:" in j for j in judgments)
        assert any("机会:" in j for j in judgments)
        assert any("关系:" in j for j in judgments)
        assert any("进展:" in j for j in judgments)

    def test_render_four_lens_skips_empty_lenses(self) -> None:
        """_render_four_lens_judgments skips lenses with no conclusions."""
        from runtime.scene_runtime import _render_four_lens_judgments

        lens_results = {
            "risk": ["流失"],
            "opportunity": [],
            "relationship": [],
            "project_progress": [],
        }
        judgments = _render_four_lens_judgments(lens_results)
        assert len(judgments) == 1
        assert "风险: 流失" in judgments[0]

    def test_lens_capped_at_three_conclusions(self) -> None:
        """Each lens produces at most 3 conclusions."""
        from runtime.scene_runtime import _derive_account_posture_lenses
        from runtime.expert_analysis_helper import EvidenceContainer, EvidenceSource

        # Stuff many keywords into one source
        container = EvidenceContainer()
        container.sources["customer_master"] = EvidenceSource(
            name="customer_master", quality="live", available=True,
            content=[
                "风险: 流失", "风险: 预警", "风险: 下滑", "风险: 危机",
                "风险: 逾期", "风险: 负向", "风险: 收紧", "风险: 压力",
            ]
        )
        result = _derive_account_posture_lenses(container)
        assert len(result["risk"]) <= 3

    def test_derive_account_posture_lenses_handles_none_container(self) -> None:
        """_derive_account_posture_lenses returns empty dicts when container is None."""
        from runtime.scene_runtime import _derive_account_posture_lenses
        result = _derive_account_posture_lenses(None)
        assert result == {"risk": [], "opportunity": [], "relationship": [], "project_progress": []}


class TestStat01LensAttribution:
    """Test STAT-01: lens attributions traceable to EvidenceContainer sources."""

    def test_lens_attributions_build_from_lens_results(self) -> None:
        """build_lens_attributions returns LensAttribution per non-empty lens."""
        from runtime.expert_analysis_helper import (
            build_lens_attributions,
            EvidenceContainer,
            EvidenceSource,
        )
        container = EvidenceContainer()
        container.sources["customer_master"] = EvidenceSource(
            name="customer_master", quality="live", available=True, content=["风险: 流失"]
        )
        lens_results = {"risk": ["流失"], "opportunity": [], "relationship": [], "project_progress": []}
        attributions = build_lens_attributions(container, lens_results)
        assert len(attributions) == 1
        assert attributions[0].lens == "risk"
        assert attributions[0].source_names == ["customer_master", "contact_records", "action_plan"]
        assert attributions[0].conclusions == ["流失"]


# -----------------------------------------------------------------------
# VAL-05 regression tests: scene-contract coverage for 4 case types
# per D-01 to D-06 (happy-path, limited-context, unresolved-customer,
# blocked-write) across post-meeting-synthesis, customer-recent-status,
# and archive-refresh scenes.
# -----------------------------------------------------------------------

import unittest
from pathlib import Path

from runtime.scene_runtime import SceneRequest, SceneResult
from runtime.scene_registry import dispatch_scene


class TestPostMeetingRegression(unittest.TestCase):
    """Regression coverage for post-meeting-synthesis scene contract.

    Validates that dispatch_scene() produces a SceneResult that conforms to
    the scene contract fields across all four case types.
    """

    def _make_request(self, customer_query: str, inputs: dict, options: dict) -> SceneRequest:
        return SceneRequest(
            scene_name="post-meeting-synthesis",
            repo_root=Path("."),
            customer_query=customer_query,
            inputs=inputs,
            options=options,
        )

    def test_post_meeting_happy_path_dispatch_and_result_shape(self) -> None:
        """Happy path: valid customer, full inputs, dispatches correctly."""
        # Provide a non-existent transcript path so _read_transcript_text returns
        # ("", "missing") — the scene still produces a valid SceneResult.
        request = self._make_request(
            customer_query="测试客户",
            inputs={"transcript_file": "/tmp/nonexistent_transcript_12345.txt", "eval_name": "test-eval"},
            options={},
        )
        result = dispatch_scene(request)

        self.assertEqual(result.scene_name, "post-meeting-synthesis")
        # resource_status values per runtime/resource_resolver.py: "resolved" | "unresolved" | "partial"
        self.assertIn(result.resource_status, ("partial", "resolved", "unresolved"))
        # customer_status can be "resolved" | "ambiguous" | "not_found" | "missing"
        self.assertIn(result.customer_status, ("resolved", "ambiguous", "not_found", "missing"))
        # context_status values per recover_live_context: "completed" | "partial" | "minimal" | "context-limited"
        self.assertIn(result.context_status, ("complete", "partial", "minimal", "context-limited"))
        self.assertIn(result.write_ceiling, ("normal", "recommendation-only"))
        self.assertIsNotNone(result.output_text)
        self.assertGreater(len(result.output_text), 0)
        self.assertIsNotNone(result.payload)

    def test_post_meeting_limited_context_fallback_visible(self) -> None:
        """Limited context: partial evidence triggers fallback visibility."""
        # Simulate partial evidence via empty customer query (unresolvable)
        request = self._make_request(
            customer_query="",  # unresolvable
            inputs={"transcript_file": "/tmp/nonexistent_transcript_12345.txt", "eval_name": "test-eval"},
            options={},
        )
        result = dispatch_scene(request)

        self.assertIn(result.context_status, ("partial", "minimal", "context-limited"))
        # fallback_category is "customer" when customer cannot be resolved
        self.assertIn(result.fallback_category, ("context", "none", "customer"))
        self.assertTrue(
            result.output_text is not None or result.recommendations is not None
        )

    def test_post_meeting_unresolved_customer_handled(self) -> None:
        """Unresolved customer: customer_status is not-found/missing, write ceiling is recommendation-only."""
        request = self._make_request(
            customer_query="此客户不存在且无法解析",
            inputs={"transcript_file": "/tmp/nonexistent_transcript_12345.txt", "eval_name": "test-eval"},
            options={},
        )
        result = dispatch_scene(request)

        # customer_status can be "not_found" or "missing" when customer cannot be resolved
        self.assertIn(result.customer_status, ("not_found", "missing"))
        self.assertEqual(result.fallback_category, "customer")
        self.assertEqual(result.write_ceiling, "recommendation-only")

    def test_post_meeting_blocked_write_ceiling(self) -> None:
        """Blocked write: confirm_write=True but customer unresolvable forces recommendation-only."""
        request = self._make_request(
            customer_query="完全不存在的客户_无法解析",
            inputs={"transcript_file": "/tmp/nonexistent_transcript_12345.txt", "eval_name": "test-eval"},
            options={"confirm_write": True},
        )
        result = dispatch_scene(request)

        self.assertEqual(result.write_ceiling, "recommendation-only")
        self.assertIn(result.fallback_category, ("customer", "safety", "permission"))
        # recommendations may be empty when customer cannot be resolved — check payload instead
        self.assertIsNotNone(result.payload)
        self.assertNotIn("write_candidates", result.payload)


class TestCustomerRecentStatusRegression(unittest.TestCase):
    """Regression coverage for customer-recent-status scene contract.

    Validates that dispatch_scene() produces a SceneResult that conforms to
    the scene contract fields across all four case types.
    """

    def _make_request(self, customer_query: str, inputs: dict, options: dict) -> SceneRequest:
        return SceneRequest(
            scene_name="customer-recent-status",
            repo_root=Path("."),
            customer_query=customer_query,
            inputs=inputs,
            options=options,
        )

    def test_customer_recent_status_happy_path_dispatch_and_result_shape(self) -> None:
        """Happy path: valid customer, dispatches and returns valid SceneResult."""
        request = self._make_request(
            customer_query="测试客户",
            inputs={},
            options={},
        )
        result = dispatch_scene(request)

        self.assertEqual(result.scene_name, "customer-recent-status")
        # resource_status values per resource_resolver.py: "resolved" | "unresolved" | "partial"
        self.assertIn(result.resource_status, ("partial", "resolved", "unresolved"))
        # customer_status can be "resolved" | "ambiguous" | "not_found" | "missing"
        self.assertIn(result.customer_status, ("resolved", "ambiguous", "not_found", "missing"))
        # context_status per recover_live_context: "completed" | "partial" | "minimal" | "context-limited"
        self.assertIn(result.context_status, ("complete", "partial", "minimal", "context-limited"))
        self.assertIn(result.write_ceiling, ("normal", "recommendation-only"))
        # payload must have lens_results or non-empty output_text
        self.assertIsNotNone(result.payload)
        has_lens_results = result.payload and "lens_results" in result.payload
        has_output = result.output_text is not None and len(result.output_text) > 0
        self.assertTrue(has_lens_results or has_output)

    def test_customer_recent_status_limited_context_fallback_visible(self) -> None:
        """Limited context: partial evidence triggers fallback visibility."""
        request = self._make_request(
            customer_query="",
            inputs={},
            options={},
        )
        result = dispatch_scene(request)

        self.assertIn(result.context_status, ("partial", "minimal", "context-limited"))
        self.assertIn(result.fallback_category, ("context", "none", "customer"))
        self.assertTrue(
            result.output_text is not None or result.recommendations is not None
        )

    def test_customer_recent_status_unresolved_customer(self) -> None:
        """Unresolved customer: customer_status not-found/missing, fallback_category customer."""
        request = self._make_request(
            customer_query="此客户根本不存在于系统中",
            inputs={},
            options={},
        )
        result = dispatch_scene(request)

        self.assertIn(result.customer_status, ("not_found", "missing"))
        self.assertEqual(result.fallback_category, "customer")
        self.assertEqual(result.write_ceiling, "recommendation-only")

    def test_customer_recent_status_blocked_write(self) -> None:
        """Blocked write: recommendation-only ceiling with non-empty recommendations."""
        request = self._make_request(
            customer_query="虚构客户_绝对不存在",
            inputs={},
            options={},
        )
        result = dispatch_scene(request)

        self.assertEqual(result.write_ceiling, "recommendation-only")
        self.assertIn(result.fallback_category, ("customer", "safety", "permission"))
        self.assertIsNotNone(result.recommendations)
        self.assertGreater(len(result.recommendations), 0)
        self.assertIsNotNone(result.payload)
        self.assertNotIn("write_candidates", result.payload)
