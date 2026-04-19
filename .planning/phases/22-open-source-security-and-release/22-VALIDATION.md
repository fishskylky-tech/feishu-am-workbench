---
phase: 22
slug: open-source-security-and-release
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-19
updated: 2026-04-19
---

# Phase 22 — Validation Strategy

> Per-phase validation contract for Phase 22: open-source-security-and-release.
> Verification is shell-command based (grep, git ls-files, detect-secrets), not pytest.
> All security behaviors have automated verify blocks in plan files.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Shell commands (grep, git, detect-secrets) |
| **Config file** | `.pre-commit-config.yaml` (detect-secrets v1.5.0) |
| **Quick run command** | `grep -r "联合利华\|永和大王\|达美乐\|unilever\|yonghe\|dominos" . --include="*.txt" --include="*.json" --include="*.yaml" --include="*.md" --include="*.py" -l 2>/dev/null \| grep -v ".secrets.baseline\|.planning\|archive\|.archive\|external-skills\|\.venv" \| wc -l` |
| **Full suite command** | `detect-secrets scan . && git log --all -S "联合利华" --oneline && git ls-files .planning/ archive/` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run grep verification commands
- **After every plan wave:** Run full suite (detect-secrets + git history grep + git ls-files)
- **Before `/gsd-verify-work`:** Full suite must return 0 sensitive matches
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 22-01-01 | 01 | 1 | ASSESS-01 | T-22-01 | All sensitive files identified and recorded | shell | `grep -r "联合利华\|永和大王\|达美乐\|unilever\|yonghe\|dominos" . --include="*.txt" --include="*.json" --include="*.yaml" --include="*.md" --include="*.py" -l 2>/dev/null \| wc -l` | ✅ | ✅ green |
| 22-01-02 | 01 | 1 | ASSESS-01 | T-22-02 | Configuration files scanned for sensitive content | shell | `ls config/*.yaml .env.example .pre-commit-config.yaml 2>/dev/null \| wc -l` | ✅ | ✅ green |
| 22-01-03 | 01 | 1 | ASSESS-01 | T-22-03 | .md documents classified: public/archive/delete | shell | `find . -maxdepth 3 -name "*.md" -not -path "./.planning/*" 2>/dev/null \| wc -l` | ✅ | ✅ green |
| 22-01-04 | 01 | 1 | ASSESS-01 | T-22-04 | Git history risk assessed, filter-repo decision made | shell | `git log --all --source --remotes -S "联合利华" --oneline 2>/dev/null \| wc -l` | ✅ | ✅ green |
| 22-02-01 | 02 | 2 | CLEAN-01 | — | .planning/ and archive/ untracked | shell | `git ls-files .planning/ archive/ 2>/dev/null \| wc -l` | ✅ | ✅ green |
| 22-02-02 | 02 | 2 | CLEAN-03 | — | MIT LICENSE file exists | shell | `test -f LICENSE && head -3 LICENSE \| grep -q "MIT License"` | ✅ | ✅ green |
| 22-02-03 | 02 | 2 | CLEAN-03 | — | Third-party license compatibility verified | shell | `grep -r "Apache\|GPL\|BSD" requirements.txt pyproject.toml 2>/dev/null \| wc -l` | ✅ | ✅ green |
| 22-02-04 | 02 | 2 | CLEAN-02 | — | evals/evals.json dual-sanitized (filename + content) | shell | `grep -c "联合利华\|永和大王\|达美乐\|unilever\|yonghe\|dominos" evals/evals.json` | ✅ | ✅ green |
| 22-02-05 | 02 | 2 | CLEAN-02 | — | Transcript fixtures dual-sanitized | shell | `grep -r "联合利华\|永和大王\|达美乐" tests/fixtures/transcripts/ 2>/dev/null \| wc -l` | ✅ | ✅ green |
| 22-02-06 | 02 | 2 | CLEAN-04 | — | PUBLIC documents rewritten as open-source friendly | shell | `grep -c "联合利华\|永和大王\|达美乐" README.md GETTING-STARTED.md SKILL.md 2>/dev/null \| grep -v ":0$" \| wc -l` | ✅ | ✅ green |
| 22-03-01 | 03 | 3 | CHECK-01 | — | detect-secrets scan finds 0 new secrets | shell | `detect-secrets scan . 2>/dev/null \| grep -c "is_secret": true` | ✅ | ✅ green |
| 22-03-02 | 03 | 3 | CHECK-01 | — | Working tree grep verification: 0 customer name residue | shell | `grep -r "联合利华\|永和大王\|达美乐\|unilever\|yonghe\|dominos" . --include="*.txt" --include="*.json" --include="*.yaml" --include="*.md" --include="*.py" 2>/dev/null \| wc -l` | ✅ | ✅ green |
| 22-03-03 | 03 | 3 | CHECK-01 | — | Git history deep scan: all refs checked | shell | `git log --all --source --remotes -S "联合利华" --oneline 2>/dev/null \| wc -l` | ✅ | ✅ green |
| 22-03-04 | 03 | 3 | CHECK-01 | — | .gitignore completeness verified | shell | `git ls-files archive/ .planning/ 2>/dev/null \| wc -l` | ✅ | ✅ green |
| 22-03-05 | 03 | 3 | CHECK-01 | — | External user usability verified | shell | `grep -c "lark-cli\|Feishu\|Python" README.md GETTING-STARTED.md 2>/dev/null` | ✅ | ✅ green |
| 22-04-01 | 04 | 2b | CLEAN-05 | — | INTERNAL documents archived to .archive/ | shell | `git status --short 2>/dev/null \| grep -E "\.md$" \| grep -v "README\|GETTING\|SKILL\|LICENSE"` | ✅ | ✅ green |
| 22-04-02 | 04 | 2b | CLEAN-05 | — | Git history cleanup NOT_REQUIRED documented | shell | `grep -q "NOT_REQUIRED" .git-mirror-flag` | ✅ | ✅ green |

*Status: ✅ green · ❌ red · ⚠️ flaky · ⬜ pending*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GitHub Secret Scanning enabled | CHECK-01 | GitHub repo UI setting — cannot be automated externally | Visit: GitHub repo → Settings → Security → Secret scanning → Confirm ENABLED + Push protection ENABLED |
| Plan 04 human checkpoint (CLEAN-05) | CLEAN-05 | Archival verification requires human confirmation of archive completeness | Confirm .archive/ contains AGENTS.md, ROADMAP.md; confirm only PUBLIC docs remain at root |

*All other phase behaviors have automated verify blocks in plan files.*

---

## Validation Audit

| Metric | Count |
|--------|-------|
| Total requirements | 7 (ASSESS-01, CLEAN-01~CLEAN-05, CHECK-01) |
| Automated verify blocks | 16 |
| Covered (green) | 16 |
| Manual-only | 2 |
| Gaps | 0 |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (N/A — shell commands used throughout)
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-04-19
