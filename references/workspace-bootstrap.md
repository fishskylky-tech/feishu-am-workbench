---
title: Workspace Bootstrap
load_triggers:
  - condition: bootstrap, install, compatibility, or environment diagnosis is needed
  - skill_stage: [bootstrap, setup, compatibility-check]
load_priority: medium
estimated_tokens: 860
dependencies: [feishu-runtime-sources, live-schema-preflight]
tier: L3-on-demand
---

# Workspace Bootstrap

Use this file when the repository needs an admin/bootstrap path for setup, compatibility reporting, or controlled repair.

The bootstrap path is separate from daily scene execution.

## Separation Rule

Bootstrap, install, compatibility, and environment diagnosis belong to an admin/bootstrap path.

They do not belong to the normal main-skill path for daily customer work.

This keeps low-frequency, high-impact setup logic from diluting normal operating scenes.

## Minimum Bootstrap Deliverables

Any future bootstrap implementation should be able to produce at least:

- workspace compatibility reporting
- local config generation or update guidance
- cache initialization or refresh output
- drift and risk reporting
- explicit `lark-cli` version dependency checks

These are the minimum deliverables for admin/bootstrap, even if the implementation surface changes later.

## Local-First Admin Behavior

The default bootstrap posture should be local-first:

- inspect the current workspace contract
- diagnose missing runtime inputs
- explain what is missing or degraded
- propose or generate safe local configuration artifacts
- refresh compatible cache artifacts when requested

Bootstrap should connect back to workspace config and runtime truth hierarchy, not to checked-in private identifiers.

## Controlled Remote Initialization

The bootstrap path may support controlled remote creation or initialization of Feishu resources, but only under these conditions:

- it remains admin-only
- it is never part of the daily scene path
- it requires strong confirmation before remote mutation
- it reports what will be created, updated, or repaired before doing so

Automatic local repair is acceptable when it only affects local configuration or cache artifacts.

Remote repair or initialization must never become an implicit side effect of normal scene execution.

## Relationship To Workspace Config

Bootstrap owns the setup-facing workflow around workspace config, not the business logic itself.

That includes:

- validating config completeness against the required minimum
- surfacing missing semantic slots or guarded policies
- generating update guidance from template/example files
- reporting mismatches between config expectations and live workspace structure

The actual environment boundary still remains workspace config plus live runtime inputs.

## Compatibility Checks

A workspace compatibility report should cover at least:

- required Base app and table reachability
- customer archive and meeting-note folder reachability
- Todo tasklist and custom-field reachability
- live schema compatibility for minimum semantic slots
- `lark-cli` availability and supported command surface
- blocked, degraded, and safe findings with next actions

## Risk Model

Bootstrap should surface risk explicitly instead of hiding it behind setup optimism.

Recommended report classes:

- compatible
- degraded
- blocked
- repairable-locally
- requires-strong-confirmation

## Safety Reminder

Bootstrap exists to make setup safer and more repeatable.

It must not weaken:

- recommendation-first daily operation
- guarded write behavior
- live confirmation before write-time mutation
- separation between public docs and private runtime truth
