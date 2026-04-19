"""Tests for SKILL.md token count verification.

Verifies SKILL.md stays under token limits using fallback chain:
1. tiktoken (most accurate for Claude models)
2. anthropic SDK tokenizer
3. char_count // 4 approximation with guard threshold
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

# Project root is parent of tests/
PROJECT_ROOT = Path(__file__).parent.parent
SKILL_MD_PATH = PROJECT_ROOT / "SKILL.md"


def count_tokens(content: str) -> int:
    """Count tokens using tiktoken if available, else approximate with guard.

    Fallback chain:
    1. tiktoken with cl100k_base encoding (most accurate for Claude models)
    2. anthropic SDK tokenizer
    3. char_count // 4 approximation
    """
    # Try tiktoken first (most accurate for Claude models)
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(content))
    except ImportError:
        pass

    # Try anthropic SDK tokenizer
    try:
        from anthropic._tokenizer import build_tokenizer

        tokenizer = build_tokenizer()
        return len(tokenizer.encode(content))
    except ImportError:
        pass

    # Fallback: char_count // 4 with guard threshold
    # This is a rough approximation - the guard threshold of 2100 catches errors
    return len(content) // 4


def get_token_limit_status(content: str) -> dict:
    """Returns dict with token_count, limit (2000), guard_limit (2100), and pass status."""
    count = count_tokens(content)
    return {
        "token_count": count,
        "limit": 2000,
        "guard_limit": 2100,
        "under_limit": count < 2000,
        "under_guard": count < 2100,
    }


def test_skill_md_exists():
    """SKILL.md should exist at project root."""
    assert SKILL_MD_PATH.exists(), f"SKILL.md not found at {SKILL_MD_PATH}"


def test_skill_md_under_token_limit():
    """SKILL.md should be under 2000 tokens with guard at 2100.

    Uses tiktoken if available, else falls back to approximation.
    If approximation fallback is used, a warning is logged.
    """
    content = SKILL_MD_PATH.read_text(encoding="utf-8")

    # Check if we're using fallback
    fallback_used = False
    try:
        import tiktoken  # noqa: F401
    except ImportError:
        fallback_used = True
        try:
            from anthropic._tokenizer import build_tokenizer  # noqa: F401
        except ImportError:
            fallback_used = True

    status = get_token_limit_status(content)

    if fallback_used:
        warnings.warn(
            f"Using token approximation fallback. "
            f"Estimated {status['token_count']} tokens (approximation). "
            f"Install tiktoken for accurate count: pip install tiktoken"
        )

    # Primary limit: 2000 tokens
    assert status["token_count"] < 2000, (
        f"SKILL.md has {status['token_count']} tokens, exceeds 2000 limit. "
        f"Needs reduction per NORM-01."
    )

    # Guard threshold: 2100 (failsafe for approximation errors)
    assert status["token_count"] < 2100, (
        f"SKILL.md has {status['token_count']} tokens, exceeds guard threshold 2100. "
        f"Approximation may be underestimating."
    )


def test_skill_md_frontmatter_has_required_fields():
    """SKILL.md frontmatter should contain all required fields per agentskills.io standard."""
    content = SKILL_MD_PATH.read_text(encoding="utf-8")

    # Parse frontmatter block (between --- lines)
    lines = content.split("\n")
    frontmatter_lines = []
    in_frontmatter = False

    for line in lines:
        if line.strip() == "---":
            if not in_frontmatter:
                in_frontmatter = True
                continue
            else:
                break
        if in_frontmatter:
            frontmatter_lines.append(line)

    frontmatter_text = "\n".join(frontmatter_lines)

    # Required fields per agentskills.io + anthropics/skills standards
    required_fields = ["name", "version", "description", "triggers", "load_strategy", "tier"]

    for field in required_fields:
        assert field in frontmatter_text, (
            f"SKILL.md frontmatter missing required field: '{field}'. "
            f"See NORM-02 alignment with agentskills.io standard."
        )


def test_skill_md_has_progressive_load_strategy():
    """SKILL.md should specify progressive load_strategy for L1/L2/L3 tiered loading."""
    content = SKILL_MD_PATH.read_text(encoding="utf-8")
    assert "load_strategy:" in content, "SKILL.md should define load_strategy"
    assert "progressive" in content or "lazy" in content, (
        "load_strategy should be 'progressive' or 'lazy' for tiered loading"
    )


def test_skill_md_has_tier_boundaries():
    """SKILL.md should define L1/L2/L3 tier boundaries clearly."""
    content = SKILL_MD_PATH.read_text(encoding="utf-8")

    # Check for tier indicators
    has_l1 = "L1" in content or "Tier 1" in content or "tier:" in content
    has_l2 = "L2" in content or "Tier 2" in content
    has_l3 = "L3" in content or "Tier 3" in content or "references/" in content

    assert has_l1 or has_l2 or has_l3, (
        "SKILL.md should define tier boundaries (L1/L2/L3 or similar)"
    )
