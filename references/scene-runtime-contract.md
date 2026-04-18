# Scene Runtime Contract

This document freezes the shared runtime contract for executable scenes.

The goal is to let later scenes feel like one family of workflows while keeping the runtime live-first, recommendation-first, and host-agnostic.

## Shared Input Envelope

Every executable scene should receive one shared request shape with:

- a stable `scene_name`
- a `customer_query` or equivalent scene target
- repo/runtime location needed to load local live config
- scene-specific inputs kept inside a scene payload instead of changing the root entry contract each time
- optional execution flags such as confirmed write

The input contract should stay small. Scene-specific details belong inside the scene payload.

## Standard Result Shape

Every executable scene should return one standard structured result with these fields visible:

- `scene_name`
- `resource_status`
- `customer_status`
- `context_status`
- `used_sources`
- `facts`
- `judgments`
- `open_questions`
- `recommendations`
- `fallback_category`
- `fallback_reason`
- `fallback_message`
- `write_ceiling`
- scene-specific payload fields layered on top of the shared contract

This is the standard level of detail locked in Phase 12.

That means the result should be rich enough to explain:

- what scene ran
- whether the customer was truly resolved
- whether live context was sufficient
- what evidence was used
- which statements are grounded facts versus higher-level judgment
- what still needs confirmation
- what next steps are being recommended
- whether execution is still at recommendation-only level

## Fallback Visibility

Fallback should be visible in two layers:

1. business-readable meaning
2. one deeper reason category

The business-readable layer answers the human question: why can this not fully proceed right now?

The deeper category answers the audit question: which class of limit caused it?

Allowed shared fallback categories:

- `customer`
- `context`
- `permission`
- `validation`
- `safety`
- `none`

Scenes may add scene-specific detail, but they should not replace these shared categories with host-specific wording.

## Write Ceiling

The result must make write ceiling explicit.

Current shared meanings are:

- `normal`
- `recommendation-only`

Scenes must not silently imply write safety from a successful-looking output.
If context is partial, fallback evidence is weak, or safety boundaries block progress, the result must say so explicitly.

## Non-Bypass Safety Rule

Scene runtimes are not allowed to create a second execution path.

The following boundaries remain the only shared safety path:

- gateway
- schema preflight
- write guard
- writer

If a scene proposes writes, it must flow through those boundaries rather than implementing its own shortcut.

## Entry Surface Rule

Stable scene names are the canonical runtime entry surface.

Compatibility commands may remain temporarily, but they should wrap scene dispatch rather than define the long-term contract.

## First-Wave Boundary Freeze

Phase 12 locks a medium-strength boundary freeze.

### Locked first-wave scene list

- `post-meeting-synthesis`
- `customer-recent-status`
- `archive-refresh`
- `todo-capture-and-update`
- `cohort-scan` (NEW in v1.2)
- `meeting-prep` (NEW in v1.2)
- `proposal` (NEW in v1.2)

### Locked priority grouping

- first group: `post-meeting-synthesis`, `customer-recent-status`
- second group: `archive-refresh`, `todo-capture-and-update`
- third group (v1.2): `cohort-scan`, `meeting-prep`, `proposal`

### Locked boundary rules

- scene boundaries are defined by workflow intent, not raw tables
- deferred scenes must not silently move into the first wave
- admin/bootstrap behavior stays out of daily scene execution
- host-specific formatting must not become part of the core runtime contract

## Host-Agnostic Rule

The shared scene contract must stay portable across agent hosts.

That means:

- the structured result should not depend on one CLI or chat renderer
- host-specific formatting belongs in the final rendering layer, not in the contract itself
- business meaning should survive across Hermes/OpenClaw/Codex-style hosts

## v1.2 Scene Additions

Phase 16-20 added expert-analysis foundation and three new scenes:
- cohort-scan: user-triggered analytical entry for customer cohorts
- meeting-prep: recommendation-first meeting brief with seven-dimension output
- proposal: structured proposal/report/resource-coordination draft with five-dimension output

All three scenes follow the same SceneResult contract and dispatch pattern.

## VAL-05 Regression Scope Note

VAL-05 regression coverage (Phase 21) covers 6 scenes: post-meeting-synthesis, customer-recent-status, archive-refresh, cohort-scan, meeting-prep, and proposal.

The scene `todo-capture-and-update` is excluded from VAL-05 regression because it was shipped in v1.1 and is not part of the v1.2 scope. The total registry contains 7 scenes, but VAL-05 specifically targets the 6 scenes upgraded or new in v1.2 (Phases 16-20).

## Current Canonical Example

`post-meeting-synthesis` is the first runtime seam using this contract.

In Phase 12 it serves as the compatibility bridge from the existing `meeting-write-loop` operator path.
In Phase 13 it becomes the first canonical scene runtime built directly on top of this contract.
