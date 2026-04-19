"""Expert card binder system: load expert card YAML configs with schema validation.

Per D-06 Plan C (binder-style expert cards): Each scene has independent expert cards
(input_review / output_review) loaded on demand.

Security:
- yaml.safe_load() only — no eval()
- Scene names validated against registry to prevent path traversal

Failure strategy (MEDIUM-04):
- YAML file missing: fail-open (log warning, return None)
- YAML syntax invalid: fail-closed (raise error)
- Schema validation fails: fail-closed (raise error)
- Invalid scene name: fail-open (log warning, return None)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# 7 registered scenes from scene_registry.py
VALID_SCENES = frozenset({
    "post-meeting-synthesis",
    "customer-recent-status",
    "archive-refresh",
    "todo-capture-and-update",
    "cohort-scan",
    "meeting-prep",
    "proposal",
})


@dataclass
class ExpertCardConfig:
    """Expert card configuration per scene."""

    enabled: bool
    expert_name: str
    review_type: str
    check_signals: list[str]
    output_field: str
    block_on_flags: list[str] | None = None


def validate_scene_name(scene_name: str) -> bool:
    """Check if scene_name is in the registry."""
    return scene_name in VALID_SCENES


def validate_card_schema(card: dict, card_type: str) -> tuple[bool, str | None]:
    """Validate required fields on a card dict.

    Returns (is_valid, error_message).
    """
    required_fields = ["expert_name", "review_type", "check_signals", "output_field"]
    for field in required_fields:
        if field not in card:
            return False, f"Missing required field '{field}' in {card_type}"

    if not isinstance(card.get("check_signals"), list):
        return False, f"'check_signals' must be a list in {card_type}"
    if len(card["check_signals"]) == 0:
        return False, f"'check_signals' must have at least one signal in {card_type}"

    return True, None


def resolve_scene_dir(repo_root: Path, scene_name: str) -> Path | None:
    """Resolve scenes/{scene_name} directory path.

    Returns None if directory does not exist.
    """
    path = repo_root / "scenes" / scene_name
    if not path.is_dir():
        return None
    return path


def load_yaml_config(path: Path) -> dict[str, Any]:
    """Load YAML config using yaml.safe_load() only."""
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def parse_input_card(raw: dict) -> ExpertCardConfig | None:
    """Parse input_review card from raw dict.

    Returns None if card is disabled.
    Raises ValueError on schema validation failure.
    """
    if not raw.get("enabled", True):
        return None

    is_valid, err = validate_card_schema(raw, "input_review")
    if not is_valid:
        raise ValueError(f"input_review schema validation failed: {err}")

    return ExpertCardConfig(
        enabled=raw.get("enabled", True),
        expert_name=raw["expert_name"],
        review_type=raw["review_type"],
        check_signals=raw["check_signals"],
        output_field=raw["output_field"],
        block_on_flags=raw.get("block_on_flags"),
    )


def parse_output_card(raw: dict) -> ExpertCardConfig | None:
    """Parse output_review card from raw dict.

    Returns None if card is disabled.
    Raises ValueError on schema validation failure.
    """
    if not raw.get("enabled", True):
        return None

    is_valid, err = validate_card_schema(raw, "output_review")
    if not is_valid:
        raise ValueError(f"output_review schema validation failed: {err}")

    return ExpertCardConfig(
        enabled=raw.get("enabled", True),
        expert_name=raw["expert_name"],
        review_type=raw["review_type"],
        check_signals=raw["check_signals"],
        output_field=raw["output_field"],
        block_on_flags=raw.get("block_on_flags"),
    )


def load_expert_cards(
    scene_name: str, repo_root: Path
) -> dict[str, ExpertCardConfig | None]:
    """Load expert cards from scenes/{scene_name}/expert-cards.yaml.

    Args:
        scene_name: One of the 7 registered scene names.
        repo_root: Root directory of the workbench repo.

    Returns:
        dict with keys "input_review" and "output_review".
        Each value is an ExpertCardConfig or None (if disabled or absent).

    Failure strategy (MEDIUM-04):
        - Scene name invalid: fail-open, log warning, return {"input_review": None, "output_review": None}
        - YAML file missing: fail-open, log warning, return {"input_review": None, "output_review": None}
        - YAML syntax invalid: fail-closed, raise yaml.YAMLError
        - Schema validation failure: fail-closed, raise ValueError
    """
    # Validate scene name against registry (path traversal prevention)
    if not validate_scene_name(scene_name):
        logger.warning(
            "load_expert_cards: scene_name '%s' not in registry. "
            "Known scenes: %s. Returning None.",
            scene_name,
            sorted(VALID_SCENES),
        )
        return {"input_review": None, "output_review": None}

    scene_dir = resolve_scene_dir(repo_root, scene_name)
    if scene_dir is None:
        expected_path = repo_root / "scenes" / scene_name
        logger.warning(
            "load_expert_cards: scene directory not found for '%s'. "
            "Expected: %s. Returning None.",
            scene_name,
            expected_path,
        )
        return {"input_review": None, "output_review": None}

    config_path = scene_dir / "expert-cards.yaml"
    if not config_path.exists():
        logger.warning(
            "load_expert_cards: expert-cards.yaml not found for scene '%s' at %s. "
            "Returning None.",
            scene_name,
            config_path,
        )
        return {"input_review": None, "output_review": None}

    # YAML syntax error → fail-closed
    raw = load_yaml_config(config_path)

    input_card: ExpertCardConfig | None = None
    output_card: ExpertCardConfig | None = None

    if "input_review" in raw:
        raw_input = raw["input_review"]
        if raw_input is not None:
            # Schema validation failure → fail-closed
            input_card = parse_input_card(raw_input)

    if "output_review" in raw:
        raw_output = raw["output_review"]
        if raw_output is not None:
            # Schema validation failure → fail-closed
            output_card = parse_output_card(raw_output)

    return {"input_review": input_card, "output_review": output_card}
