"""Tests for expert_card_loader.py.

Behavior-based tests for the expert card loader:
- YAML loading and parsing
- Scene name validation (path traversal prevention)
- Graceful handling of missing scenes/cards
- Schema validation

Tests match the ExpertCardConfig-based design from plan 23-03.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# Import from runtime package
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from runtime.expert_card_loader import (
    ExpertCardConfig,
    VALID_SCENES,
    validate_scene_name,
    validate_card_schema,
    load_yaml_config,
    load_expert_cards,
)


class TestValidSceneNames:
    """BEHAVIOR: Known scenes are recognized."""

    def test_valid_scenes_is_frozenset(self):
        """VALID_SCENES should be a frozenset."""
        assert isinstance(VALID_SCENES, frozenset)

    def test_valid_scene_names_recognized(self):
        """VALID_SCENES should contain the 7 expected scene names."""
        expected = frozenset({
            "post-meeting-synthesis",
            "customer-recent-status",
            "archive-refresh",
            "todo-capture-and-update",
            "cohort-scan",
            "meeting-prep",
            "proposal",
        })
        assert VALID_SCENES == expected

    def test_validate_scene_name_returns_bool(self):
        """validate_scene_name returns True/False, not the name."""
        assert validate_scene_name("post-meeting-synthesis") is True
        assert validate_scene_name("invalid-scene") is False


class TestValidateCardSchema:
    """Schema validation tests."""

    def test_valid_card_passes(self):
        """A valid card with all required fields passes validation."""
        card = {
            "enabled": True,
            "expert_name": "测试专家",
            "review_type": "test_audit",
            "check_signals": ["signal1", "signal2"],
            "output_field": "test_output",
        }
        is_valid, err = validate_card_schema(card, "input_review")
        assert is_valid is True
        assert err is None

    def test_missing_expert_name_fails(self):
        """Missing expert_name fails validation."""
        card = {
            "enabled": True,
            "review_type": "test_audit",
            "check_signals": ["signal1"],
            "output_field": "test_output",
        }
        is_valid, err = validate_card_schema(card, "input_review")
        assert is_valid is False
        assert "expert_name" in err

    def test_missing_review_type_fails(self):
        """Missing review_type fails validation."""
        card = {
            "enabled": True,
            "expert_name": "测试专家",
            "check_signals": ["signal1"],
            "output_field": "test_output",
        }
        is_valid, err = validate_card_schema(card, "output_review")
        assert is_valid is False
        assert "review_type" in err

    def test_empty_check_signals_fails(self):
        """Empty check_signals list fails validation."""
        card = {
            "enabled": True,
            "expert_name": "测试专家",
            "review_type": "test_audit",
            "check_signals": [],
            "output_field": "test_output",
        }
        is_valid, err = validate_card_schema(card, "input_review")
        assert is_valid is False
        assert "at least one signal" in err

    def test_check_signals_not_list_fails(self):
        """check_signals that is not a list fails validation."""
        card = {
            "enabled": True,
            "expert_name": "测试专家",
            "review_type": "test_audit",
            "check_signals": "not-a-list",
            "output_field": "test_output",
        }
        is_valid, err = validate_card_schema(card, "output_review")
        assert is_valid is False
        assert "must be a list" in err


class TestLoadExpertCards:
    """Behavior-based tests for load_expert_cards()."""

    def test_valid_yaml_loads_success(self, tmp_path):
        """BEHAVIOR: Valid YAML with all fields parses correctly."""
        # Create scene directory structure (repo_root/scenes/scene_name)
        scene_dir = tmp_path / "scenes" / "post-meeting-synthesis"
        scene_dir.mkdir(parents=True)
        expert_cards_file = scene_dir / "expert-cards.yaml"

        # Write valid expert-cards.yaml with all required fields
        expert_cards_file.write_text(yaml.dump({
            "input_review": {
                "enabled": True,
                "expert_name": "会议材料审核专家",
                "review_type": "materials_audit",
                "check_signals": ["遗漏的关联信息", "前后不一致的事实"],
                "output_field": "input_audit_notes",
            },
            "output_review": {
                "enabled": True,
                "expert_name": "经营顾问",
                "review_type": "recommendation_audit",
                "check_signals": ["专业性", "业务逻辑"],
                "output_field": "output_audit_notes",
                "block_on_flags": ["业务逻辑错误"],
            },
        }))

        # Load cards
        cards = load_expert_cards("post-meeting-synthesis", repo_root=tmp_path)

        # Verify input_review parsed correctly
        assert cards["input_review"] is not None
        input_card = cards["input_review"]
        assert isinstance(input_card, ExpertCardConfig)
        assert input_card.expert_name == "会议材料审核专家"
        assert input_card.review_type == "materials_audit"
        assert "遗漏的关联信息" in input_card.check_signals

        # Verify output_review parsed correctly
        assert cards["output_review"] is not None
        output_card = cards["output_review"]
        assert output_card.expert_name == "经营顾问"
        assert output_card.block_on_flags == ["业务逻辑错误"]

    def test_missing_scene_returns_none_values(self, tmp_path):
        """BEHAVIOR: Missing scene is handled gracefully, no exception."""
        cards = load_expert_cards("nonexistent-scene", repo_root=tmp_path)
        assert cards["input_review"] is None
        assert cards["output_review"] is None

    def test_invalid_scene_name_returns_none(self, tmp_path):
        """BEHAVIOR: Invalid/unknown scene names handled gracefully."""
        cards = load_expert_cards("invalid-scene-name", repo_root=tmp_path)
        assert cards["input_review"] is None
        assert cards["output_review"] is None

    def test_yaml_missing_required_fields_raises(self, tmp_path):
        """BEHAVIOR: YAML missing required fields raises ValueError."""
        scene_dir = tmp_path / "scenes" / "customer-recent-status"
        scene_dir.mkdir(parents=True)
        expert_cards_file = scene_dir / "expert-cards.yaml"

        # YAML with missing required fields
        expert_cards_file.write_text(yaml.dump({
            "input_review": {
                "enabled": True,
                "review_type": "materials_audit",
                # Missing: expert_name, check_signals, output_field
            },
        }))

        with pytest.raises(ValueError, match="schema validation failed"):
            load_expert_cards("customer-recent-status", repo_root=tmp_path)

    def test_yaml_invalid_syntax_raises(self, tmp_path):
        """BEHAVIOR: Invalid YAML syntax raises yaml.YAMLError."""
        scene_dir = tmp_path / "scenes" / "cohort-scan"
        scene_dir.mkdir(parents=True)
        expert_cards_file = scene_dir / "expert-cards.yaml"

        # Invalid YAML (unclosed quote)
        expert_cards_file.write_text('input_review:\n  enabled: true\n  expert_name: "unclosed')

        with pytest.raises(yaml.YAMLError):
            load_expert_cards("cohort-scan", repo_root=tmp_path)

    def test_only_input_review_defined(self, tmp_path):
        """When only input_review is defined, output_review should be None."""
        scene_dir = tmp_path / "scenes" / "meeting-prep"
        scene_dir.mkdir(parents=True)
        expert_cards_file = scene_dir / "expert-cards.yaml"

        expert_cards_file.write_text(yaml.dump({
            "input_review": {
                "enabled": True,
                "expert_name": "会议准备专家",
                "review_type": "prep_audit",
                "check_signals": ["遗漏准备项"],
                "output_field": "prep_audit_notes",
            },
        }))

        cards = load_expert_cards("meeting-prep", repo_root=tmp_path)

        assert cards["input_review"] is not None
        assert cards["output_review"] is None

    def test_only_output_review_defined(self, tmp_path):
        """When only output_review is defined, input_review should be None."""
        scene_dir = tmp_path / "scenes" / "proposal"
        scene_dir.mkdir(parents=True)
        expert_cards_file = scene_dir / "expert-cards.yaml"

        expert_cards_file.write_text(yaml.dump({
            "output_review": {
                "enabled": True,
                "expert_name": "提案审核顾问",
                "review_type": "proposal_audit",
                "check_signals": ["完整性", "可执行性"],
                "output_field": "proposal_audit_notes",
                "block_on_flags": ["范围超出"],
            },
        }))

        cards = load_expert_cards("proposal", repo_root=tmp_path)

        assert cards["input_review"] is None
        assert cards["output_review"] is not None

    def test_disabled_input_review_returns_none(self, tmp_path):
        """When input_review.enabled=False, returns None for input."""
        scene_dir = tmp_path / "scenes" / "archive-refresh"
        scene_dir.mkdir(parents=True)
        expert_cards_file = scene_dir / "expert-cards.yaml"

        expert_cards_file.write_text(yaml.dump({
            "input_review": {
                "enabled": False,
                "expert_name": "档案审核专家",
                "review_type": "archive_audit",
                "check_signals": ["遗漏信息"],
                "output_field": "archive_notes",
            },
            "output_review": {
                "enabled": True,
                "expert_name": "经营顾问",
                "review_type": "recommendation_audit",
                "check_signals": ["专业性"],
                "output_field": "output_audit_notes",
            },
        }))

        cards = load_expert_cards("archive-refresh", repo_root=tmp_path)

        assert cards["input_review"] is None
        assert cards["output_review"] is not None

    def test_load_yaml_config(self, tmp_path):
        """load_yaml_config uses yaml.safe_load only."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("key: value\nlist:\n  - item1\n  - item2\n")

        result = load_yaml_config(yaml_file)
        assert result == {"key": "value", "list": ["item1", "item2"]}


