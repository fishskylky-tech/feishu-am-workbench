---
title: Scene Skill Architecture
load_triggers:
  - condition: defining scene skill boundaries or expert-agent collaboration
  - skill_stage: [architecture-planning, packaging, scene-design]
load_priority: medium
estimated_tokens: 980
dependencies: [workbench-information-architecture, minimal-stable-core]
tier: L3-on-demand
---

# Scene Skill Architecture

Use this file when the repository needs to decide how future scene skills should be carved, loaded, and connected to expert agents.

The goal is to keep the root skill thin while making scene capabilities self-contained and workflow-shaped.

## Four-Layer Contract

Phase 7 locks one architecture contract for daily operating paths:

1. main skill
2. scene skills
3. expert agents
4. runtime foundation

The main skill keeps one top-level interaction pattern.
The scene skills own workflow logic.
The expert agents provide structured intermediate artifacts on demand.
The runtime foundation remains the shared live-access and safety layer.

## Main Skill Boundary

The main skill must stay a thin entry and orchestration layer.

It is responsible for:

- scene detection
- deciding whether live context is needed
- choosing which scene skill to invoke
- keeping the recommendation -> confirmation -> write flow consistent
- preserving one user-facing interaction style across scenes

It is not responsible for:

- deep business reasoning for each workflow
- raw Feishu table-by-table handling
- acting as a universal dispatcher for all expert agents

If a rule only matters inside one workflow, it should move to that scene skill instead of growing the root skill.

## Scene Skills Boundary

Scene skills must be defined by AM workflows rather than by raw Feishu tables.

This means a scene skill may span customer master, detail tables, archive docs, and Todo together when that matches the user's operating goal.

Do not create scene skills named after one table such as "customer-master-skill" or "action-plan-skill".

## First-Wave Scene Skills

The first locked wave is:

1. `post-meeting-synthesis`
2. `customer-recent-status`
3. `archive-refresh`
4. `todo-capture-and-update`

Priority grouping is also locked:

- first group: `post-meeting-synthesis`, `customer-recent-status`
- second group: `archive-refresh`, `todo-capture-and-update`

The first group should be planned and packaged before the second group.

## Deferred Scene Candidates

These scene candidates remain valid but are intentionally not part of the first locked wave:

- `meeting-prep`
- `weekly-or-monthly-account-review`
- `public-update-synthesis`
- `phase-goal-review`

They should not be silently pulled into the first scene-skill wave.

## Expert Agents Collaboration Model

Expert agents are scene-internal collaborators, not a fixed global pipeline.

The scene skill decides whether an expert call is needed.
The main skill does not invoke expert agents as a universal step.

Required collaboration rules:

- invoke expert agents on demand
- keep final user-facing synthesis inside the scene skill
- return structured intermediate artifacts instead of free-form final answers

Typical expert outputs include:

- hydrated context
- risk or opportunity lists
- write safety reports
- action candidates

This keeps expert agents composable while leaving scenario judgment inside the scene skill.

## Runtime Foundation Boundary

The runtime foundation remains shared across all scene skills.

It continues to own:

- resource probing
- customer resolution
- targeted read primitives
- schema preflight
- write guard
- diagnostics
- normalized writer surfaces

It must not silently assemble a full business-context bundle for every scene.
Scene skills stay responsible for deciding what to hydrate and what to ask expert agents to produce.

## Packaging Guidance

The exact folder structure remains implementation-discretionary, but the packaging contract is fixed:

- each future scene skill should be a self-contained workflow package
- each scene package should keep its own loading guidance and scenario references
- the root skill should point to scene skills rather than absorbing their detailed rules
- expert-agent descriptors should stay subordinate to the scene package that calls them

## Safety Reminder

This architecture changes packaging, not truth hierarchy.

- live truth still outranks cached or inferred context
- recommendation-first still applies before writes
- every write path still depends on live preflight and guard behavior

## Boundary Freeze Rules

Phase 12 turns these first-wave decisions into a medium-strength runtime boundary freeze.

That means later work must preserve all of the following unless a future phase explicitly reopens them:

- the first-wave scene list
- the first-group / second-group priority split
- the workflow-first split rule instead of table-first scene carving
- deferred scenes staying out of the first wave
- gateway, schema preflight, write guard, and writer as the non-bypass shared path

This is intentionally stronger than a loose architecture preference, but weaker than hard-coding every later implementation detail.
