"""Tests for WRITE-02: confirmation checklist infrastructure."""

from __future__ import annotations

import pytest

from runtime.confirmation_checklist import (
    ConfirmationChecklist,
    ChecklistItem,
    build_archive_refresh_checklist,
    build_meeting_prep_checklist,
    render_confirmation_checklist,
)
from runtime.expert_analysis_helper import EvidenceContainer, EvidenceSource


class TestWrite02Checklist:
    """Test WRITE-02 universal checklist items per D-10 through D-13."""

    def test_archive_refresh_checklist_has_universal_items(self) -> None:
        """Archive refresh checklist includes all 4 WRITE-02 universal items per D-13."""
        checklist = build_archive_refresh_checklist(None, None)
        assert checklist.audience is not None
        assert checklist.purpose is not None
        assert checklist.internal_external is not None
        assert checklist.resource_coordination is not None

    def test_meeting_prep_checklist_has_universal_items(self) -> None:
        """Meeting prep checklist includes all 4 WRITE-02 universal items per D-16."""
        checklist = build_meeting_prep_checklist(None, None)
        assert checklist.audience is not None
        assert checklist.purpose is not None
        assert checklist.internal_external is not None
        assert checklist.resource_coordination is not None

    def test_audience_item_has_required_fields(self) -> None:
        """Audience item has key, label, and system_suggestion per D-13."""
        checklist = build_archive_refresh_checklist(None, None)
        assert checklist.audience.key == "audience"
        assert checklist.audience.label == "受众"
        assert isinstance(checklist.audience.system_suggestion, str)

    def test_checklist_confirmed_answers_returns_dict(self) -> None:
        """confirmed_answers() returns dict of all confirmed values."""
        checklist = build_archive_refresh_checklist(None, None)
        answers = checklist.confirmed_answers()
        assert isinstance(answers, dict)
        assert "audience" in answers
        assert "purpose" in answers
        assert "internal_external" in answers
        assert "resource_coordination" in answers

    def test_archive_refresh_scene_name(self) -> None:
        """Archive refresh checklist has scene_name='archive-refresh'."""
        checklist = build_archive_refresh_checklist(None, None)
        assert checklist.scene_name == "archive-refresh"

    def test_meeting_prep_scene_name(self) -> None:
        """Meeting prep checklist has scene_name='meeting-prep'."""
        checklist = build_meeting_prep_checklist(None, None)
        assert checklist.scene_name == "meeting-prep"

    def test_archive_refresh_has_scene_specific_items(self) -> None:
        """Archive refresh checklist has scene-specific items per D-14, D-15."""
        checklist = build_archive_refresh_checklist(None, None)
        item_keys = [item.key for item in checklist.items]
        assert "refresh_type" in item_keys
        assert "archive_location" in item_keys
        assert "key_people_sync" in item_keys

    def test_meeting_prep_has_meeting_type_suggestion(self) -> None:
        """Meeting prep checklist has meeting_type_suggestion per D-17."""
        checklist = build_meeting_prep_checklist(None, None)
        item_keys = [item.key for item in checklist.items]
        assert "meeting_type_suggestion" in item_keys
        assert "agenda_suggestion" in item_keys


class TestMinimalQuestions:
    """Test minimal-questions principle per D-11."""

    def test_checklist_with_none_evidence_container_still_builds(self) -> None:
        """build_*_checklist() works when evidence_container is None per D-11."""
        checklist = build_archive_refresh_checklist(None, None)
        assert checklist is not None
        assert checklist.scene_name == "archive-refresh"

    def test_system_suggestions_provided_for_all_items(self) -> None:
        """All checklist items have system_suggestion (system infers, not asks) per D-11."""
        checklist = build_archive_refresh_checklist(None, None)
        for item in checklist.items:
            assert item.system_suggestion, f"Item {item.key} has no system suggestion"

    def test_universal_items_have_suggestions(self) -> None:
        """Universal WRITE-02 items always have system_suggestion (no free-form input) per D-11."""
        checklist = build_meeting_prep_checklist(None, None)
        for item in [checklist.audience, checklist.purpose, checklist.internal_external, checklist.resource_coordination]:
            if item:
                assert item.system_suggestion, f"Universal item {item.key} has no suggestion"

    def test_render_output_includes_scene_header(self) -> None:
        """render_confirmation_checklist output starts with scene header per UI-SPEC."""
        checklist = build_archive_refresh_checklist(None, None)
        lines = render_confirmation_checklist(checklist)
        assert lines[0] == "=== archive-refresh确认清单 ==="

    def test_render_output_includes_all_items(self) -> None:
        """Rendered checklist includes all checklist items."""
        checklist = build_meeting_prep_checklist(None, None)
        lines = render_confirmation_checklist(checklist)
        content = "\n".join(lines)
        assert "受众" in content
        assert "目的" in content
        assert "内部/外部" in content
        assert "资源协调" in content
        assert "会议类型" in content

    def test_render_output_includes_continue_prompt(self) -> None:
        """Rendered checklist ends with continue prompt per UI-SPEC."""
        checklist = build_archive_refresh_checklist(None, None)
        lines = render_confirmation_checklist(checklist)
        assert any("输入 q 退出" in line for line in lines)

    def test_checklist_item_confirmed_value_prefers_modification(self) -> None:
        """ChecklistItem.confirmed_value() returns modification if provided."""
        item = ChecklistItem(
            key="test",
            label="Test",
            system_suggestion="default",
            user_modification="modified",
        )
        assert item.confirmed_value() == "modified"

    def test_checklist_item_confirmed_value_falls_back_to_suggestion(self) -> None:
        """ChecklistItem.confirmed_value() returns suggestion if no modification."""
        item = ChecklistItem(
            key="test",
            label="Test",
            system_suggestion="default",
        )
        assert item.confirmed_value() == "default"
