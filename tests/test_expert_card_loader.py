"""Tests for expert_card_loader.py.

Behavior-based tests for the expert card loader:
- YAML loading and parsing
- Scene name validation (path traversal prevention)
- Graceful handling of missing scenes/cards
- Schema validation
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# Import from runtime package
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from runtime.expert_card_loader import (
    ExpertCards,
    InputReviewCard,
    OutputReviewCard,
    VALID_SCENES,
    _validate_scene_name,
    _safe_load_yaml,
    load_expert_cards,
    YAMLParseError,
)


class TestValidSceneNamesRecognized:
    """BEHAVIOR: Known scenes are recognized."""

    def test_valid_scene_names_recognized(self):
        """VALID_SCENES should contain the 7 expected scene names."""
        expected_scenes = [
            "post-meeting-synthesis",
            "customer-recent-status",
            "archive-refresh",
            "todo-capture-and-update",
            "cohort-scan",
            "meeting-prep",
            "proposal",
        ]
        assert VALID_SCENES == expected_scenes, (
            f"VALID_SCENES mismatch. Expected {expected_scenes}, got {VALID_SCENES}"
        )

    def test_valid_scene_names_all_strings(self):
        """All VALID_SCENES entries should be strings."""
        for scene in VALID_SCENES:
            assert isinstance(scene, str), f"Scene name {scene} is not a string"
            assert len(scene) > 0, "Scene name cannot be empty"


class TestValidateSceneName:
    """Path traversal prevention tests."""

    def test_valid_scene_name_returns_same(self):
        """Valid scene names should pass through unchanged."""
        assert _validate_scene_name("post-meeting-synthesis") == "post-meeting-synthesis"
        assert _validate_scene_name("cohort-scan") == "cohort-scan"

    def test_path_traversal_attempt_blocked(self):
        """Path traversal patterns should be rejected."""
        dangerous_names = [
            "../etc/passwd",
            "post-meeting-synthesis/../../../etc/passwd",
            "post-meeting-synthesis\\..\\..\\etc",
            "~/.ssh/id_rsa",
            "$HOME/file",
            "`whoami`",
            "; rm -rf",
            "& ls",
            "| cat",
        ]
        for name in dangerous_names:
            with pytest.raises(ValueError, match="Invalid scene name|contains dangerous pattern"):
                _validate_scene_name(name)

    def test_unknown_scene_passes_validation(self):
        """Unknown scene names pass _validate_scene_name (handled gracefully later).

        _validate_scene_name only blocks path traversal. Unknown/unregistered
        scenes are handled gracefully by load_expert_cards returning None values.
        """
        # These should NOT raise - unknown scenes pass validation
        assert _validate_scene_name("nonexistent-scene") == "nonexistent-scene"
        assert _validate_scene_name("invalid-scene") == "invalid-scene"


class TestSafeYamlLoad:
    """YAML parsing safety tests."""

    def test_valid_yaml_loads_success(self, tmp_path):
        """Valid YAML should parse successfully."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("key: value\nlist:\n  - item1\n  - item2\n")

        result = _safe_load_yaml(yaml_file)
        assert result == {"key": "value", "list": ["item1", "item2"]}

    def test_invalid_yaml_syntax_raises(self, tmp_path):
        """Invalid YAML syntax should raise YAMLParseError."""
        yaml_file = tmp_path / "invalid.yaml"
        # Unclosed quote - invalid YAML
        yaml_file.write_text('key: "unclosed quote\nanother: value')

        with pytest.raises(YAMLParseError):
            _safe_load_yaml(yaml_file)

    def test_empty_yaml_returns_empty_dict(self, tmp_path):
        """Empty YAML file should return empty dict."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("")

        result = _safe_load_yaml(yaml_file)
        assert result == {}

    def test_yaml_with_comments_loads(self, tmp_path):
        """YAML with comments should parse correctly."""
        yaml_file = tmp_path / "with_comments.yaml"
        yaml_file.write_text("# This is a comment\nkey: value  # inline comment\n")

        result = _safe_load_yaml(yaml_file)
        assert result == {"key": "value"}


class TestLoadExpertCards:
    """Behavior-based tests for load_expert_cards()."""

    def test_valid_yaml_loads_success(self, tmp_path):
        """BEHAVIOR: Valid YAML with all fields parses correctly."""
        # Create scene directory structure
        scene_dir = tmp_path / "post-meeting-synthesis"
        scene_dir.mkdir()
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
                "enabled": False,  # Disabled for this scene
                "expert_name": "经营顾问",
                "review_type": "recommendation_audit",
                "check_dimensions": ["专业性", "业务逻辑"],
                "output_field": "output_audit_notes",
                "block_on_flags": ["业务逻辑错误"],
            },
        }))

        # Load cards
        cards = load_expert_cards("post-meeting-synthesis", scenes_dir=tmp_path)

        # Verify input_review parsed correctly
        assert cards.input_review is not None
        assert cards.input_review.expert_name == "会议材料审核专家"
        assert cards.input_review.review_type == "materials_audit"
        assert "遗漏的关联信息" in cards.input_review.check_signals

        # Verify output_review parsed correctly (even though disabled)
        assert cards.output_review is not None
        assert cards.output_review.enabled is False
        assert cards.output_review.expert_name == "经营顾问"

    def test_missing_scene_returns_none_values(self, tmp_path):
        """BEHAVIOR: Missing scene is handled gracefully, no exception."""
        # Call with nonexistent scene
        cards = load_expert_cards("nonexistent-scene", scenes_dir=tmp_path)

        # Should return ExpertCards with None values
        assert cards.input_review is None
        assert cards.output_review is None

    def test_scene_without_expert_cards_file(self, tmp_path):
        """Scene directory exists but no expert-cards.yaml returns None values."""
        # Create scene directory without expert-cards.yaml
        scene_dir = tmp_path / "archive-refresh"
        scene_dir.mkdir()

        cards = load_expert_cards("archive-refresh", scenes_dir=tmp_path)

        assert cards.input_review is None
        assert cards.output_review is None

    def test_invalid_scene_name_handled_gracefully(self, tmp_path):
        """BEHAVIOR: Invalid scene names are rejected safely."""
        # Path traversal attempt - should raise ValueError
        with pytest.raises(ValueError):
            load_expert_cards("../etc/passwd", scenes_dir=tmp_path)

        # Unknown scene - returns None values gracefully (not an exception)
        cards = load_expert_cards("invalid-scene-name", scenes_dir=tmp_path)
        assert cards.input_review is None
        assert cards.output_review is None

    def test_yaml_missing_required_fields_handled(self, tmp_path):
        """BEHAVIOR: Malformed YAML does not crash the loader."""
        scene_dir = tmp_path / "customer-recent-status"
        scene_dir.mkdir()
        expert_cards_file = scene_dir / "expert-cards.yaml"

        # YAML with missing required fields (no expert_name, no output_field)
        expert_cards_file.write_text(yaml.dump({
            "input_review": {
                "enabled": True,
                "review_type": "materials_audit",
                # Missing: expert_name, check_signals, output_field
            },
        }))

        # Should not raise, should return card with empty defaults
        cards = load_expert_cards("customer-recent-status", scenes_dir=tmp_path)

        # Should have input_review with empty defaults
        assert cards.input_review is not None
        assert cards.input_review.expert_name == ""  # Empty default
        assert cards.input_review.check_signals == []  # Empty default

    def test_yaml_invalid_syntax_handled(self, tmp_path):
        """BEHAVIOR: Invalid YAML syntax is handled gracefully."""
        scene_dir = tmp_path / "cohort-scan"
        scene_dir.mkdir()
        expert_cards_file = scene_dir / "expert-cards.yaml"

        # Invalid YAML (unclosed quote, wrong indent)
        expert_cards_file.write_text('input_review:\n  enabled: true\n  expert_name: "unclosed\n    bad_indent: value')

        # Should raise YAMLParseError
        with pytest.raises(YAMLParseError):
            load_expert_cards("cohort-scan", scenes_dir=tmp_path)

    def test_only_input_review_defined(self, tmp_path):
        """When only input_review is defined, output_review should be None."""
        scene_dir = tmp_path / "meeting-prep"
        scene_dir.mkdir()
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

        cards = load_expert_cards("meeting-prep", scenes_dir=tmp_path)

        assert cards.input_review is not None
        assert cards.output_review is None

    def test_only_output_review_defined(self, tmp_path):
        """When only output_review is defined, input_review should be None."""
        scene_dir = tmp_path / "proposal"
        scene_dir.mkdir()
        expert_cards_file = scene_dir / "expert-cards.yaml"

        expert_cards_file.write_text(yaml.dump({
            "output_review": {
                "enabled": True,
                "expert_name": "提案审核顾问",
                "review_type": "proposal_audit",
                "check_dimensions": ["完整性", "可执行性"],
                "output_field": "proposal_audit_notes",
                "block_on_flags": ["范围超出"],
            },
        }))

        cards = load_expert_cards("proposal", scenes_dir=tmp_path)

        assert cards.input_review is None
        assert cards.output_review is not None
