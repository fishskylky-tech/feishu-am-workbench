from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOST_DOCS = [
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / ".planning" / "PROJECT.md",
]
RULE_DOCS = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "SKILL.md",
    REPO_ROOT / ".planning" / "PROJECT.md",
]
CORE_CODE_PATHS = [
    REPO_ROOT / "runtime",
    REPO_ROOT / "evals" / "meeting_output_bridge.py",
    REPO_ROOT / "evals" / "runner.py",
]
HOST_MARKERS = ("Hermes", "OpenClaw", "Codex")
RULE_MARKERS = ("live-first",)
RECOMMENDATION_MARKERS = ("recommendation-first", "recommendation mode")


class PortabilityContractTests(unittest.TestCase):
    def test_host_portability_is_documented_in_project_contracts(self) -> None:
        for path in HOST_DOCS:
            text = path.read_text(encoding="utf-8")
            for marker in HOST_MARKERS:
                self.assertIn(marker, text, f"{path} missing host marker {marker}")

    def test_live_first_and_recommendation_first_rules_are_consistent(self) -> None:
        for path in RULE_DOCS:
            text = path.read_text(encoding="utf-8").casefold()
            for marker in RULE_MARKERS:
                self.assertIn(marker, text, f"{path} missing rule marker {marker}")
            self.assertTrue(
                any(marker in text for marker in RECOMMENDATION_MARKERS),
                f"{path} missing recommendation rule marker",
            )

    def test_core_runtime_and_eval_logic_remain_host_agnostic(self) -> None:
        code_files: list[Path] = []
        for path in CORE_CODE_PATHS:
            if path.is_dir():
                code_files.extend(sorted(path.rglob("*.py")))
            else:
                code_files.append(path)
        for path in code_files:
            text = path.read_text(encoding="utf-8")
            for marker in HOST_MARKERS:
                self.assertNotIn(marker, text, f"{path} should not hard-code host marker {marker}")


if __name__ == "__main__":
    unittest.main()
