"""Tests for ARCH-01: archive refresh five-dimension structured synthesis."""

from __future__ import annotations

import pytest

from runtime.scene_runtime import (
    _derive_archive_refresh_lenses,
    _render_archive_refresh_output,
)
from runtime.expert_analysis_helper import EvidenceContainer, EvidenceSource


class TestArchiveRefreshFiveDimension:
    """Test five-dimension output per D-01-D-02."""

    def test_derive_archive_refresh_lenses_returns_five_keys(self) -> None:
        """_derive_archive_refresh_lenses returns dict with 5 dimension keys."""
        container = EvidenceContainer()
        result = _derive_archive_refresh_lenses(container)
        assert set(result.keys()) == {
            "historical_arc", "key_people", "risk", "opportunity", "operating_posture"
        }

    def test_derive_archive_refresh_lenses_handles_none_container(self) -> None:
        """Returns empty dicts when container is None."""
        result = _derive_archive_refresh_lenses(None)
        assert all(v == [] for v in result.values())

    def test_derive_extracts_history_keywords(self) -> None:
        """Historical arc keywords extracted from customer_archive and meeting_notes."""
        container = EvidenceContainer()
        container.sources["customer_archive"] = EvidenceSource(
            name="customer_archive", quality="archived", available=True,
            content=["客户历史: 过去三年持续合作", "此前项目顺利完成"]
        )
        container.sources["meeting_notes"] = EvidenceSource(
            name="meeting_notes", quality="recovered", available=True,
            content=["历年纪要显示稳定增长"]
        )
        result = _derive_archive_refresh_lenses(container)
        assert "历史" in result["historical_arc"] or "过去" in result["historical_arc"] or "此前" in result["historical_arc"]

    def test_derive_extracts_people_keywords(self) -> None:
        """Key people keywords extracted from contact_records."""
        container = EvidenceContainer()
        container.sources["contact_records"] = EvidenceSource(
            name="contact_records", quality="live", available=True,
            content=["关键人物: 张总", "决策人: 李明"]
        )
        result = _derive_archive_refresh_lenses(container)
        assert "关键人物" in result["key_people"] or "决策人" in result["key_people"]

    def test_each_dimension_capped_at_three_conclusions(self) -> None:
        """Each dimension produces at most 3 conclusions per D-02."""
        container = EvidenceContainer()
        # Load with many keywords
        for src_name in ["customer_archive", "meeting_notes", "customer_master", "action_plan", "contact_records"]:
            container.sources[src_name] = EvidenceSource(
                name=src_name, quality="live", available=True,
                content=["历史", "过去", "此前", "之前", "历年", "历程", "往日", "以往"]
            )
        result = _derive_archive_refresh_lenses(container)
        for key, values in result.items():
            assert len(values) <= 3, f"{key} has {len(values)} items, expected max 3"

    def test_render_output_includes_all_five_dimensions(self) -> None:
        """_render_archive_refresh_output renders all 5 dimensions with labels."""
        lens_results = {
            "historical_arc": ["历史", "过去"],
            "key_people": ["关键人物"],
            "risk": ["风险"],
            "opportunity": ["机会"],
            "operating_posture": ["姿态"],
        }
        lines = _render_archive_refresh_output(lens_results)
        assert lines[0] == "--- 档案更新建议 ---"
        assert any("历史弧线" in line for line in lines)
        assert any("关键人物" in line for line in lines)
        assert any("风险" in line for line in lines)
        assert any("机会" in line for line in lines)
        assert any("运营姿态" in line for line in lines)

    def test_render_output_empty_dimensions_show_placeholder(self) -> None:
        """Empty dimensions show '暂无结论' placeholder."""
        lens_results = {k: [] for k in ["historical_arc", "key_people", "risk", "opportunity", "operating_posture"]}
        lines = _render_archive_refresh_output(lens_results)
        # Each of the 5 dimension lines must contain "暂无结论"
        assert len(lines) >= 5, f"Expected at least 5 lines, got {len(lines)}"
        placeholder_lines = [l for l in lines if "暂无结论" in l]
        assert len(placeholder_lines) == 5, f"Expected 5 placeholder lines, got {len(placeholder_lines)}"


