"""Expert card loader for scene-specific expert review configurations.

Loads expert-card YAML configs from scenes/{scene_name}/ directory.
Each scene can have input_review and/or output_review expert cards.

This module provides the binding between scene execution and the expert review
layer defined by AGENT-01 (D-06 Plan C: binder-style expert cards).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# The 7 registered scenes from scene_registry.py
VALID_SCENES = [
    "post-meeting-synthesis",
    "customer-recent-status",
    "archive-refresh",
    "todo-capture-and-update",
    "cohort-scan",
    "meeting-prep",
    "proposal",
]


class ExpertCardError(Exception):
    """Base exception for expert card loading errors."""
    pass


class YAMLParseError(ExpertCardError):
    """Raised when YAML parsing fails."""
    pass


class SceneNotFoundError(ExpertCardError):
    """Raised when scene directory does not exist."""
    pass


@dataclass
class InputReviewCard:
    """Input review expert card configuration."""
    enabled: bool
    expert_name: str
    review_type: str
    check_signals: list[str]
    output_field: str


@dataclass
class OutputReviewCard:
    """Output review expert card configuration."""
    enabled: bool
    expert_name: str
    review_type: str
    check_dimensions: list[str]
    output_field: str
    block_on_flags: list[str]


@dataclass
class ExpertCards:
    """Container for expert cards loaded from a scene's expert-cards.yaml."""
    input_review: InputReviewCard | None = None
    output_review: OutputReviewCard | None = None


def _validate_scene_name(scene_name: str) -> str:
    """Validate scene name to prevent path traversal attacks.

    Raises:
        ValueError: If scene_name contains path traversal patterns.
    """
    # Block path traversal attempts - these are always rejected
    dangerous_patterns = ["..", "/", "\\", "~", "$", "`", ";", "&", "|"]
    for pattern in dangerous_patterns:
        if pattern in scene_name:
            raise ValueError(
                f"Invalid scene name '{scene_name}': contains dangerous pattern '{pattern}'"
            )

    # Note: Unknown scenes (not in VALID_SCENES) are NOT rejected here.
    # They are handled gracefully by returning ExpertCards with None values.
    # This allows the loader to degrade gracefully for unregistered scenes.

    return scene_name


def _safe_load_yaml(file_path: Path) -> dict[str, Any]:
    """Safely load YAML file using yaml.safe_load.

    Raises:
        YAMLParseError: If YAML parsing fails.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise YAMLParseError(f"Invalid YAML in {file_path}: {e}")
    except OSError as e:
        raise ExpertCardError(f"Cannot read {file_path}: {e}")


def load_expert_cards(scene_name: str, scenes_dir: Path | None = None) -> ExpertCards:
    """Load expert cards for a given scene.

    Args:
        scene_name: Name of the scene (e.g., 'post-meeting-synthesis').
        scenes_dir: Path to scenes directory. Defaults to {project_root}/scenes/.

    Returns:
        ExpertCards container with input_review and/or output_review cards.
        Returns ExpertCards with None values if scene not found or cards not defined.

    Raises:
        ValueError: If scene_name is invalid or contains path traversal.
        YAMLParseError: If YAML file is malformed.
    """
    # Validate scene name first (security)
    validated_name = _validate_scene_name(scene_name)

    # Default scenes directory
    if scenes_dir is None:
        # Project root is parent of runtime/
        project_root = Path(__file__).parent.parent
        scenes_dir = project_root / "scenes"

    scene_dir = scenes_dir / validated_name
    expert_cards_file = scene_dir / "expert-cards.yaml"

    # If scene directory doesn't exist, return None values gracefully
    if not scene_dir.exists():
        return ExpertCards(input_review=None, output_review=None)

    # If expert-cards.yaml doesn't exist, return None values
    if not expert_cards_file.exists():
        return ExpertCards(input_review=None, output_review=None)

    # Load and parse YAML
    data = _safe_load_yaml(expert_cards_file)

    result = ExpertCards()

    # Parse input_review card if present
    if "input_review" in data and data["input_review"]:
        ir_data = data["input_review"]
        result.input_review = InputReviewCard(
            enabled=ir_data.get("enabled", False),
            expert_name=ir_data.get("expert_name", ""),
            review_type=ir_data.get("review_type", ""),
            check_signals=ir_data.get("check_signals", []),
            output_field=ir_data.get("output_field", ""),
        )

    # Parse output_review card if present
    if "output_review" in data and data["output_review"]:
        or_data = data["output_review"]
        result.output_review = OutputReviewCard(
            enabled=or_data.get("enabled", False),
            expert_name=or_data.get("expert_name", ""),
            review_type=or_data.get("review_type", ""),
            check_dimensions=or_data.get("check_dimensions", []),
            output_field=or_data.get("output_field", ""),
            block_on_flags=or_data.get("block_on_flags", []),
        )

    return result
