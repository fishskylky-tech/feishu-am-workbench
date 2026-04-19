from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EVALS_PATH = REPO_ROOT / "evals" / "evals.json"
README_PATH = REPO_ROOT / "README.md"
LICENSE_PATH = REPO_ROOT / "LICENSE"


class ValidationAssetTests(unittest.TestCase):
    def test_license_exists(self) -> None:
        self.assertTrue(LICENSE_PATH.exists())
        license_text = LICENSE_PATH.read_text()
        self.assertIn("MIT License", license_text)
        self.assertIn("2026", license_text)

    def test_evals_file_is_valid_json(self) -> None:
        evals = json.loads(EVALS_PATH.read_text())
        self.assertIn("version", evals)
        self.assertIn("evals", evals)
        self.assertEqual(len(evals["evals"]), 3)

    def test_evals_have_sanitized_customer_names(self) -> None:
        evals = json.loads(EVALS_PATH.read_text())["evals"]
        names = {item["name"] for item in evals}
        self.assertEqual(len(evals), 3)
        self.assertEqual(
            names,
            {
                "<CUSTOMER_A>-stage-review",
                "<CUSTOMER_B>-product-solution-discussion",
                "<CUSTOMER_C>-ad-tracking-qa",
            },
        )

    def test_evals_references_sanitized_transcript_files(self) -> None:
        evals = json.loads(EVALS_PATH.read_text())["evals"]
        files = {Path(path).name for item in evals for path in item.get("files", [])}
        self.assertIn("20260410-<CUSTOMER_A> Campaign活动分析优化-阶段汇报.txt", files)
        self.assertIn("20260409 神策AI 产品和<CUSTOMER_B>会议记录.txt", files)
        self.assertIn("2026-3-18 <CUSTOMER_C>神策会议纪要.txt", files)

    def test_evals_content_has_no_customer_names(self) -> None:
        evals_text = EVALS_PATH.read_text()
        self.assertNotIn("联合利华", evals_text)
        self.assertNotIn("永和大王", evals_text)
        self.assertNotIn("达美乐", evals_text)
        self.assertNotIn("unilever", evals_text)
        self.assertNotIn("yonghe", evals_text)
        self.assertNotIn("dominos", evals_text)

    def test_readme_is_open_source_friendly(self) -> None:
        readme_text = README_PATH.read_text(encoding="utf-8")
        self.assertNotIn("联合利华", readme_text)
        self.assertNotIn("永和大王", readme_text)
        self.assertNotIn("达美乐", readme_text)
        self.assertIn("python3 -m runtime", readme_text)


if __name__ == "__main__":
    unittest.main()
