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
README_PATH = REPO_ROOT / "README.md"
STATUS_PATH = REPO_ROOT / "STATUS.md"
PHASE_1_SUMMARY = REPO_ROOT / ".planning" / "phases" / "01-brownfield-baseline" / "01-01-SUMMARY.md"
PHASE_1_VERIFICATION = REPO_ROOT / ".planning" / "phases" / "01-brownfield-baseline" / "01-VERIFICATION.md"
PHASE_2_SUMMARY = REPO_ROOT / ".planning" / "phases" / "02-live-runtime-hardening" / "02-01-SUMMARY.md"
PHASE_6_VERIFICATION = REPO_ROOT / ".planning" / "phases" / "06-validation-and-portability" / "06-VERIFICATION.md"
PHASE_3_VALIDATION = REPO_ROOT / ".planning" / "phases" / "03-core-context-recovery" / "03-VALIDATION.md"
PHASE_3_VERIFICATION = REPO_ROOT / ".planning" / "phases" / "03-core-context-recovery" / "03-VERIFICATION.md"
PHASE_4_VALIDATION = REPO_ROOT / ".planning" / "phases" / "04-unified-safe-writes" / "04-VALIDATION.md"
PHASE_4_VERIFICATION = REPO_ROOT / ".planning" / "phases" / "04-unified-safe-writes" / "04-VERIFICATION.md"
PHASE_5_VERIFICATION = REPO_ROOT / ".planning" / "phases" / "05-expanded-account-model" / "05-VERIFICATION.md"
ROADMAP_PATH = REPO_ROOT / ".planning" / "ROADMAP.md"
REQUIREMENTS_PATH = REPO_ROOT / ".planning" / "REQUIREMENTS.md"
MILESTONES_PATH = REPO_ROOT / ".planning" / "MILESTONES.md"
V1_0_ARCHIVE_ROADMAP_PATH = REPO_ROOT / ".planning" / "milestones" / "v1.0-ROADMAP.md"
V1_0_ARCHIVE_REQUIREMENTS_PATH = REPO_ROOT / ".planning" / "milestones" / "v1.0-REQUIREMENTS.md"
V1_1_ARCHIVE_ROADMAP_PATH = REPO_ROOT / ".planning" / "milestones" / "v1.1-ROADMAP.md"
V1_1_ARCHIVE_REQUIREMENTS_PATH = REPO_ROOT / ".planning" / "milestones" / "v1.1-REQUIREMENTS.md"
V1_1_AUDIT_PATH = REPO_ROOT / ".planning" / "v1.1-MILESTONE-AUDIT.md"
SCENE_RUNTIME_CONTRACT_PATH = REPO_ROOT / "references" / "scene-runtime-contract.md"
SCENE_SKILL_ARCHITECTURE_PATH = REPO_ROOT / "references" / "scene-skill-architecture.md"
PHASE_12_CONTEXT_PATH = REPO_ROOT / ".planning" / "phases" / "12-scene-runtime-contract-and-boundary-freeze" / "12-CONTEXT.md"
PHASE_12_VERIFICATION_PATH = REPO_ROOT / ".planning" / "phases" / "12-scene-runtime-contract-and-boundary-freeze" / "12-VERIFICATION.md"
PHASE_13_CONTEXT_PATH = REPO_ROOT / ".planning" / "phases" / "13-canonical-post-meeting-scene-runtime" / "13-CONTEXT.md"
PHASE_13_SUMMARY_PATH = REPO_ROOT / ".planning" / "phases" / "13-canonical-post-meeting-scene-runtime" / "13-01-SUMMARY.md"
PHASE_13_VERIFICATION_PATH = REPO_ROOT / ".planning" / "phases" / "13-canonical-post-meeting-scene-runtime" / "13-VERIFICATION.md"
PHASE_14_CONTEXT_PATH = REPO_ROOT / ".planning" / "phases" / "14-customer-recent-status-scene-runtime" / "14-CONTEXT.md"
PHASE_14_SUMMARY_PATH = REPO_ROOT / ".planning" / "phases" / "14-customer-recent-status-scene-runtime" / "14-01-SUMMARY.md"
PHASE_14_VERIFICATION_PATH = REPO_ROOT / ".planning" / "phases" / "14-customer-recent-status-scene-runtime" / "14-VERIFICATION.md"
PHASE_15_CONTEXT_PATH = REPO_ROOT / ".planning" / "phases" / "15-archive-and-todo-scene-expansion-closure" / "15-CONTEXT.md"
PHASE_15_SUMMARY_PATH = REPO_ROOT / ".planning" / "phases" / "15-archive-and-todo-scene-expansion-closure" / "15-02-SUMMARY.md"
PHASE_15_VERIFICATION_PATH = REPO_ROOT / ".planning" / "phases" / "15-archive-and-todo-scene-expansion-closure" / "15-VERIFICATION.md"
STATE_PATH = REPO_ROOT / ".planning" / "STATE.md"


