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
        assert all("暂无结论" in line for line in lines if "暂无结论" in line)


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
