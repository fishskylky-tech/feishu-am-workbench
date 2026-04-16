from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EVALS_PATH = REPO_ROOT / "evals" / "evals.json"
VALIDATION_PATH = REPO_ROOT / "VALIDATION.md"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
VERSION_PATH = REPO_ROOT / "VERSION"
MULTI_CASE_REPORT = REPO_ROOT / "archive" / "validation-reports" / "2026-04-11-multi-case-skill-validation.md"


class ValidationAssetTests(unittest.TestCase):
    def test_version_is_consistent_across_assets(self) -> None:
        version = VERSION_PATH.read_text().strip()
        evals = json.loads(EVALS_PATH.read_text())

        self.assertEqual(version, "0.2.13")
        self.assertEqual(evals["version"], version)
        self.assertIn("## [0.2.13] - 2026-04-15", CHANGELOG_PATH.read_text())

    def test_evals_cover_three_real_transcript_cases(self) -> None:
        evals = json.loads(EVALS_PATH.read_text())["evals"]
        names = {item["name"] for item in evals}
        files = {Path(path).name for item in evals for path in item.get("files", [])}

        self.assertEqual(len(evals), 3)
        self.assertEqual(
            names,
            {
                "unilever-stage-review",
                "yonghe-product-solution-discussion",
                "dominos-ad-tracking-qa",
            },
        )
        self.assertIn("20260410-联合利华 Campaign活动分析优化-阶段汇报.txt", files)
        self.assertIn("20260409 神策AI 产品和永和大王会议记录.txt", files)
        self.assertIn("2026-3-18 达美乐神策会议纪要.txt", files)
        self.assertTrue(all(not Path(path).is_absolute() for item in evals for path in item.get("files", [])))

    def test_validation_doc_defines_baseline_green_and_regression_protocol(self) -> None:
        text = VALIDATION_PATH.read_text()

        self.assertIn("RED / baseline", text)
        self.assertIn("GREEN / current-branch", text)
        self.assertIn("REFACTOR / regression", text)
        self.assertIn("联合利华", text)
        self.assertIn("永和大王", text)
        self.assertIn("达美乐", text)

    def test_consolidated_multi_case_report_exists(self) -> None:
        text = MULTI_CASE_REPORT.read_text()

        self.assertIn("联合利华", text)
        self.assertIn("永和大王", text)
        self.assertIn("达美乐", text)
        self.assertIn("P1", text)
        self.assertIn("P3", text)

    def test_meeting_output_bridge_exists(self) -> None:
        bridge_path = REPO_ROOT / "evals" / "meeting_output_bridge.py"
        text = bridge_path.read_text()

        self.assertIn("build_meeting_output", text)
        self.assertIn("run_gateway_and_build_meeting_output", text)
        self.assertIn("fallback 原因", text)
        self.assertIn("Meeting type", text)

    def test_evals_include_live_first_assertions_without_scene_type(self) -> None:
        evals = json.loads(EVALS_PATH.read_text())["evals"]
        live_first_ids = []
        checks = []
        for case in evals:
            for assertion in case["assertions"]:
                if assertion["type"] == "live_first_gate":
                    live_first_ids.append(assertion["id"])
                checks.append(assertion.get("check", ""))
        self.assertEqual(len(live_first_ids), 3)
        self.assertFalse(any("scene type" in check.casefold() for check in checks))


if __name__ == "__main__":
    unittest.main()
