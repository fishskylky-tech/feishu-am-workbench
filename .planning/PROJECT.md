# Feishu AM Workbench

## What This Is

Feishu AM Workbench is a personal AM skill project for Hermes/OpenClaw/Codex-style agents. It helps a Sensors Data AM use Feishu Base, Drive docs, and Task as a customer operating platform: recover live context, interpret customer materials, propose safe updates, and gradually evolve toward a reusable account-management operating model.

This is a brownfield project: the repository already has a working runtime, validation assets, a private GitHub collaboration surface, and a live Feishu workspace with customer master, contracts, actions, key people, competitors, archives, meeting notes, and a task module.

## Core Value

Use one live-first, safety-first skill to turn AM inputs into actionable customer operating context and guarded write plans inside the existing Feishu workbench.

## Requirements

### Validated

- ✓ Local runtime can resolve Feishu resource hints and render capability diagnostics — v1.0
- ✓ Meeting flow can execute live-first gateway with customer resolution and minimum context recovery — v1.0
- ✓ Todo write surface returns normalized preflight/guard/dedupe/write results — v1.0
- ✓ 客户主数据 / 客户联系记录 / 行动计划 already have a minimal semantic contract in runtime — v1.0
- ✓ Repository already contains real-case eval assets and regression tests for the current meeting/Todo path — v1.0
- ✓ Root guidance, milestone audit evidence, and runtime operator surface are aligned with shipped state — v1.0

### Active

- [ ] Introduce scene-skill runtime surfaces beyond the single root skill entrypoint
- [ ] Land bootstrap/admin flows as executable operator paths rather than architecture-only contracts
- [ ] Reduce live-only verification dependence for fallback quality and safe-write edge cases
- [ ] Build proactive AM outputs such as risk reminders and weekly operating summaries
- [ ] Deepen archive and historical meeting-note understanding beyond link-level recovery

### Out of Scope

- Full SaaS CRM productization — current priority is personal AM value, not a multi-tenant app
- Automatic writes without confirmation — violates the project safety model
- Full-field mirroring of every Feishu table — too fragile and too expensive to maintain
- Generic platform abstraction that ignores the current Feishu workbench operating model — would dilute near-term value

## Context

- Shipped milestone: v1.0 archived on 2026-04-16 with roadmap, requirements, audit, and phase artifacts preserved under `.planning/milestones/`.
- Local repo now documents architecture, status, validation protocol, security model, roadmap intent, and a runtime meeting write-loop operator surface.
- GitHub remote is active and private, with open issues, PRs, discussions, and one active Projects v2 board for 2026 roadmap execution.
- Live Feishu Base currently contains 8 business tables, including customer master, contracts, actions, key people, competitors, contact logs, and a potential-customer pool.
- Live customer archive folder already mixes canonical customer archives, a meeting-note folder, a weekly-info folder, and a template doc; this reflects real workflow value but also data quality risks.
- Live task module currently centers on a single 神策 tasklist, which is already part of the runtime write path.
- Existing docs now reflect a completed v1.0 brownfield milestone and are ready for the next milestone definition cycle.

## Constraints

- **Tech stack**: Python runtime + lark-cli + markdown skill docs — this is already the established execution surface
- **Security**: secrets and live resource identifiers stay in env/private runtime sources — required to avoid leaking personal customer workspace data
- **Safety**: writes must remain recommendation-first and guarded — high-risk master-data updates cannot become automatic
- **Brownfield**: roadmap must respect existing runtime, docs, tests, and live workspace structures — this is not a greenfield rewrite
- **Portability**: business logic should stay portable across agent hosts — the project is intended for Hermes/OpenClaw-style usage, not one locked host

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Treat the repo as a brownfield GSD project | Existing code, tests, docs, and live resources already prove non-trivial scope | — Pending |
| Keep the runtime thin and scene-driven | Foundation should resolve/protect, not over-assemble business context | ✓ Good |
| Model Base through minimal semantic contracts, not full mirrors | Reduces drift and maintenance cost | ✓ Good |
| Keep personal-value-first before generalization | Matches current user goal and existing roadmap language | ✓ Good |
| Use live Feishu structure as a planning input, not just local docs | Prevents roadmap drift from real workspace operations | ✓ Good |

## Current State

- v1.0 shipped with phases 1-11 complete and archived.
- The repository now supports capability diagnostics, customer-grounded context recovery, guarded Todo writes, milestone-grade validation evidence, and a runtime meeting write-loop operator command.

## Next Milestone Goals

- Turn scene-skill architecture contracts into executable scene runtimes.
- Add bootstrap/admin execution paths for new-workspace compatibility and setup.
- Continue converting live-only validation boundaries into more repeatable automation.

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-16 after v1.0 milestone archival*