class TestArchiveRefreshDistinctFormat:
    """Test ARCH-01 is distinct from Phase 17/18 formats per D-03."""

    def test_five_dimensions_different_from_stat01_four_lens(self) -> None:
        """ARCH-01 uses 5 dimensions, STAT-01 uses 4 lenses — format is distinct."""
        from runtime.scene_runtime import _derive_account_posture_lenses
        arch_result = _derive_archive_refresh_lenses(EvidenceContainer())
        stat_result = _derive_account_posture_lenses(EvidenceContainer())
        # ARCH-01 has 5 keys, STAT-01 has 4 keys
        assert len(arch_result.keys()) == 5
        assert len(stat_result.keys()) == 4
        # Keys are different
        assert arch_result.keys() != stat_result.keys()

    def test_output_header_is_archive_specific(self) -> None:
        """Archive refresh output uses '--- 档案更新建议 ---' header per UI-SPEC."""
        lines = _render_archive_refresh_output({k: [] for k in ["historical_arc", "key_people", "risk", "opportunity", "operating_posture"]})
        assert lines[0] == "--- 档案更新建议 ---"


# -----------------------------------------------------------------------
# VAL-05 regression tests: scene-contract coverage for archive-refresh
# per D-01 to D-06 (happy-path, limited-context, unresolved-customer,
# blocked-write).
# -----------------------------------------------------------------------

import unittest
from pathlib import Path

from runtime.scene_runtime import SceneRequest
from runtime.scene_registry import dispatch_scene


class TestArchiveRefreshRegression(unittest.TestCase):
    """Regression coverage for archive-refresh scene contract.

    Validates that dispatch_scene() produces a SceneResult that conforms to
    the scene contract fields across all four case types.
    """

    def _make_request(self, customer_query: str, inputs: dict, options: dict) -> SceneRequest:
        return SceneRequest(
            scene_name="archive-refresh",
            repo_root=Path("."),
            customer_query=customer_query,
            inputs=inputs,
            options=options,
        )

    def test_archive_refresh_happy_path_dispatch_and_result_shape(self) -> None:
        """Happy path: valid customer, dispatches and returns valid SceneResult."""
        request = self._make_request(
            customer_query="测试客户",
            inputs={},
            options={},
        )
        result = dispatch_scene(request)

        self.assertEqual(result.scene_name, "archive-refresh")
        # resource_status from gateway: "resolved" | "partial" | "unresolved"
        self.assertIn(result.resource_status, ("resolved", "partial", "unresolved"))
        # customer_status can be "resolved" | "ambiguous" | "not_found" | "missing"
        self.assertIn(result.customer_status, ("resolved", "ambiguous", "not_found", "missing"))
        # context_status per recover_live_context: "completed" | "partial" | "minimal" | "context-limited"
        self.assertIn(result.context_status, ("not-run", "completed", "partial", "context-limited"))
        self.assertIn(result.write_ceiling, ("normal", "recommendation-only"))
        self.assertIsNotNone(result.payload)
        self.assertGreater(len(result.payload), 0)

    def test_archive_refresh_limited_context_fallback_visible(self) -> None:
        """Limited context: partial evidence triggers fallback visibility."""
        request = self._make_request(
            customer_query="",
            inputs={},
            options={},
        )
        result = dispatch_scene(request)

        self.assertIn(result.context_status, ("not-run", "completed", "partial", "context-limited"))
        self.assertIn(result.fallback_category, ("context", "none", "customer"))
        self.assertTrue(
            result.output_text is not None or result.recommendations is not None
        )

    def test_archive_refresh_unresolved_customer(self) -> None:
        """Unresolved customer: customer_status not-found/missing, fallback_category customer."""
        request = self._make_request(
            customer_query="此客户不存在于任何系统中",
            inputs={},
            options={},
        )
        result = dispatch_scene(request)

        self.assertIn(result.customer_status, ("not_found", "missing"))
        self.assertEqual(result.fallback_category, "customer")
        self.assertEqual(result.write_ceiling, "recommendation-only")

    def test_archive_refresh_blocked_write(self) -> None:
        """Blocked write: recommendation-only ceiling with non-empty recommendations."""
        request = self._make_request(
            customer_query="虚构客户_绝对不存在于系统",
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
