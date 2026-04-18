# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`feishu-am-workbench` is a personal AM (Account Management) workflow skill for Feishu (Lark) Base, Docs, and Todo. It transforms mixed inputs (meeting transcripts, customer materials, natural language) into structured account views and proposes cross-workbench updates — but only writes after explicit user confirmation.

The runtime layer enables live Feishu access, schema preflight, and write guard. Without `lark-cli` or valid credentials, the skill operates in recommendation-only mode.

## Build/Test Commands

```bash
# Activate environment (required before any Python commands)
source .venv/bin/activate

# Capability diagnostics
python3 -m runtime .
python3 -m runtime diagnose . --json

# Run a specific scene
python3 -m runtime scene post-meeting-synthesis --customer-query <CUSTOMER_A> --json

# Core test slice (run before any PR)
python3 -m unittest tests.test_env_loader tests.test_runtime_smoke tests.test_meeting_output_bridge tests.test_validation_assets -q

# All tests
python -m unittest discover -s tests -q

# Single test file
python3 -m unittest tests.test_meeting_output_bridge -q
```

## Architecture

```
runtime/               # Local execution layer (Python 3.10+)
  gateway.py           # Unified Feishu gateway: resource resolution, customer resolution, schema preflight, write guard
  live_adapter.py      # lark-cli command surface adapter
  schema_preflight.py  # Live schema validation before writes
  write_guard.py       # Protected fields, idempotency, no-write fallback
  todo_writer.py       # Unified Todo write-back (create, update, subtask, dedupe)
  scene_runtime.py     # Scene execution assembly
  scene_registry.py     # Stable scene name → handler mapping
  models.py            # SceneRequest, SceneResult, WriteCandidate, WriteExecutionResult
  semantic_registry.py # SEMANTIC_FIELD_REGISTRY, TableProfile

evals/                 # Scene bridging and validation artifacts
  meeting_output_bridge.py  # Meeting scene integration surface
  runner.py

references/             # Business rules, Feishu semantic constraints, scene docs
tests/                  # unittest-based regression suite
```

### 6-Layer Design

1. **Input Layer** — Receives transcripts, customer materials, natural language
2. **Scene Orchestration** — Routes to `meeting-prep`, `post-meeting`, `account-analysis`, `archive-refresh`
3. **Extraction & Judgment** — Entity extraction, fact vs judgment, routing, account judgment
4. **Feishu Workbench Foundation** — `ResourceResolver`, `ContextHydrator`, `LiveSchemaPreflight`, `WriteGuard`
5. **Output Layer** — Structured analysis with audit fields
6. **Write-back Layer** — Only executes after explicit user confirmation

### Core Execution Path (Meeting Scene)

1. `runtime/__main__.py` → `scene_registry.py` → `scene_runtime.py`
2. `gateway.py` loads runtime sources, probes live resources, resolves customer
3. `evals/meeting_output_bridge.py` recovers live context per customer
4. Scene logic generates facts, judgment, open questions, `WriteCandidate`
5. User confirms → `TodoWriter` runs `SchemaPreflightRunner` + `WriteGuard` + dedupe → `lark-cli` write

## Key Conventions

- **Live-first**: Meeting scenarios attempt live runtime before single-file analysis
- **Recommendation-first**: Default to giving suggestions, not writing directly
- **Absolute dates only**: Never `近期`, `昨天`, `明年`; use absolute dates like `2026-04-20`
- **One customer ID per customer**: Use `客户主数据` as source of truth; deduplicate at customer level before writing
- **Protected fields**: Master data fields marked protected must never be auto-updated
- **No raw transcripts as cold memory**: Meeting-note docs must be structured, not raw transcripts
- **Write order**: Base tables → supporting docs → Todo last
- **Idempotency**: Dedupe by meaning, not exact title match; prefer update/subtask over duplicate create

## Configuration

Environment variables (from `.env`, NOT committed to repo):
- `FEISHU_AM_BASE_TOKEN`
- `FEISHU_AM_CUSTOMER_MASTER_TABLE_ID`
- `FEISHU_AM_CUSTOMER_ARCHIVE_FOLDER`
- `FEISHU_AM_MEETING_NOTES_FOLDER`
- `FEISHU_AM_TODO_TASKLIST_GUID`
- `FEISHU_AM_TODO_CUSTOMER_FIELD_GUID`
- `FEISHU_AM_TODO_PRIORITY_FIELD_GUID`

## Branch Strategy

- `main` — stable, always deployable
- `codex/*` — development branches (e.g., `codex/m1-validation-*`)

## Important File Locations

- `SKILL.md` — Skill entry point with L1/L2/L3 progressive loading tiers
- `references/feishu-workbench-gateway.md` — Always load first when accessing Feishu
- `references/actual-field-mapping.md` — Cached Feishu schema (generate via `lark-cli` commands listed in SKILL.md)
- `references/meeting-context-recovery.md` — Context recovery process for meeting scenes
