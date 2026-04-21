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
import os
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

AGENTS_DIR = Path(__file__).parent.parent / "agents"

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


class RegistryCache:
    """Singleton cache for agent-registry.yaml with mtime-based invalidation.

    Cache invalidation strategy (per OpenCode review concern MEDIUM-3):
    1. Primary: mtime-based — cache invalidates when registry file mtime changes
    2. Secondary: TTL-based — cache expires after 60 seconds as a safety net

    This prevents stale registry data in long-running processes when agent files are updated.
    """
    _instance: dict | None = None
    _loaded_at: float | None = None
    _registry_mtime: float | None = None
    _lock: threading.Lock | None = None

    @classmethod
    def _get_lock(cls) -> threading.Lock:
        """Get or create the thread lock (lazily initialized)."""
        if cls._lock is None:
            cls._lock = threading.Lock()
        return cls._lock

    @classmethod
    def get_registry(cls) -> dict:
        """Load and cache agent-registry.yaml with mtime-based invalidation."""
        lock = cls._get_lock()
        with lock:
            now = time.monotonic()
            registry_path = AGENTS_DIR / "agent-registry.yaml"
            file_mtime = registry_path.stat().st_mtime if registry_path.exists() else 0

            # Invalidate if registry file mtime changed (registry edited)
            # or if TTL expired
            cache_stale = (
                cls._instance is None
                or cls._loaded_at is None
                or now - cls._loaded_at > 60
                or cls._registry_mtime != file_mtime
            )

            if cache_stale:
                if registry_path.exists():
                    with registry_path.open(encoding="utf-8") as f:
                        cls._instance = yaml.safe_load(f)
                else:
                    cls._instance = {"agents": {}}
                cls._loaded_at = now
                cls._registry_mtime = file_mtime

            return cls._instance or {"agents": {}}

    @classmethod
    def invalidate(cls) -> None:
        """Clear cache to force reload on next access."""
        cls._instance = None
        cls._loaded_at = None
        cls._registry_mtime = None


def normalize_agent_name(name: str) -> str:
    """Normalize agent name for security validation.

    - Lowercase
    - Strip whitespace
    - Only allow alphanumeric, dash, underscore
    - Max 64 characters
    - Prevents path traversal and injection attacks

    Per OpenCode review concern MEDIUM-2: security boundary incomplete.
    """
    if not name or not isinstance(name, str):
        return ""
    normalized = name.strip().lower()
    normalized = re.sub(r"[^a-z0-9_-]", "", normalized)
    return normalized[:64]


def validate_agent_reference(agent_name: str) -> tuple[bool, str | None]:
    """Validate that agent_name exists in agent-registry.yaml.

    Returns (is_valid, error_message).
    SOLE SOURCE OF TRUTH invariant: only agent-registry.yaml defines valid agent names.
    expert-cards.yaml may only REFERENCE agents by name; it cannot define them inline.

    Per AA-01-PLAN.md Section 2: agent-registry.yaml is the ONLY source of truth.
    Per OpenCode review concern MEDIUM-2: security normalization applied before validation.
    """
    # Security: normalize before validation
    normalized = normalize_agent_name(agent_name)
    if not normalized:
        return False, f"Invalid agent_name format: '{agent_name}'"

    registry = RegistryCache.get_registry()
    agents = registry.get("agents", {})

    if normalized not in agents:
        return False, f"Agent '{normalized}' not found in agent-registry.yaml. Valid agents: {list(agents.keys())}"

    agent_config = agents[normalized]
    if not agent_config.get("enabled", True):
        return False, f"Agent '{normalized}' is disabled in agent-registry.yaml"

    return True, None


