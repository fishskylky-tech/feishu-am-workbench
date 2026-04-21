"""Tests for Phase 25: Expert Copy & Adaptation.

Verifies that 4 expert prompt files were correctly copied from agency-agents repo.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
AGENTS_DIR = REPO_ROOT / "agents"


class TestExpertFilesExist:
    """VERIFICATION: All 4 expert files exist after Phase 25 copy."""

    def test_sales_account_strategist_exists(self):
        """sales-account-strategist.md must exist in agents/ directory."""
        path = AGENTS_DIR / "sales-account-strategist.md"
        assert path.exists(), f"Expected {path} to exist (Phase 25 must_have 25-01)"

    def test_sales_proposal_strategist_exists(self):
        """sales-proposal-strategist.md must exist in agents/ directory."""
        path = AGENTS_DIR / "sales-proposal-strategist.md"
        assert path.exists(), f"Expected {path} to exist (Phase 25 must_have 25-02)"

    def test_customer_service_exists(self):
        """customer-service.md must exist in agents/ directory."""
        path = AGENTS_DIR / "customer-service.md"
        assert path.exists(), f"Expected {path} to exist (Phase 25 must_have 25-03)"

    def test_sales_data_extraction_agent_exists(self):
        """sales-data-extraction-agent.md must exist in agents/ directory."""
        path = AGENTS_DIR / "sales-data-extraction-agent.md"
        assert path.exists(), f"Expected {path} to exist (Phase 25 must_have 25-04)"


class TestExpertFilesFrontmatter:
    """VERIFICATION: All copied files have valid frontmatter."""

    def test_sales_account_strategist_has_frontmatter(self):
        """sales-account-strategist.md must have --- frontmatter delimiter."""
        path = AGENTS_DIR / "sales-account-strategist.md"
        content = path.read_text()
        lines = content.split("\n")
        assert lines[0] == "---" or lines[1] == "---", (
            f"Expected --- frontmatter delimiter in {path}"
        )

    def test_sales_account_strategist_has_correct_name_field(self):
        """sales-account-strategist.md frontmatter must contain 'name: Account Strategist'."""
        path = AGENTS_DIR / "sales-account-strategist.md"
        content = path.read_text()
        assert "name: Account Strategist" in content, (
            f"Expected 'name: Account Strategist' in frontmatter of {path}"
        )

    def test_customer_service_has_frontmatter(self):
        """customer-service.md must have --- frontmatter delimiter."""
        path = AGENTS_DIR / "customer-service.md"
        content = path.read_text()
        lines = content.split("\n")
        assert lines[0] == "---" or lines[1] == "---", (
            f"Expected --- frontmatter delimiter in {path}"
        )

    def test_customer_service_has_correct_name_field(self):
        """customer-service.md frontmatter must contain 'name: Customer Service'."""
        path = AGENTS_DIR / "customer-service.md"
        content = path.read_text()
        assert "name: Customer Service" in content, (
            f"Expected 'name: Customer Service' in frontmatter of {path}"
        )


class TestExpertFilesNonEmpty:
    """VERIFICATION: All copied files are non-empty (meet minimum size per source).

    Note: sales-data-extraction-agent.md is 67 lines per the original GitHub source
    (2,697 bytes). PLAN assumed >100 lines but source file is smaller — verified as-is.
    """

    @pytest.mark.parametrize(
        "filename,min_lines",
        [
            ("sales-account-strategist.md", 100),
            ("sales-proposal-strategist.md", 100),
            ("customer-service.md", 100),
            ("sales-data-extraction-agent.md", 50),  # Source file is 67 lines
        ],
    )
    def test_file_has_minimum_lines(self, filename: str, min_lines: int):
        """Each expert file must have sufficient content (min_lines threshold)."""
        path = AGENTS_DIR / filename
        content = path.read_text()
        line_count = len(content.split("\n"))
        assert line_count > min_lines, (
            f"Expected {path} to have >{min_lines} lines, got {line_count}"
        )
