---
phase: 07
phase_name: "skill-architecture-scene-expansion"
project: "Feishu AM Workbench"
generated: "2026-04-16T00:00:00Z"
counts:
  decisions: 4
  lessons: 4
  patterns: 4
  surprises: 3
missing_artifacts:
  - "07-UAT.md"
---

# Phase 07 Learnings: skill-architecture-scene-expansion

## Decisions

### Workflow Boundaries Over Table Boundaries
Phase 7 locked scene decomposition around AM workflows instead of raw Feishu tables.

**Rationale:** This keeps future packaging aligned with operating tasks such as post-meeting synthesis and recent-status recovery, instead of letting table structure dictate skill boundaries.
**Source:** 07-01-SUMMARY.md

---

### Root Skill Stays Thin
The root skill was kept responsible for routing and top-level interaction consistency only.

**Rationale:** The phase goal was to stop the repository from continuing to grow as one monolithic root skill and move deep workflow reasoning below the entry layer.
**Source:** 07-01-SUMMARY.md

---

### Bootstrap Remains An Admin-Only Path
Bootstrap and controlled remote initialization were explicitly separated from daily scene execution.

**Rationale:** Compatibility checks, config guidance, and remote repair have a different risk profile from daily AM workflows and therefore require stronger confirmation boundaries.
**Source:** 07-02-SUMMARY.md

---

### Cache Never Outranks Live Truth
Schema, manifest/index, and semantic caches were defined as subordinate acceleration layers rather than runtime truth.

**Rationale:** Cache may help routing and early reasoning, but write paths still require live confirmation before mutation to preserve the repo's live-first safety model.
**Source:** 07-02-SUMMARY.md

---

## Lessons

### Architecture Contracts Need Canonical Entry-Doc Integration
It was not enough to lock the architecture in phase artifacts alone; the README, loading strategy, and reference index also needed to expose the new packaging direction.

**Context:** 07-03 was needed specifically so future planners and executors could discover the Phase 7 contract from canonical docs instead of reconstructing it from planning history.
**Source:** 07-03-SUMMARY.md

---

### Current-Vs-Target Framing Prevents False Claims
Repo entry docs need to distinguish architectural direction from already-shipped runtime structure.

**Context:** The phase explicitly documented that scene-skill folders are the target shape, not a claim that runnable scene packaging already exists.
**Source:** 07-03-SUMMARY.md

---

### Verification Can Close An Architecture Phase Without Runtime Additions
An architecture-contract phase can be considered complete even when it does not ship scene-skill folders, bootstrap commands, or cache refresh commands.

**Context:** Verification concluded that Phase 7's obligation was to make boundaries clear, discoverable, and reusable by later phases, not to implement every future execution surface immediately.
**Source:** 07-VERIFICATION.md

---

### Dirty Target Files Change Execution Tactics
When target documentation files already contain unrelated uncommitted changes, the safer execution tactic is to avoid automatic git commits.

**Context:** All three plan summaries recorded that the run skipped task commits because target files already had pre-existing workspace edits that would have been mixed into the same commit.
**Source:** 07-01-SUMMARY.md

---

## Patterns

### Thin Root Skill
Keep the root skill limited to routing, live-context decisions, and top-level interaction rules.

**When to use:** Use this pattern when a skill repository is starting to absorb too many workflow-specific rules and needs a stable entry layer without becoming a monolith.
**Source:** 07-01-SUMMARY.md

---

### Scene-Owned Reasoning
Place detailed workflow rules and expert-agent composition below the root skill boundary.

**When to use:** Use this pattern when workflows have distinct operating logic and need deeper guidance without polluting the global entry surface.
**Source:** 07-01-SUMMARY.md

---

### Bootstrap Isolation
Keep setup, compatibility checks, and controlled remote initialization outside daily scene execution.

**When to use:** Use this pattern when administrative setup flows need stronger confirmations and different guardrails than normal user-facing workbench operations.
**Source:** 07-02-SUMMARY.md

---

### Load-By-Surface Guidance
Apply one progressive-disclosure model across root skill, scene skills, and admin/bootstrap, but load each surface at a different moment.

**When to use:** Use this pattern when a docs-first repository needs future executors to discover the right guidance without loading every instruction source up front.
**Source:** 07-03-SUMMARY.md

---

## Surprises

### Existing Workspace Changes Blocked Atomic Commits
The target documentation files already contained uncommitted workspace changes during execution.

**Impact:** Phase 7 had to avoid automatic git commits across all three plans, which preserved isolation but removed the expected task-commit trail for this run.
**Source:** 07-01-SUMMARY.md

---

### No Goal-Level Gaps Were Found Despite The Work Being Doc-Only
Verification found no Phase 7 goal gaps even though the phase produced architecture and documentation contracts rather than runnable scene implementations.

**Impact:** This confirmed that the success condition for the phase was contract clarity and discoverability, not immediate runtime expansion.
**Source:** 07-VERIFICATION.md

---

### Phase 7 Closed Without Building Scene Folders Or Bootstrap Commands
The final project state records that Phase 7 closed as an architecture-contract phase and did not create runnable scene-skill folders or bootstrap commands yet.

**Impact:** Later phases can proceed from stable contracts, but implementation work still remains deliberately deferred instead of being implicitly bundled into architecture closure.
**Source:** .planning/STATE.md