@dataclass(frozen=True)
class ExpertCardConfig:
    """Expert card configuration per scene."""

    enabled: bool
    expert_name: str
    review_type: str
    check_signals: list[str]
    output_field: str
    block_on_flags: list[str] | None = None
    prompt_file: str | None = None
    agent_name: str | None = None  # LLM agent name; required when prompt_file is set


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

    # D-02: Extract prompt_file if present with strict path security
    prompt_file = raw.get("prompt_file")
    if prompt_file:
        # Strict path security rules (per OpenCode review):
        # 1. Reject non-.md extensions to prevent arbitrary file inclusion
        if not prompt_file.endswith(".md"):
            raise ValueError(f"prompt_file must have .md extension: {prompt_file}")

        # 2. Build path (do not resolve yet)
        prompt_path = AGENTS_DIR / prompt_file

        # 3. Reject symlinks BEFORE resolve (resolve() follows symlinks making is_symlink() always False)
        if prompt_path.is_symlink():
            raise ValueError(f"prompt_file cannot be a symlink: {prompt_path}")

        # 4. Resolve to absolute path to prevent relative path traversal
        prompt_path = prompt_path.resolve()

        # 5. Verify resolved path is still under AGENTS_DIR (prevents symlink + path traversal)
        try:
            prompt_path.relative_to(AGENTS_DIR)
        except ValueError:
            raise ValueError(f"prompt_file must be under AGENTS_DIR: {prompt_path}")

        # 6. Verify file exists and is readable
        if not prompt_path.exists():
            raise ValueError(f"prompt_file not found: {prompt_path}")

    # D-03: Extract agent_name if present and validate against registry
    agent_name = raw.get("agent_name")
    if agent_name:
        is_valid, err = validate_agent_reference(agent_name)
        if not is_valid:
            raise ValueError(f"agent_name '{agent_name}' not found in agent-registry.yaml: {err}")

    return ExpertCardConfig(
        enabled=raw.get("enabled", True),
        expert_name=raw["expert_name"],
        review_type=raw["review_type"],
        check_signals=raw["check_signals"],
        output_field=raw["output_field"],
        block_on_flags=raw.get("block_on_flags"),
        prompt_file=prompt_file,
        agent_name=agent_name,
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

    # D-02: Extract prompt_file if present with strict path security
    prompt_file = raw.get("prompt_file")
    if prompt_file:
        # Strict path security rules (per OpenCode review):
        # 1. Reject non-.md extensions to prevent arbitrary file inclusion
        if not prompt_file.endswith(".md"):
            raise ValueError(f"prompt_file must have .md extension: {prompt_file}")

        # 2. Build path (do not resolve yet)
        prompt_path = AGENTS_DIR / prompt_file

        # 3. Reject symlinks BEFORE resolve (resolve() follows symlinks making is_symlink() always False)
        if prompt_path.is_symlink():
            raise ValueError(f"prompt_file cannot be a symlink: {prompt_path}")

        # 4. Resolve to absolute path to prevent relative path traversal
        prompt_path = prompt_path.resolve()

        # 5. Verify resolved path is still under AGENTS_DIR (prevents symlink + path traversal)
        try:
            prompt_path.relative_to(AGENTS_DIR)
        except ValueError:
            raise ValueError(f"prompt_file must be under AGENTS_DIR: {prompt_path}")

        # 6. Verify file exists and is readable
        if not prompt_path.exists():
            raise ValueError(f"prompt_file not found: {prompt_path}")

    # D-03: Extract agent_name if present and validate against registry
    agent_name = raw.get("agent_name")
    if agent_name:
        is_valid, err = validate_agent_reference(agent_name)
        if not is_valid:
            raise ValueError(f"agent_name '{agent_name}' not found in agent-registry.yaml: {err}")

    return ExpertCardConfig(
        enabled=raw.get("enabled", True),
        expert_name=raw["expert_name"],
        review_type=raw["review_type"],
        check_signals=raw["check_signals"],
        output_field=raw["output_field"],
        block_on_flags=raw.get("block_on_flags"),
        prompt_file=prompt_file,
        agent_name=agent_name,
    )


def _validate_expert_cards(raw: dict) -> None:
    """Validate all agent_name references in expert-cards.yaml against registry.

    Raises ValueError if any agent_name is not found in agent-registry.yaml.
    Per SOLE SOURCE OF TRUTH invariant from AA-01-PLAN.md Section 2.
    Per OpenCode review concern MEDIUM-04.
    """
    for card_type in ("input_review", "output_review"):
        if card_type in raw and raw[card_type] is not None:
            card = raw[card_type]
            if isinstance(card, dict) and "agent_name" in card:
                is_valid, err = validate_agent_reference(card["agent_name"])
                if not is_valid:
                    raise ValueError(
                        f"expert-cards.yaml {card_type} references unknown agent '{card['agent_name']}': {err}"
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
        - Invalid agent reference: fail-closed, raise ValueError
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

    # Validate agent references against registry (SOLE SOURCE OF TRUTH)
    _validate_expert_cards(raw)

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


if __name__ == "__main__":
    from pathlib import Path
    import sys

    repo_root = Path(__file__).parent.parent

    # Test post-meeting-synthesis scene
    cards = load_expert_cards("post-meeting-synthesis", repo_root)
    input_card = cards["input_review"]
    assert input_card is not None, "input_review should not be None"
    assert input_card.prompt_file == "sales-account-strategist.md", \
        f"Expected prompt_file='agents/sales-account-strategist.md', got {input_card.prompt_file}"
    assert input_card.agent_name == "sales-account-strategist", \
        f"Expected agent_name='sales-account-strategist', got {input_card.agent_name}"

    output_card = cards["output_review"]
    assert output_card is not None, "output_review should not be None"
    assert output_card.prompt_file == "sales-account-strategist.md", \
        f"Expected prompt_file='agents/sales-account-strategist.md', got {output_card.prompt_file}"
    assert output_card.agent_name == "sales-account-strategist", \
        f"Expected agent_name='sales-account-strategist', got {output_card.agent_name}"

    # Test customer-recent-status scene
    cards2 = load_expert_cards("customer-recent-status", repo_root)
    input_card2 = cards2["input_review"]
    assert input_card2 is not None, "input_review should not be None"
    assert input_card2.prompt_file == "sales-account-strategist.md"
    assert input_card2.agent_name == "sales-account-strategist"

    # Verify LLM path activation conditions
    # Both prompt_file AND agent_name must be non-None for LLM path
    assert input_card.prompt_file and input_card.agent_name, \
        f"LLM path requires BOTH prompt_file and agent_name. Got prompt_file={input_card.prompt_file}, agent_name={input_card.agent_name}"
    assert output_card.prompt_file and output_card.agent_name, \
        f"LLM path requires BOTH prompt_file and agent_name. Got prompt_file={output_card.prompt_file}, agent_name={output_card.agent_name}"
    assert input_card2.prompt_file and input_card2.agent_name, \
        f"LLM path requires BOTH prompt_file and agent_name. Got prompt_file={input_card2.prompt_file}, agent_name={input_card2.agent_name}"

    print("E2E smoke test PASSED: LLM mode fields wired correctly in both scenes")
    print("  - post-meeting-synthesis input_review: LLM path will activate")
    print("  - post-meeting-synthesis output_review: LLM path will activate")
    print("  - customer-recent-status input_review: LLM path will activate")
    sys.exit(0)