class TestOutputAuditBlocking:
    """BEHAVIOR: block_on_flags triggers blocked=True in output audit."""

    def test_block_on_flags_triggers_blocked(self, tmp_path):
        """When block_on_flags dimension is flagged, audit_result.blocked should be True."""
        # Import here to avoid import errors if expert_analysis_helper is not available
        from runtime.expert_analysis_helper import run_output_audit

        # Create a minimal output_card with block_on_flags
        output_card = ExpertCardConfig(
            enabled=True,
            expert_name="经营顾问",
            review_type="recommendation_audit",
            check_signals=["专业性", "业务逻辑"],
            output_field="output_audit_notes",
            block_on_flags=["业务逻辑"],
        )

        # Recommendations that only address "专业性", not "业务逻辑"
        recommendations = ["建议使用规范的专业术语撰写报告"]

        result = run_output_audit(recommendations, output_card)

        assert result.blocked is True, (
            f"Expected blocked=True when block_on_flags dimension '业务逻辑' is flagged, "
            f"but got blocked={result.blocked}. findings={result.findings}"
        )

    def test_no_block_when_all_flags_pass(self, tmp_path):
        """When no block_on_flags dimensions are flagged, blocked should be False."""
        from runtime.expert_analysis_helper import run_output_audit

        output_card = ExpertCardConfig(
            enabled=True,
            expert_name="经营顾问",
            review_type="recommendation_audit",
            check_signals=["专业性", "业务逻辑"],
            output_field="output_audit_notes",
            block_on_flags=["业务逻辑"],
        )

        # Recommendations that address both dimensions
        recommendations = [
            "建议使用规范的专业术语，符合业务逻辑地进行方案设计",
        ]

        result = run_output_audit(recommendations, output_card)

        assert result.blocked is False, (
            f"Expected blocked=False when all flags pass, "
            f"but got blocked={result.blocked}. findings={result.findings}"
        )

    def test_yaml_missing_expert_cards_file_returns_none(self, tmp_path):
        """BEHAVIOR: Missing expert-cards.yaml is handled gracefully (fail-open)."""
        scene_dir = tmp_path / "scenes" / "proposal"
        scene_dir.mkdir(parents=True)
        # Note: intentionally NOT creating expert-cards.yaml
        cards = load_expert_cards("proposal", repo_root=tmp_path)
        assert cards["input_review"] is None
        assert cards["output_review"] is None
