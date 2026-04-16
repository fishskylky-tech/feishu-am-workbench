---
title: Cache Governance
load_triggers:
  - condition: designing cache, manifest, or ontology layers
  - skill_stage: [architecture-planning, bootstrap, cache-refresh]
load_priority: medium
estimated_tokens: 980
dependencies: [feishu-runtime-sources, live-schema-preflight, base-integration-model]
tier: L3-on-demand
---

# Cache Governance

Use this file when future work needs cache acceleration without confusing cache with live truth.

Phase 7 locks three cache classes and one trust rule: cache may accelerate routing and early reasoning, but live truth remains authoritative when safety or mutation is involved.

Each cache class must also declare a refresh lifecycle that is explicit, auditable, and subordinate to live truth.

## Trust Hierarchy

Use this order when cache participates in a run:

1. live confirmation
2. workspace config and semantic-slot mapping
3. compatible cache artifact
4. recommendation-only fallback when uncertainty remains

Cache can help route the work.
Cache cannot silently replace live confirmation for critical reads or writes.

## Cache Class 1: workspace schema cache

Purpose:

- reduce repeated schema discovery
- retain field type and option snapshots
- accelerate preflight reasoning before live checks

Authoritative source:

- live Base schema

Allowed uses:

- preflight preparation
- compatibility comparison
- drift explanation

Refresh lifecycle:

- initialize during bootstrap when requested
- refresh explicitly on drift, setup, or scheduled maintenance
- do not assume implicit always-rebuild behavior

Drift handling:

- compare cached fields/options to live values
- record rename, type, and option drift explicitly
- prefer live values immediately when conflict exists

Write rule:

- every write still requires live confirmation before mutation

## Cache Class 2: workspace manifest/index cache

Purpose:

- accelerate archive lookup
- accelerate meeting-note lookup
- retain folder, tasklist, and repeated resource routing hints

Authoritative source:

- live probe results and confirmed workspace resources

Allowed uses:

- route likely customer archive docs
- shortlist meeting-note candidates
- reuse known folder and tasklist mappings

Refresh lifecycle:

- initialize during bootstrap or first explicit indexing run
- refresh when routing drift is detected
- refresh after controlled bootstrap changes that affect resource topology

Drift handling:

- treat stale links as routing hints only
- when index conflicts with live probe, trust the live probe
- surface stale or duplicate candidates instead of hiding them

Critical read rule:

- important archive or resource decisions should re-check live state when the cached route is uncertain or safety-sensitive

## Cache Class 3: semantic/ontology cache

Purpose:

- preserve entity, relation, event, and operating-state interpretations
- support consistent write-target mapping across scenes
- reduce repeated reasoning over stable business semantics

Authoritative source:

- scene reasoning grounded in live or confirmed evidence

Allowed uses:

- early reasoning
- cross-scene vocabulary normalization
- evidence-linked interpretation support

Refresh lifecycle:

- versioned refresh as an explicit artifact lifecycle
- refresh on ontology changes, not on every run
- preserve provenance for changed mappings or concepts

Drift handling:

- if semantic cache and live evidence disagree, prefer live evidence
- do not let cached semantics become a default runtime truth source
- downgrade to recommendation mode when ontology confidence is weak

Critical decision rule:

- semantic/ontology cache may guide reasoning, but it cannot approve a write by itself

## Mandatory Live Confirmation Cases

Live confirmation is mandatory for:

- every write path before mutation
- protected or guarded field updates
- strict enum option resolution
- owner resolution for Todo writes
- critical reads where stale routing could misidentify the target customer or document

## Operational Rules

- cache refresh should be explicit and auditable
- cache artifacts should record when they were produced and from which live scope
- cache failures should degrade to slower live paths or recommendation-only mode, not guessed writes
- cache design should stay portable across agent hosts and should not encode host-specific business truth