class ValidationAssetTests(unittest.TestCase):
    def test_version_is_consistent_across_assets(self) -> None:
        version = VERSION_PATH.read_text().strip()
        evals = json.loads(EVALS_PATH.read_text())
        readme_text = README_PATH.read_text(encoding="utf-8")

        self.assertEqual(version, "0.2.14")
        self.assertEqual(evals["version"], version)
        self.assertIn("## [0.2.14] - 2026-04-16", CHANGELOG_PATH.read_text())
        self.assertIn("版本：0.2.14", readme_text)

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

    def test_gap_closure_phase_has_required_audit_artifacts(self) -> None:
        self.assertTrue(PHASE_1_SUMMARY.exists())
        self.assertTrue(PHASE_1_VERIFICATION.exists())
        self.assertTrue(PHASE_6_VERIFICATION.exists())

        phase_2_summary = PHASE_2_SUMMARY.read_text(encoding="utf-8")
        self.assertIn("requirements-completed:", phase_2_summary)
        self.assertIn("FOUND-02", phase_2_summary)
        self.assertIn("LIVE-03", phase_2_summary)

    def test_root_guidance_mentions_archived_v1_0_and_v1_1(self) -> None:
        readme_text = README_PATH.read_text(encoding="utf-8")
        status_text = STATUS_PATH.read_text(encoding="utf-8")

        self.assertIn("v1.0 phases 1-11 与 v1.1 phases 12-15 都已完成并归档", readme_text)
        self.assertIn("v1.1 phases 12-15 都已完成并归档", readme_text)
        self.assertIn("v1.0 phases 1-11 与 v1.1 phases 12-15 都已经全部收口并完成归档", status_text)
        self.assertIn("v1.1: Executable Scene Runtimes", ROADMAP_PATH.read_text(encoding="utf-8"))

    def test_runtime_operator_surface_is_documented(self) -> None:
        readme_text = README_PATH.read_text(encoding="utf-8")
        status_text = STATUS_PATH.read_text(encoding="utf-8")
        runtime_readme = (REPO_ROOT / "runtime" / "README.md").read_text(encoding="utf-8")

        self.assertIn("python3 -m runtime scene post-meeting-synthesis", readme_text)
        self.assertIn("python3 -m runtime scene customer-recent-status", readme_text)
        self.assertIn("python3 -m runtime scene archive-refresh", readme_text)
        self.assertIn("python3 -m runtime scene todo-capture-and-update", readme_text)
        self.assertIn("python3 -m runtime meeting-write-loop", readme_text)
        self.assertIn("compatibility wrapper", readme_text)
        self.assertIn("customer recent status", status_text)
        self.assertIn("archive refresh", status_text)
        self.assertIn("Todo follow-on", status_text)
        self.assertIn("python3 -m runtime scene customer-recent-status", runtime_readme)
        self.assertIn("python3 -m runtime scene todo-capture-and-update", runtime_readme)

    def test_scene_runtime_contract_and_boundary_freeze_are_documented(self) -> None:
        contract_text = SCENE_RUNTIME_CONTRACT_PATH.read_text(encoding="utf-8")
        scene_arch_text = SCENE_SKILL_ARCHITECTURE_PATH.read_text(encoding="utf-8")
        runtime_readme = (REPO_ROOT / "runtime" / "README.md").read_text(encoding="utf-8")

        self.assertIn("Standard Result Shape", contract_text)
        self.assertIn("recommendation-first", contract_text)
        self.assertIn("gateway", contract_text)
        self.assertIn("schema preflight", contract_text)
        self.assertIn("write guard", contract_text)
        self.assertIn("writer", contract_text)
        self.assertIn("post-meeting-synthesis", contract_text)
        self.assertIn("customer-recent-status", contract_text)
        self.assertIn("archive-refresh", contract_text)
        self.assertIn("todo-capture-and-update", contract_text)
        self.assertIn("first group: `post-meeting-synthesis`, `customer-recent-status`", contract_text)
        self.assertIn("workflow-first split rule", scene_arch_text)
        self.assertIn("non-bypass shared path", scene_arch_text)
        self.assertIn("python3 -m runtime scene post-meeting-synthesis", runtime_readme)

    def test_planning_state_alignment_tracks_v1_1_post_closeout_state(self) -> None:
        roadmap_text = ROADMAP_PATH.read_text(encoding="utf-8")
        requirements_text = REQUIREMENTS_PATH.read_text(encoding="utf-8")
        state_text = STATE_PATH.read_text(encoding="utf-8")

        self.assertIn("No active mainline milestone", roadmap_text)
        self.assertIn("v1.1-ROADMAP.md", roadmap_text)
        self.assertIn("optional historical cleanup", roadmap_text)
        self.assertIn("No active mainline milestone", requirements_text)
        self.assertIn("v1.1-REQUIREMENTS.md", requirements_text)
        self.assertIn("v1.1 archived", state_text)
        self.assertIn("Optional: /gsd-plan-phase 999.1", state_text)
        self.assertTrue(PHASE_12_CONTEXT_PATH.exists())

    def test_scene_runtime_mainline_phase_artifacts_exist(self) -> None:
        self.assertTrue(PHASE_12_VERIFICATION_PATH.exists())
        self.assertTrue(PHASE_13_CONTEXT_PATH.exists())
        self.assertTrue(PHASE_13_SUMMARY_PATH.exists())
        self.assertTrue(PHASE_13_VERIFICATION_PATH.exists())
        self.assertTrue(PHASE_14_CONTEXT_PATH.exists())
        self.assertTrue(PHASE_14_SUMMARY_PATH.exists())
        self.assertTrue(PHASE_14_VERIFICATION_PATH.exists())
        self.assertTrue(PHASE_15_CONTEXT_PATH.exists())
        self.assertTrue(PHASE_15_SUMMARY_PATH.exists())
        self.assertTrue(PHASE_15_VERIFICATION_PATH.exists())

    def test_milestone_archives_exist(self) -> None:
        self.assertTrue(MILESTONES_PATH.exists())
        self.assertTrue(V1_0_ARCHIVE_ROADMAP_PATH.exists())
        self.assertTrue(V1_0_ARCHIVE_REQUIREMENTS_PATH.exists())
        self.assertTrue(V1_1_ARCHIVE_ROADMAP_PATH.exists())
        self.assertTrue(V1_1_ARCHIVE_REQUIREMENTS_PATH.exists())
        self.assertTrue(V1_1_AUDIT_PATH.exists())

        milestones_text = MILESTONES_PATH.read_text(encoding="utf-8")
        self.assertIn("## v1.1", milestones_text)
        self.assertIn("v1.1-ROADMAP.md", milestones_text)
        self.assertIn("v1.1-REQUIREMENTS.md", milestones_text)
        self.assertIn("v1.1-MILESTONE-AUDIT.md", milestones_text)
        self.assertIn("## v1.0", milestones_text)
        self.assertIn("v1.0-ROADMAP.md", milestones_text)
        self.assertIn("v1.0-REQUIREMENTS.md", milestones_text)

    def test_context_and_account_verification_artifacts_exist(self) -> None:
        self.assertTrue(PHASE_3_VERIFICATION.exists())
        self.assertTrue(PHASE_5_VERIFICATION.exists())

        phase_3_validation = PHASE_3_VALIDATION.read_text(encoding="utf-8")
        self.assertIn("nyquist_compliant: true", phase_3_validation)
        self.assertIn("Manual-Only Verifications", phase_3_validation)

    def test_safe_write_validation_and_verification_are_closed(self) -> None:
        self.assertTrue(PHASE_4_VERIFICATION.exists())

        phase_4_validation = PHASE_4_VALIDATION.read_text(encoding="utf-8")
        self.assertIn("nyquist_compliant: true", phase_4_validation)
        self.assertIn("wave_0_complete: true", phase_4_validation)
        self.assertIn("**Approval:** approved", phase_4_validation)


if __name__ == "__main__":
    unittest.main()
